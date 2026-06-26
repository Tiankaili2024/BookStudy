from django.db import models
from django.conf import settings

class OperationLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, related_name="operation_logs", verbose_name="操作人")
    ip = models.CharField("IP地址", max_length=45)
    module = models.CharField("操作模块", max_length=50)
    action = models.CharField("操作动作", max_length=50)
    detail = models.JSONField("操作详情", default=dict)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        db_table = "bs_operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]


class SystemConfig(models.Model):
    key = models.CharField("配置键", max_length=100, unique=True, db_index=True)
    value = models.JSONField("配置值")
    description = models.CharField("说明", max_length=255, blank=True, default="")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, verbose_name="修改人")
    updated_at = models.DateTimeField("修改时间", auto_now=True)

    class Meta:
        db_table = "bs_system_config"
        verbose_name = "系统配置"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.key


class AdminRoom(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="admin_rooms", verbose_name="管理员")
    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE,
                             related_name="admins", verbose_name="自习室")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bs_admin_room"
        verbose_name = "管理员-自习室绑定"
        verbose_name_plural = verbose_name
        unique_together = [("user", "room")]
