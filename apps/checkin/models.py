from django.db import models
from django.conf import settings

class CheckIn(models.Model):
    METHOD_CHOICES = (
        ("qr", "二维码"),
        ("face", "人脸识别"),
        ("manual", "管理员手动"),
        ("gps", "GPS定位"),
    )

    reservation = models.OneToOneField("reservations.Reservation", on_delete=models.CASCADE,
                                       related_name="checkin", verbose_name="关联预约")
    check_in_time = models.DateTimeField("签到时间", null=True, blank=True)
    check_out_time = models.DateTimeField("签退时间", null=True, blank=True)
    check_in_method = models.CharField("签到方式", max_length=20, choices=METHOD_CHOICES, default="qr")
    is_ontime = models.BooleanField("是否准时", default=True)
    is_early_leave = models.BooleanField("是否早退", default=False)
    temp_leave_count = models.IntegerField("暂离次数", default=0)
    duration_minutes = models.IntegerField("在座时长(分钟)", default=0)

    class Meta:
        db_table = "bs_checkin"
        verbose_name = "签到记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.reservation.user.last_name}{self.reservation.user.first_name}-签到-{self.check_in_time}"


class TempLeave(models.Model):
    checkin = models.ForeignKey(CheckIn, on_delete=models.CASCADE, related_name="temp_leaves", verbose_name="签到记录")
    leave_time = models.DateTimeField("离开时间")
    return_time = models.DateTimeField("返回时间", null=True, blank=True)
    is_timeout = models.BooleanField("是否超时", default=False)

    class Meta:
        db_table = "bs_temp_leave"
        verbose_name = "暂离记录"
        verbose_name_plural = verbose_name
