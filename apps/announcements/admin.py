from django.contrib import admin
from .models import Announcement, AnnouncementRead

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "scope_type", "is_pinned", "start_time", "created_at"]
    list_filter = ["scope_type", "is_pinned"]
