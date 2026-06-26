from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date, timedelta
from .models import CheckIn, TempLeave
from apps.reservations.models import Reservation
from apps.credits.models import CreditRecord
from apps.violations.models import Violation


@login_required
def checkin_qr_view(request):
    """签到页面（入口扫码）"""
    today = date.today()
    now = timezone.now().time()

    # Find user's pending reservation today
    pending_res = request.user.reservations.filter(
        date=today, status="confirmed"
    ).select_related("seat__room").first()

    return render(request, "checkin/checkin.html", {"reservation": pending_res, "now": now})


@login_required
def checkin_do(request, reservation_id):
    """执行签到"""
    res = get_object_or_404(Reservation, pk=reservation_id, user=request.user)

    if res.status != "confirmed":
        messages.error(request, "该预约状态异常。")
        return redirect("checkin_qr")

    if res.date != date.today():
        messages.error(request, "只能签到当天的预约。")
        return redirect("checkin_qr")

    now = timezone.now()
    res_start = timezone.make_aware(
        datetime.combine(res.date, res.start_time),
        timezone.get_current_timezone()
    )
    minutes_late = int((now - res_start).total_seconds() / 60)

    # Check if too late
    if minutes_late > 30:
        # Mark as no-show
        res.status = "no_show"
        res.save()
        # Deduct 5 points
        request.user.credit_score = max(0, request.user.credit_score - 5)
        request.user.save()
        CreditRecord.objects.create(
            user=request.user, change=-5, balance=request.user.credit_score,
            type="no_show", reference_id=res.id, description=f"爽约-预约#{res.id}"
        )
        Violation.objects.create(
            user=request.user, reservation=res, type="no_show", points_deducted=-5,
            description=f"预约 {res.date} {res.start_time}-{res.end_time} 未在规定时间内签到",
            status="confirmed"
        )
        messages.error(request, "已超过签到窗口，标记为爽约，扣5信用分。")
        return redirect("checkin_qr")

    # Determine on-time / late
    is_ontime = minutes_late <= 0
    violation_type = None
    points = 0

    if 0 < minutes_late <= 15:
        is_ontime = False
        violation_type = "late"
        points = -1
    elif 15 < minutes_late <= 30:
        is_ontime = False
        violation_type = "severe_late"
        points = -3

    # Create CheckIn
    checkin = CheckIn.objects.create(
        reservation=res, check_in_time=now,
        is_ontime=is_ontime if not is_ontime else is_ontime
    )
    res.status = "checked_in"
    res.save()

    if violation_type:
        request.user.credit_score = max(0, request.user.credit_score + points)
        request.user.save()
        CreditRecord.objects.create(
            user=request.user, change=points, balance=request.user.credit_score,
            type=violation_type, reference_id=res.id, description=f"{'迟到' if violation_type=='late' else '严重迟到'}-预约#{res.id}"
        )
        msg = f"签到成功（迟到{minutes_late}分钟），扣{abs(points)}信用分。"
    else:
        msg = "签到成功！祝自习愉快~"

    messages.success(request, msg)
    return redirect("checkin_qr")


@login_required
def checkout(request, reservation_id):
    """签退"""
    res = get_object_or_404(Reservation, pk=reservation_id, user=request.user, status="checked_in")
    checkin = getattr(res, "checkin", None)
    if not checkin:
        messages.error(request, "未找到签到记录。")
        return redirect("checkin_qr")

    now = timezone.now()
    checkin.check_out_time = now

    # Calculate duration
    if checkin.check_in_time:
        delta = now - checkin.check_in_time
        checkin.duration_minutes = int(delta.total_seconds() / 60)

    # Check early leave
    res_end = timezone.make_aware(
        datetime.combine(res.date, res.end_time),
        timezone.get_current_timezone()
    )
    if now < res_end - timedelta(minutes=15):
        checkin.is_early_leave = True

    checkin.save()
    res.status = "completed"
    res.save()

    messages.success(request, f"签退成功，本次自习 {checkin.duration_minutes} 分钟。")
    return redirect("checkin_qr")


@login_required
def temp_leave(request, reservation_id):
    """暂离申请"""
    res = get_object_or_404(Reservation, pk=reservation_id, user=request.user, status="checked_in")
    checkin = getattr(res, "checkin", None)
    if not checkin:
        return redirect("checkin_qr")

    if checkin.temp_leave_count >= 3:
        messages.error(request, "今日暂离次数已达上限(3次)。")
        return redirect("checkin_qr")

    TempLeave.objects.create(checkin=checkin, leave_time=timezone.now())
    checkin.temp_leave_count += 1
    checkin.save()

    messages.success(request, "已申请暂离，请在60分钟内返回。")
    return redirect("checkin_qr")


@login_required
def temp_return(request, reservation_id):
    """暂离返回"""
    res = get_object_or_404(Reservation, pk=reservation_id, user=request.user, status="checked_in")
    checkin = getattr(res, "checkin", None)
    if not checkin:
        return redirect("checkin_qr")

    last_leave = checkin.temp_leaves.filter(return_time__isnull=True).last()
    if not last_leave:
        messages.error(request, "没有进行中的暂离。")
        return redirect("checkin_qr")

    now = timezone.now()
    elapsed = (now - last_leave.leave_time).total_seconds() / 60
    last_leave.return_time = now
    if elapsed > 60:
        last_leave.is_timeout = True
    last_leave.save()

    if elapsed > 60:
        messages.warning(request, "暂离超时！扣3信用分。")
        # Deduct & create violation
        request.user.credit_score = max(0, request.user.credit_score - 3)
        request.user.save()
        CreditRecord.objects.create(
            user=request.user, change=-3, balance=request.user.credit_score,
            type="temp_leave_timeout", description=f"暂离超时-预约#{res.id}"
        )
        Violation.objects.create(
            user=request.user, reservation=res, type="temp_leave_timeout",
            points_deducted=-3, description=f"暂离超时({elapsed:.0f}分钟)",
            status="confirmed"
        )
    else:
        messages.success(request, f"已返回，暂离{elapsed:.0f}分钟。")

    return redirect("checkin_qr")
