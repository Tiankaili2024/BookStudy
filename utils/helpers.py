from django.utils import timezone
from datetime import date, timedelta


def get_week_range():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def is_peak_hour(hour):
    return 8 <= hour <= 12 or 14 <= hour <= 17 or 18 <= hour <= 21


def calculate_score_level(score):
    if score >= 120: return "diamond"
    if score >= 100: return "gold"
    if score >= 60: return "normal"
    if score >= 30: return "restricted"
    return "frozen"


def log_operation(user, module, action, detail=None, ip=""):
    from apps.dashboard.models import OperationLog
    return OperationLog.objects.create(
        user=user, module=module, action=action,
        detail=detail or {}, ip=ip
    )
