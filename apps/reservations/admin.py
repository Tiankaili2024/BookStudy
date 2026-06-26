from django.contrib import admin
from .models import Reservation, WaitQueue

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "seat", "date", "start_time", "end_time", "status", "created_at"]
    list_filter = ["status", "date", "seat__room"]
    search_fields = ["user__student_id", "user__last_name", "user__first_name", "seat__seat_number"]
    date_hierarchy = "date"


@admin.register(WaitQueue)
class WaitQueueAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "seat", "date", "start_time", "end_time", "status"]
    list_filter = ["status", "date"]
