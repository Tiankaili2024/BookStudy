"""核心业务逻辑单元测试 - 模型层 + 简易视图测试"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, datetime, timedelta
from apps.users.models import User
from apps.rooms.models import Room, Seat, TimeSlot
from apps.reservations.models import Reservation, WaitQueue
from apps.checkin.models import CheckIn, TempLeave
from apps.violations.models import Violation, Appeal, BlacklistRecord
from apps.credits.models import CreditRecord
from apps.notifications.models import Notification
from apps.announcements.models import Announcement
from apps.feedback.models import Feedback
from apps.dashboard.models import OperationLog, SystemConfig, AdminRoom


class UserModelTest(TestCase):
    def test_create_user(self):
        u = User.objects.create_user(username="test", password="pass12345", student_id="S001", role="student")
        self.assertEqual(u.credit_score, 100)
        self.assertEqual(u.role, "student")
        self.assertEqual(u.status, "active")

    def test_user_str(self):
        u = User.objects.create_user(username="u1", password="pass12345", student_id="X001",
                                      last_name="张", first_name="三")
        self.assertIn("张三", str(u))
        self.assertIn("X001", str(u))

    def test_credit_score_default(self):
        u = User.objects.create_user(username="fresh", password="pass12345", student_id="N001")
        self.assertEqual(u.credit_score, 100)


class RoomSeatModelTest(TestCase):
    def setUp(self):
        self.room = Room.objects.create(name="测试室", building="A楼", floor=2, capacity=30, status="open")
        self.seat = Seat.objects.create(room=self.room, seat_number="A-01", row=0, col=0, status="available")

    def test_room_creation(self):
        self.assertEqual(str(self.room), "A楼2F-测试室")

    def test_seat_creation(self):
        self.assertIn("测试室", str(self.seat))
        self.assertIn("A-01", str(self.seat))

    def test_seat_unique(self):
        with self.assertRaises(Exception):
            Seat.objects.create(room=self.room, seat_number="A-01", row=0, col=1)

    def test_timeslot_creation(self):
        ts = TimeSlot.objects.create(name="上午", start_time=time(8,0), end_time=time(12,0))
        self.assertIn("上午", str(ts))


class ReservationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ruser", password="pass12345", student_id="R001")
        self.room = Room.objects.create(name="预约测试", building="A", floor=1, capacity=10, status="open")
        self.seat = Seat.objects.create(room=self.room, seat_number="1-01", row=0, col=0)
        self.today = date.today()

    def test_create_reservation(self):
        res = Reservation.objects.create(
            user=self.user, seat=self.seat, date=self.today,
            start_time=time(8,0), end_time=time(12,0), status="confirmed"
        )
        self.assertEqual(res.status, "confirmed")
        self.assertEqual(self.user.reservations.count(), 1)

    def test_reservation_str(self):
        res = Reservation.objects.create(
            user=self.user, seat=self.seat, date=self.today,
            start_time=time(8,0), end_time=time(12,0), status="confirmed"
        )
        self.assertIn(self.seat.seat_number, str(res))

    def test_conflict_detection(self):
        Reservation.objects.create(
            user=self.user, seat=self.seat, date=self.today,
            start_time=time(8,0), end_time=time(12,0), status="confirmed"
        )
        conflict = Reservation.objects.filter(
            seat=self.seat, date=self.today,
            start_time__lt=time(12,0), end_time__gt=time(8,0),
            status__in=["confirmed", "checked_in"]
        ).exists()
        self.assertTrue(conflict)

    def test_wait_queue(self):
        wq = WaitQueue.objects.create(
            user=self.user, seat=self.seat, date=self.today,
            start_time=time(8,0), end_time=time(12,0)
        )
        self.assertEqual(wq.status, "waiting")


class CheckinModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cuser", password="pass12345", student_id="C001")
        self.room = Room.objects.create(name="签到测试", building="A", floor=1, capacity=10, status="open")
        self.seat = Seat.objects.create(room=self.room, seat_number="1-01", row=0, col=0)
        self.res = Reservation.objects.create(
            user=self.user, seat=self.seat, date=date.today(),
            start_time=time(8,0), end_time=time(12,0), status="confirmed"
        )

    def test_checkin_create(self):
        ci = CheckIn.objects.create(
            reservation=self.res, check_in_time=timezone.now(),
            is_ontime=True, duration_minutes=120
        )
        self.assertEqual(ci.duration_minutes, 120)
        self.assertTrue(ci.is_ontime)

    def test_checkin_late(self):
        ci = CheckIn.objects.create(
            reservation=self.res, check_in_time=timezone.now(),
            is_ontime=False, duration_minutes=100
        )
        self.assertFalse(ci.is_ontime)

    def test_temp_leave(self):
        ci = CheckIn.objects.create(
            reservation=self.res, check_in_time=timezone.now(), duration_minutes=60
        )
        tl = TempLeave.objects.create(checkin=ci, leave_time=timezone.now())
        self.assertIsNone(tl.return_time)
        self.assertEqual(ci.temp_leaves.count(), 1)


class ViolationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="vuser", password="pass12345", student_id="V001")
        self.room = Room.objects.create(name="违规测试", building="A", floor=1, capacity=10, status="open")
        self.seat = Seat.objects.create(room=self.room, seat_number="1-01", row=0, col=0)
        self.res = Reservation.objects.create(
            user=self.user, seat=self.seat, date=date.today(),
            start_time=time(8,0), end_time=time(12,0), status="confirmed"
        )

    def test_create_violation(self):
        v = Violation.objects.create(
            user=self.user, type="no_show", points_deducted=-5, status="confirmed",
            description="未签到"
        )
        self.assertEqual(v.points_deducted, -5)
        self.assertEqual(v.type, "no_show")

    def test_appeal_create(self):
        v = Violation.objects.create(
            user=self.user, type="late", points_deducted=-1, status="confirmed"
        )
        a = Appeal.objects.create(violation=v, user=self.user, reason="测试申诉")
        self.assertEqual(a.status, "pending")

    def test_blacklist_create(self):
        bl = BlacklistRecord.objects.create(
            user=self.user, reason="测试封禁", days=7,
            started_at=timezone.now(),
            expired_at=timezone.now() + timedelta(days=7)
        )
        self.assertEqual(bl.days, 7)

    def test_blacklist_permanent(self):
        bl = BlacklistRecord.objects.create(
            user=self.user, reason="永久封禁", days=0,
            started_at=timezone.now()
        )
        self.assertIsNone(bl.expired_at)


class CreditModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cruser", password="pass12345", student_id="CR001")

    def test_credit_record(self):
        cr = CreditRecord.objects.create(user=self.user, change=-5, balance=95, type="no_show")
        self.assertEqual(cr.change, -5)
        self.assertEqual(cr.balance, 95)

    def test_credit_record_positive(self):
        cr = CreditRecord.objects.create(user=self.user, change=3, balance=103, type="streak_7")
        self.assertEqual(cr.change, 3)


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="nuser", password="pass12345", student_id="N001")

    def test_notification_create(self):
        n = Notification.objects.create(
            user=self.user, title="测试通知", content="这是一条测试",
            category="system", is_read=False
        )
        self.assertFalse(n.is_read)
        self.assertEqual(n.category, "system")


class AnnouncementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auser", password="pass12345", student_id="A001")

    def test_announcement_create(self):
        a = Announcement.objects.create(
            title="测试公告", content="测试内容",
            is_pinned=True, scope_type="all",
            start_time=timezone.now(), created_by=self.user
        )
        self.assertTrue(a.is_pinned)


class FeedbackModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fuser", password="pass12345", student_id="F001")

    def test_feedback_create(self):
        f = Feedback.objects.create(
            user=self.user, type="suggestion", title="测试反馈",
            content="建议增加座位", status="pending"
        )
        self.assertEqual(f.status, "pending")


class DashboardModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="duser", password="pass12345", student_id="D001")

    def test_config_create(self):
        c = SystemConfig.objects.create(key="test_key", value={"a": 1}, description="测试配置")
        self.assertEqual(c.key, "test_key")
        self.assertEqual(c.value, {"a": 1})

    def test_operation_log(self):
        log = OperationLog.objects.create(
            user=self.user, ip="127.0.0.1", module="users", action="login",
            detail={"result": "success"}
        )
        self.assertEqual(log.module, "users")


class AdminRoomTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="aduser", password="pass12345", student_id="AD001")
        self.room = Room.objects.create(name="管理测试", building="A", floor=1, capacity=10, status="open")

    def test_admin_room_binding(self):
        ar = AdminRoom.objects.create(user=self.user, room=self.room)
        self.assertEqual(self.user.admin_rooms.count(), 1)
        self.assertEqual(self.room.admins.count(), 1)
