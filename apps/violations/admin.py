from django.contrib import admin
from .models import Violation, Appeal, BlacklistRecord

@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "points_deducted", "status", "created_at"]
    list_filter = ["type", "status", "created_at"]
    search_fields = ["user__student_id", "user__last_name"]

@admin.register(Appeal)
class AppealAdmin(admin.ModelAdmin):
    list_display = ["id", "violation", "user", "status", "created_at"]
    list_filter = ["status"]

@admin.register(BlacklistRecord)
class BlacklistRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "days", "started_at", "expired_at", "removed_at"]
    list_filter = ["started_at"]
