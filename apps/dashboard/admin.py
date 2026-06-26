from django.contrib import admin
from .models import OperationLog, SystemConfig, AdminRoom

@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "module", "action", "created_at"]
    list_filter = ["module", "created_at"]

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ["key", "description", "updated_at"]

@admin.register(AdminRoom)
class AdminRoomAdmin(admin.ModelAdmin):
    list_display = ["user", "room", "created_at"]
