from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "type", "status", "rating", "created_at"]
    list_filter = ["type", "status"]
