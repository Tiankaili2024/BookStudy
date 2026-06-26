from django.db import models
from django.conf import settings

class Reservation(models.Model):
    STATUS_CHOICES = (
        ("pending", "待确认"),
        ("confirmed", "已确认"),
        ("checked_in", "已签到"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
        ("no_show", "爽约"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="reservations", verbose_name="用户")
    seat = models.ForeignKey("rooms.Seat", on_delete=models.CASCADE,
                             related_name="reservations", verbose_name="座位")
    date = models.DateField("预约日期", db_index=True)
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    cancel_reason = models.CharField("取消原因", max_length=255, blank=True, default="")
    is_temp = models.BooleanField("临时预约", default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name="created_reservations", verbose_name="创建人")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "bs_reservation"
        verbose_name = "预约记录"
        verbose_name_plural = verbose_name
        ordering = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["seat", "date"]),
        ]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-{self.seat}-{self.date}"


class WaitQueue(models.Model):
    STATUS_CHOICES = (
        ("waiting", "等待中"),
        ("notified", "已通知"),
        ("accepted", "已接受"),
        ("expired", "已过期"),
        ("cancelled", "已取消"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="wait_queues", verbose_name="用户")
    seat = models.ForeignKey("rooms.Seat", on_delete=models.CASCADE,
                             related_name="wait_queues", verbose_name="座位")
    date = models.DateField("日期")
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="waiting")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_wait_queue"
        verbose_name = "排队候补"
        verbose_name_plural = verbose_name
        ordering = ["created_at"]
