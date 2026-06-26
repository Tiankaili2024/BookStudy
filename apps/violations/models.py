from django.db import models
from django.conf import settings

class Violation(models.Model):
    TYPE_CHOICES = (
        ("no_show", "爽约"),
        ("late", "迟到"),
        ("severe_late", "严重迟到"),
        ("ghost_occupation", "占座不用"),
        ("proxy", "代签"),
        ("disorder", "扰乱秩序"),
        ("damage", "损坏设施"),
        ("temp_leave_timeout", "暂离超时"),
        ("item_left", "物品遗留"),
    )
    STATUS_CHOICES = (
        ("pending_review", "待审核"),
        ("confirmed", "已确认"),
        ("appealed", "申诉中"),
        ("overturned", "已撤销"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="violations", verbose_name="用户")
    reservation = models.ForeignKey("reservations.Reservation", on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="violations", verbose_name="关联预约")
    type = models.CharField("违规类型", max_length=30, choices=TYPE_CHOICES)
    points_deducted = models.IntegerField("扣分值", default=0)
    description = models.TextField("违规描述", blank=True, default="")
    evidence = models.ImageField("证据附件", upload_to="violations/", blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name="recorded_violations", verbose_name="登记人")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending_review")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_violation"
        verbose_name = "违规记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-{self.get_type_display()}-{self.created_at.date()}"


class Appeal(models.Model):
    STATUS_CHOICES = (
        ("pending", "待审核"),
        ("approved", "已通过"),
        ("rejected", "已驳回"),
        ("partially_approved", "部分通过"),
    )

    violation = models.ForeignKey(Violation, on_delete=models.CASCADE,
                                  related_name="appeals", verbose_name="关联违规")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="appeals", verbose_name="申诉人")
    reason = models.TextField("申诉理由")
    attachment = models.ImageField("附件", upload_to="appeals/", blank=True)
    status = models.CharField("状态", max_length=30, choices=STATUS_CHOICES, default="pending")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="reviewed_appeals", verbose_name="审核人")
    review_comment = models.TextField("审核意见", blank=True, default="")
    reviewed_at = models.DateTimeField("审核时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_appeal"
        verbose_name = "申诉记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]


class BlacklistRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="blacklist_records", verbose_name="用户")
    reason = models.TextField("入黑原因")
    days = models.IntegerField("处罚天数", default=7, help_text="0=永久")
    started_at = models.DateTimeField("生效时间")
    expired_at = models.DateTimeField("到期时间", null=True, blank=True)
    removed_at = models.DateTimeField("提前解除时间", null=True, blank=True)
    removed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="removed_blacklists", verbose_name="解除人")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_blacklist_record"
        verbose_name = "黑名单记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-黑名单({self.started_at.date()})"
