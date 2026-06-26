from django.db import models
from django.conf import settings

class Feedback(models.Model):
    TYPE_CHOICES = (
        ("bug", "故障报修"),
        ("suggestion", "建议"),
        ("complaint", "投诉"),
    )
    STATUS_CHOICES = (
        ("pending", "待处理"),
        ("processing", "处理中"),
        ("resolved", "已解决"),
        ("closed", "已关闭"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="feedbacks", verbose_name="用户")
    type = models.CharField("类型", max_length=20, choices=TYPE_CHOICES)
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    attachment = models.ImageField("附件", upload_to="feedback/", blank=True)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    handler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="handled_feedbacks", verbose_name="处理人")
    reply = models.TextField("回复", blank=True, default="")
    rating = models.IntegerField("满意度(1-5)", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_feedback"
        verbose_name = "反馈"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.last_name}{self.user.first_name}-{self.title}"
