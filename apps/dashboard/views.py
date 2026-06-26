from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from datetime import date, timedelta
import json

from apps.rooms.models import Room, Seat
from apps.reservations.models import Reservation
from apps.checkin.models import CheckIn
from apps.violations.models import Violation, BlacklistRecord
from apps.users.models import User
from apps.dashboard.models import OperationLog
from apps.credits.models import CreditRecord


def home(request):
    """首页 - 根据角色重定向到对应看板"""
    if not request.user.is_authenticated:
        rooms = Room.objects.filter(status="open")[:6]
        return render(request, "home.html", {"rooms": rooms})

    if request.user.role == "admin":
        return redirect("admin_dashboard")
    elif request.user.role == "front_desk":
        return redirect("front_desk_dashboard")
    else:
        return redirect("student_dashboard")


# ========== Student Dashboard ==========

@login_required
def student_dashboard(request):
    user = request.user
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # Stats
    total_reservations = user.reservations.count()
    total_duration = CheckIn.objects.filter(
        reservation__user=user, duration_minutes__gt=0
    ).aggregate(total=Sum("duration_minutes"))["total"] or 0

    completed = user.reservations.filter(status="completed").count()
    noshow = user.reservations.filter(status="no_show").count()
    attendance_rate = round(completed / max(completed + noshow, 1) * 100, 1)

    # Daily study heatmap (last 30 days)
    daily_data = []
    streak = 0
    max_streak = 0
    for i in range(30, -1, -1):
        d = today - timedelta(days=i)
        mins = CheckIn.objects.filter(
            reservation__user=user, reservation__date=d, duration_minutes__gt=0
        ).aggregate(total=Sum("duration_minutes"))["total"] or 0
        daily_data.append({"date": d.isoformat(), "minutes": mins, "level": min(4, mins // 60)})
        if mins > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # Time period distribution
    morning = CheckIn.objects.filter(
        reservation__user=user,
        check_in_time__hour__gte=6, check_in_time__hour__lt=12,
        duration_minutes__gt=0
    ).count()
    afternoon = CheckIn.objects.filter(
        reservation__user=user,
        check_in_time__hour__gte=12, check_in_time__hour__lt=18,
        duration_minutes__gt=0
    ).count()
    evening = CheckIn.objects.filter(
        reservation__user=user,
        check_in_time__hour__gte=18,
        duration_minutes__gt=0
    ).count()

    period_data = [
        {"name": "上午", "value": morning},
        {"name": "下午", "value": afternoon},
        {"name": "晚间", "value": evening},
    ]

    # Monthly trend
    months_data = []
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=1)
        month_start = month_start.replace(day=1)
        for _ in range(i):
            month_start = (month_start - timedelta(days=1)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if month_start > today:
            continue
        m = CheckIn.objects.filter(
            reservation__user=user, check_in_time__date__gte=month_start,
            check_in_time__date__lte=min(month_end, today),
            duration_minutes__gt=0
        ).aggregate(total=Sum("duration_minutes"))["total"] or 0
        months_data.append({"month": month_start.strftime("%Y-%m"), "hours": round(m / 60, 1)})

    # Upcoming reservations
    upcoming = user.reservations.filter(
        date__gte=today, status__in=["confirmed"]
    ).select_related("seat__room").order_by("date", "start_time")[:5]

    return render(request, "dashboard/student.html", {
        "total_reservations": total_reservations,
        "total_hours": round(total_duration / 60, 1),
        "attendance_rate": attendance_rate,
        "score": user.credit_score,
        "current_streak": streak,
        "max_streak": max_streak,
        "daily_data": json.dumps(daily_data),
        "period_data": json.dumps(period_data),
        "months_data": json.dumps(months_data),
        "upcoming": upcoming,
    })


# ========== Front Desk Dashboard ==========

@login_required
def front_desk_dashboard(request):
    if request.user.role not in ["admin", "front_desk"]:
        return redirect("student_dashboard")

    today = date.today()
    now = timezone.now()

    # Get managed rooms
    if request.user.role == "admin":
        rooms = Room.objects.all()
    else:
        room_ids = request.user.admin_rooms.values_list("room_id", flat=True)
        rooms = Room.objects.filter(id__in=room_ids)
    room_ids = rooms.values_list("id", flat=True)

    # Today stats
    today_reservations = Reservation.objects.filter(date=today, seat__room_id__in=room_ids)
    total_seats = Seat.objects.filter(room_id__in=room_ids, status="available").count()
    occupied = today_reservations.filter(status="checked_in").count()
    total_res = today_reservations.count()
    checked_in_count = today_reservations.filter(status="checked_in").count()
    completed_count = today_reservations.filter(status="completed").count()
    noshow_count = today_reservations.filter(status="no_show").count()

    # Weekly violation stats
    week_ago = today - timedelta(days=7)
    weekly_violations = Violation.objects.filter(
        created_at__date__gte=week_ago,
        user__reservations__seat__room_id__in=room_ids
    ).distinct()

    violation_by_type = weekly_violations.values("type").annotate(cnt=Count("id")).order_by("-cnt")

    # Hourly occupancy
    hourly_data = []
    for h in range(7, 24):
        count = today_reservations.filter(
            start_time__hour__lte=h, end_time__hour__gt=h, status__in=["confirmed", "checked_in"]
        ).count()
        hourly_data.append({"hour": f"{h}:00", "count": count})

    # Room utilization comparison
    room_stats = []
    for room in rooms:
        total = room.seats.filter(status="available").count() or 1
        used = today_reservations.filter(seat__room=room, status__in=["checked_in", "completed"]).count()
        room_stats.append({"name": room.name, "used": used, "total": total, "rate": round(used / total * 100, 1)})

    return render(request, "dashboard/front_desk.html", {
        "rooms": rooms, "today": today, "now": now,
        "total_seats": total_seats, "occupied": occupied,
        "total_res": total_res, "checked_in_count": checked_in_count,
        "completed_count": completed_count, "noshow_count": noshow_count,
        "violation_by_type": json.dumps(list(violation_by_type)),
        "hourly_data": json.dumps(hourly_data),
        "room_stats": json.dumps(room_stats),
    })


# ========== Admin Dashboard ==========

@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("home")

    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # Overall stats
    total_rooms = Room.objects.count()
    total_users = User.objects.filter(role="student").count()
    total_seats = Seat.objects.filter(status="available").count()
    banned_count = User.objects.filter(status="banned").count()

    # Today
    today_res = Reservation.objects.filter(date=today)
    today_checkin = today_res.filter(status="checked_in").count()

    # 30-day trends
    daily_trend = []
    for i in range(30, -1, -1):
        d = today - timedelta(days=i)
        cnt = Reservation.objects.filter(date=d).count()
        daily_trend.append({"date": d.isoformat(), "count": cnt})

    # Room comparison
    room_compare = []
    for room in Room.objects.all():
        r_count = Reservation.objects.filter(
            seat__room=room, date__gte=thirty_days_ago
        ).count()
        room_compare.append({"name": room.name, "count": r_count})

    # College comparison
    college_data = User.objects.filter(role="student").exclude(college="").values("college").annotate(
        total_duration=Sum("reservations__checkin__duration_minutes")
    ).order_by("-total_duration")[:10]

    # Violation rate
    month_violations = Violation.objects.filter(created_at__date__gte=thirty_days_ago).count()
    month_reservations = Reservation.objects.filter(date__gte=thirty_days_ago).count()
    violation_rate = round(month_violations / max(month_reservations, 1) * 100, 2)

    # System health
    recent = Reservation.objects.filter(date__gte=thirty_days_ago)
    reservation_total = recent.count()
    noshow_rate = round(recent.filter(status="no_show").count() / max(reservation_total, 1) * 100, 1)

    # Active users (last 7 days)
    week_ago = today - timedelta(days=7)
    active_users = Reservation.objects.filter(
        date__gte=week_ago
    ).values("user").distinct().count()

    return render(request, "dashboard/admin.html", {
        "total_rooms": total_rooms, "total_users": total_users,
        "total_seats": total_seats, "banned_count": banned_count,
        "today_checkin": today_checkin, "today_res": today_res.count(),
        "daily_trend": json.dumps(daily_trend),
        "room_compare": json.dumps(room_compare),
        "college_data": json.dumps(list(college_data)),
        "violation_rate": violation_rate, "noshow_rate": noshow_rate,
        "active_users": active_users,
    })
