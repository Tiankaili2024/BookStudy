from django.db import models
from django.conf import settings

class CreditRecord(models.Model):
    TYPE_CHOICES = (
        ("init", "初始积分"),
        ("no_show", "爽约"),
        ("late", "迟到"),
        ("severe_late", "严重迟到"),
        ("ghost_occupation", "占座不用"),
        ("proxy", "代签"),
        ("disorder", "扰乱秩序"),
        ("damage", "损坏设施"),
        ("temp_leave_timeout", "暂离超时"),
        ("item_left", "物品遗留"),
        ("streak_7", "连续7天"),
        ("streak_30", "连续30天"),
        ("attendance_90", "月出勤率>90%"),
        ("report_violation", "举报违规"),
        ("appeal_reversal", "申诉撤销"),
        ("manual", "手动调整"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="credit_records", verbose_name="用户")
    change = models.IntegerField("变动值")
    balance = models.IntegerField("变动后余额")
    type = models.CharField("变动类型", max_length=30, choices=TYPE_CHOICES)
    reference_id = models.IntegerField("关联业务ID", null=True, blank=True)
    description = models.CharField("说明", max_length=255, blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_credit_record"
        verbose_name = "积分记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-{self.get_type_display()}:{self.change:+d}"
