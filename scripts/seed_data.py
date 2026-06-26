"""种子数据脚本 - 填充测试数据"""
import os, sys, django
from pathlib import Path

# Ensure project root is in path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from django.utils import timezone
from datetime import date, time, datetime, timedelta
from apps.users.models import User
from apps.rooms.models import Room, Seat, TimeSlot
from apps.reservations.models import Reservation
from apps.checkin.models import CheckIn
from apps.credits.models import CreditRecord
from apps.violations.models import Violation, BlacklistRecord
from apps.notifications.models import Notification
from apps.dashboard.models import AdminRoom, SystemConfig
from apps.announcements.models import Announcement
from apps.feedback.models import Feedback


def seed():
    print("=== 开始填充种子数据 ===\n")

    # ---------- 系统配置 ----------
    SystemConfig.objects.get_or_create(
        key="reservation_rules", defaults={
            "value": {"advance_days": 3, "max_per_day": 3, "max_future": 5, "noshow_freeze_days": 3},
            "description": "预约规则"
        }
    )
    SystemConfig.objects.get_or_create(
        key="checkin_rules", defaults={
            "value": {"window_before": 30, "window_after": 30, "temp_leave_max": 60, "temp_leave_count": 3},
            "description": "签到规则"
        }
    )
    print("[OK] 系统配置")

    # ---------- 前台管理员 ----------
    fd, _ = User.objects.get_or_create(
        username="frontdesk1", defaults={
            "student_id": "F0001", "last_name": "王", "first_name": "前台",
            "role": "front_desk", "credit_score": 100, "email": "frontdesk1@bookstudy.com"
        }
    )
    fd.set_password("admin123"); fd.save()
    print("[OK] 前台管理员")

    # ---------- 学生用户 ----------
    students = []
    names = [("张", "三"), ("李", "四"), ("王", "五"), ("赵", "六"), ("陈", "七"),
             ("刘", "八"), ("孙", "九"), ("周", "十"), ("吴", "十一"), ("郑", "十二")]
    for i, (ln, fn) in enumerate(names):
        s, _ = User.objects.get_or_create(
            username=f"student{i+1}", defaults={
                "student_id": f"S{1000+i+1}", "last_name": ln, "first_name": fn,
                "role": "student", "credit_score": 100 - i * 5, "college": "计算机学院",
                "major": "软件工程", "grade": "2024", "email": f"student{i+1}@bookstudy.com"
            }
        )
        s.set_password("student123"); s.save()
        students.append(s)
        CreditRecord.objects.get_or_create(
            user=s, type="init", defaults={"change": 100, "balance": s.credit_score, "description": "初始积分"}
        )
    print(f"[OK] {len(students)} 名学生")

    # ---------- 自习室 ----------
    room_data = [
        ("静音自习室A", "图书馆", 2, "silent", 24),
        ("普通自习室B", "图书馆", 2, "normal", 30),
        ("讨论区C", "图书馆", 3, "discussion", 16),
        ("电脑区D", "图书馆", 3, "computer", 20),
        ("通宵自习室E", "教学楼", 1, "normal", 40),
    ]
    rooms = []
    for name, bld, fl, tp, cap in room_data:
        r, _ = Room.objects.get_or_create(
            name=name, defaults={
                "building": bld, "floor": fl, "room_type": tp, "capacity": cap,
                "status": "open", "open_time": time(7, 0), "close_time": time(22, 0),
                "description": f"{name}，{cap}个座位"
            }
        )
        rooms.append(r)
    print(f"[OK] {len(rooms)} 个自习室")

    # ---------- 绑定前台 ----------
    for r in rooms[:3]:
        AdminRoom.objects.get_or_create(user=fd, room=r)

    # ---------- 座位 ----------
    for room in rooms:
        for i in range(room.capacity):
            row, col = i // 8, i % 8
            stype = "normal"
            if i % 7 == 0: stype = "power"
            elif i % 11 == 0: stype = "booth"
            Seat.objects.get_or_create(
                room=room, seat_number=f"{row+1}-{col+1:02d}",
                defaults={"row": row, "col": col, "seat_type": stype,
                          "tags": ["靠窗"] if col == 0 else [], "status": "available"}
            )
    total_seats = Seat.objects.count()
    print(f"[OK] {total_seats} 个座位")

    # ---------- 时段 ----------
    for room in rooms:
        for name, st, et in [("上午", time(8,0), time(12,0)), ("下午", time(13,0), time(17,0)), ("晚间", time(18,0), time(22,0))]:
            TimeSlot.objects.get_or_create(room=room, name=name, start_time=st, end_time=et, defaults={"is_active": True})
    print("[OK] 时段模板")

    # ---------- 预约 + 签到 ----------
    today = date.today()
    statuses = ["completed", "completed", "completed", "confirmed", "no_show", "completed", "cancelled", "checked_in"]
    for i, student in enumerate(students):
        room = rooms[i % len(rooms)]
        seat = room.seats.first()
        slot = room.timeslots.first()
        if not seat or not slot: continue

        offset = -i if i < 5 else i - 5
        res_date = today + timedelta(days=offset)
        status = statuses[i % len(statuses)]
        if res_date < today and status in ["confirmed", "checked_in"]: status = "completed"
        if res_date > today and status in ["checked_in", "completed", "no_show"]: status = "confirmed"

        res = Reservation.objects.create(
            user=student, seat=seat, date=res_date, start_time=slot.start_time,
            end_time=slot.end_time, status=status, created_by=student
        )

        if status in ["completed", "checked_in"]:
            ci_t = timezone.make_aware(datetime.combine(res_date, slot.start_time))
            if i == 4: ci_t += timedelta(minutes=10)
            CheckIn.objects.create(
                reservation=res, check_in_time=ci_t,
                check_out_time=ci_t + timedelta(minutes=180+i*30),
                is_ontime=(i != 4), duration_minutes=180+i*30
            )

        if status == "no_show":
            Violation.objects.create(user=student, reservation=res, type="no_show",
                                     points_deducted=-5, status="confirmed")
            CreditRecord.objects.create(user=student, change=-5, balance=student.credit_score,
                                        type="no_show", description="爽约扣分")

    # ---------- 黑名单样例 ----------
    BlacklistRecord.objects.create(
        user=students[0], reason="测试黑名单(已过期)", days=7,
        started_at=timezone.now() - timedelta(days=10),
        expired_at=timezone.now() - timedelta(days=3)
    )

    # ---------- 违规 ----------
    Violation.objects.create(user=students[1], type="late", points_deducted=-1, status="confirmed", description="迟到8分钟")
    CreditRecord.objects.create(user=students[1], change=-1, balance=students[1].credit_score, type="late", description="迟到扣分")

    # ---------- 公告 ----------
    Announcement.objects.create(
        title="考试周延长开放通知", content="6月25日-7月5日自习室延长至23:00。",
        is_pinned=True, scope_type="all",
        start_time=timezone.now() - timedelta(days=1),
        created_by=User.objects.get(username="admin")
    )

    # ---------- 反馈 ----------
    Feedback.objects.create(
        user=students[2], type="suggestion", title="建议增加充电插座",
        content="普通区希望能增加USB充电口。", status="pending"
    )

    # ---------- 通知 ----------
    Notification.objects.create(
        user=students[0], title="欢迎使用自习室预约系统",
        content="您的初始信用积分为100分，请遵守自习室规则。", category="system", is_read=False
    )

    print(f"\n=== 种子数据填充完成! ===")
    print(f"  管理员:   admin / admin123")
    print(f"  前台:     frontdesk1 / admin123")
    print(f"  学生:     student1 / student123 (共10名)")
    print(f"  自习室:   5个 | 座位: {total_seats}个")
    print(f"  预约:     {Reservation.objects.count()}条")
    print(f"  签到:     {CheckIn.objects.count()}条")


if __name__ == "__main__":
    seed()
