from django.db import models
from django.conf import settings

class Announcement(models.Model):
    SCOPE_CHOICES = (
        ("all", "全平台"),
        ("room", "指定自习室"),
        ("college", "指定学院"),
    )

    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    attachment = models.FileField("附件", upload_to="announcements/", blank=True)
    is_pinned = models.BooleanField("置顶", default=False)
    scope_type = models.CharField("发布范围类型", max_length=20, choices=SCOPE_CHOICES, default="all")
    scope_value = models.JSONField("范围值", default=list, blank=True, help_text="自习室ID列表或学院名称列表")
    start_time = models.DateTimeField("生效时间")
    end_time = models.DateTimeField("失效时间", null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="announcements", verbose_name="发布人")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "bs_announcement"
        verbose_name = "公告"
        verbose_name_plural = verbose_name
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE,
                                     related_name="reads", verbose_name="公告")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    read_at = models.DateTimeField("阅读时间", auto_now_add=True)

    class Meta:
        db_table = "bs_announcement_read"
        verbose_name = "公告已读"
        verbose_name_plural = verbose_name
        unique_together = [("announcement", "user")]
