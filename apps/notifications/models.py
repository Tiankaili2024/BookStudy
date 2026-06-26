from django.db import models
from django.conf import settings

class Notification(models.Model):
    CATEGORY_CHOICES = (
        ("reservation", "预约通知"),
        ("checkin", "签到提醒"),
        ("violation", "违规通知"),
        ("blacklist", "黑名单通知"),
        ("appeal", "申诉结果"),
        ("system", "系统通知"),
        ("announcement", "公告"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="notifications", verbose_name="用户")
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    category = models.CharField("分类", max_length=30, choices=CATEGORY_CHOICES, default="system")
    is_read = models.BooleanField("已读", default=False, db_index=True)
    channels = models.JSONField("发送渠道", default=list)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_notification"
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-{self.title}"
