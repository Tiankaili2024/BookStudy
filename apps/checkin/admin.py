from django.contrib import admin
from .models import CheckIn, TempLeave

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ["id", "reservation", "check_in_time", "check_out_time", "check_in_method", "is_ontime", "duration_minutes"]
    list_filter = ["check_in_method", "is_ontime", "check_in_time"]
