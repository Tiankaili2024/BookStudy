from django.contrib import admin
from .models import Room, Seat, TimeSlot, SpecialSchedule

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "building", "floor", "capacity", "room_type", "status"]
    list_filter = ["status", "room_type", "building"]
    search_fields = ["name", "building"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["seat_number", "room", "seat_type", "status", "row", "col"]
    list_filter = ["seat_type", "status", "room"]
    search_fields = ["seat_number", "room__name"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["name", "start_time", "end_time", "room", "is_active"]
    list_filter = ["is_active", "room"]


@admin.register(SpecialSchedule)
class SpecialScheduleAdmin(admin.ModelAdmin):
    list_display = ["room", "date", "is_closed", "reason"]
    list_filter = ["is_closed", "room"]
