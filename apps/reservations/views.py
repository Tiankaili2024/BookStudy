from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from datetime import date, datetime, timedelta
from .models import Reservation, WaitQueue
from apps.rooms.models import Room, Seat


@login_required
def reservation_create(request, seat_id, date_str):
    """预约座位"""
    seat = get_object_or_404(Seat.objects.select_related("room"), pk=seat_id)
    user = request.user

    # Check blacklist
    if user.status == "banned":
        now = timezone.now()
        active_black = user.blacklist_records.filter(
            Q(expired_at__isnull=True) | Q(expired_at__gt=now),
            removed_at__isnull=True
        ).first()
        if active_black:
            if active_black.expired_at:
                remaining = (active_black.expired_at - now).days
                messages.error(request, f"您当前在黑名单中，剩余 {remaining} 天。")
            else:
                messages.error(request, "您的账户已被永久列入黑名单。")
            return redirect("room_detail", pk=seat.room_id)

    # Check credit score
    if user.credit_score < 30:
        messages.error(request, "信用分不足30分，无法预约。")
        return redirect("room_detail", pk=seat.room_id)

    res_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Check if past
    if res_date < date.today():
        messages.error(request, "不能预约过去的日期。")
        return redirect("room_detail", pk=seat.room_id)

    # Check conflicts
    start = request.POST.get("start_time")
    end = request.POST.get("end_time")
    if not start or not end:
        messages.error(request, "请选择时段。")
        return redirect("room_detail", pk=seat.room_id)

    conflict = Reservation.objects.filter(
        seat_id=seat_id, date=res_date,
        start_time__lt=end, end_time__gt=start,
        status__in=["confirmed", "checked_in"]
    ).exists()
    if conflict:
        messages.error(request, "该时段已被预约，请选择其他时段或座位。")
        return redirect("room_detail", pk=seat.room_id)

    # Check user conflict
    user_conflict = Reservation.objects.filter(
        user=user, date=res_date,
        start_time__lt=end, end_time__gt=start,
        status__in=["confirmed", "checked_in"]
    ).exists()
    if user_conflict:
        messages.error(request, "您在该时段已有预约。")
        return redirect("room_detail", pk=seat.room_id)

    # Check daily limit
    today_count = Reservation.objects.filter(
        user=user, date=res_date,
        status__in=["confirmed", "checked_in", "completed"]
    ).count()
    if today_count >= 3:
        messages.error(request, "每日最多预约3个时段。")
        return redirect("room_detail", pk=seat.room_id)

    # Check recent no-show limit
    seven_days_ago = date.today() - timedelta(days=7)
    noshow_count = Reservation.objects.filter(
        user=user, date__gte=seven_days_ago, status="no_show"
    ).count()
    if noshow_count >= 2:
        messages.error(request, "7天内爽约2次，预约权限已被暂停3天。")
        return redirect("room_detail", pk=seat.room_id)

    res = Reservation.objects.create(
        user=user, seat=seat, date=res_date,
        start_time=start, end_time=end,
        status="confirmed", created_by=user
    )
    messages.success(request, f"预约成功！{res_date} {start}-{end} {seat.room.name}{seat.seat_number}")
    return redirect("my_reservations")


@login_required
def my_reservations(request):
    """我的预约列表"""
    status_filter = request.GET.get("status", "")
    res_list = request.user.reservations.all()
    if status_filter:
        res_list = res_list.filter(status=status_filter)
    res_list = res_list.select_related("seat__room").order_by("-date", "-start_time")
    return render(request, "reservations/my_list.html", {
        "reservations": res_list, "status_filter": status_filter
    })


@login_required
def cancel_reservation(request, pk):
    """取消预约"""
    res = get_object_or_404(Reservation, pk=pk, user=request.user)

    if res.status not in ["pending", "confirmed"]:
        messages.error(request, "该预约无法取消。")
        return redirect("my_reservations")

    # Calculate time diff
    res_start = timezone.make_aware(
        datetime.combine(res.date, res.start_time),
        timezone.get_current_timezone()
    )
    hours_left = (res_start - timezone.now()).total_seconds() / 3600

    if hours_left < 0.5:
        messages.error(request, "距离开始不足30分钟，无法取消。")
        return redirect("my_reservations")
    elif hours_left < 2:
        # Deduct 2 points
        res.user.credit_score = max(0, res.user.credit_score - 2)
        res.user.save()
        from apps.credits.models import CreditRecord
        CreditRecord.objects.create(
            user=res.user, change=-2, balance=res.user.credit_score,
            type="late", description=f"临近取消预约 #{res.id}"
        )
        messages.warning(request, "距离开不足2小时取消，扣除2信用分。")

    res.status = "cancelled"
    res.cancel_reason = request.POST.get("reason", "用户取消")
    res.save()

    # Notify wait queue
    notify_wait_queue(res)
    messages.success(request, "预约已取消。")
    return redirect("my_reservations")


def notify_wait_queue(reservation):
    """通知排队用户"""
    next_in_line = WaitQueue.objects.filter(
        seat=reservation.seat, date=reservation.date,
        start_time=reservation.start_time, end_time=reservation.end_time,
        status="waiting"
    ).first()
    if next_in_line:
        next_in_line.status = "notified"
        next_in_line.save()
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=next_in_line.user, title="候补成功",
            content=f"座位 {reservation.seat} 在 {reservation.date} {reservation.start_time}-{reservation.end_time} 有空位了，请尽快确认。",
            category="reservation"
        )


@login_required
def join_wait_queue(request, seat_id, date_str):
    """加入排队候补"""
    seat = get_object_or_404(Seat, pk=seat_id)
    res_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    start = request.POST.get("start_time")
    end = request.POST.get("end_time")
    if not start or not end:
        messages.error(request, "请选择时段。")
        return redirect("room_detail", pk=seat.room_id)

    WaitQueue.objects.create(
        user=request.user, seat=seat, date=res_date,
        start_time=start, end_time=end
    )
    messages.success(request, "已加入排队候补，有空位时我们会通知您。")
    return redirect("room_detail", pk=seat.room_id)


# ---------- Admin Reservation Management ----------

class ReservationManageView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/manage_list.html"
    context_object_name = "reservations"
    paginate_by = 20

    def get_queryset(self):
        qs = Reservation.objects.select_related("user", "seat__room").all()
        date_str = self.request.GET.get("date", "")
        status = self.request.GET.get("status", "")
        room_id = self.request.GET.get("room_id", "")
        if date_str:
            qs = qs.filter(date=date_str)
        if status:
            qs = qs.filter(status=status)
        if room_id:
            qs = qs.filter(seat__room_id=room_id)
        return qs.order_by("-date", "-start_time")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rooms"] = Room.objects.all()
        return ctx
