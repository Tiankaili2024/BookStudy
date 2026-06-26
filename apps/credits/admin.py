from django.contrib import admin
from .models import CreditRecord

@admin.register(CreditRecord)
class CreditRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "change", "balance", "created_at"]
    list_filter = ["type", "created_at"]
    search_fields = ["user__student_id", "user__last_name"]
