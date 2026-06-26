from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from datetime import date
from .models import Room, Seat, TimeSlot
from apps.reservations.models import Reservation


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


# ---------- Room Views ----------

class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        return Room.objects.filter(status="open").order_by("building", "floor", "name")


@login_required
def room_detail_view(request, pk):
    room = get_object_or_404(Room, pk=pk)
    today = date.today()
    seats = room.seats.all().order_by("row", "col")

    # Get reservation status for each seat for today
    reserved_seat_ids = set(
        Reservation.objects.filter(
            seat__room=room, date=today, status__in=["confirmed", "checked_in"]
        ).values_list("seat_id", flat=True)
    )

    max_row = max((s.row for s in seats), default=0) + 1
    max_col = max((s.col for s in seats), default=0) + 1

    # Build grid
    grid = []
    for r in range(max_row):
        row_seats = []
        for c in range(max_col):
            seat = next((s for s in seats if s.row == r and s.col == c), None)
            row_seats.append(seat)
        grid.append(row_seats)

    timeslots = room.timeslots.filter(is_active=True)

    return render(request, "rooms/room_detail.html", {
        "room": room, "grid": grid, "timeslots": timeslots,
        "reserved_seat_ids": reserved_seat_ids, "today": today,
    })


# ---------- Seat Management (Admin) ----------

class SeatManageView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = Seat
    template_name = "rooms/seat_manage.html"
    context_object_name = "seats"

    def get_queryset(self):
        qs = Seat.objects.select_related("room").all()
        room_id = self.request.GET.get("room_id")
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rooms"] = Room.objects.all()
        ctx["selected_room_id"] = self.request.GET.get("room_id", "")
        return ctx


class SeatCreateView(AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model = Seat
    template_name = "rooms/seat_form.html"
    fields = ["room", "seat_number", "row", "col", "seat_type", "tags", "status"]
    success_url = reverse_lazy("seat_manage")


class SeatUpdateView(AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Seat
    template_name = "rooms/seat_form.html"
    fields = ["seat_number", "row", "col", "seat_type", "tags", "status"]
    success_url = reverse_lazy("seat_manage")


class SeatDeleteView(AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Seat
    template_name = "rooms/seat_confirm_delete.html"
    success_url = reverse_lazy("seat_manage")


# ---------- TimeSlot Management ----------

class TimeSlotListView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = TimeSlot
    template_name = "rooms/timeslot_list.html"
    context_object_name = "timeslots"

    def get_queryset(self):
        qs = TimeSlot.objects.select_related("room").all()
        room_id = self.request.GET.get("room_id")
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rooms"] = Room.objects.all()
        ctx["selected_room_id"] = self.request.GET.get("room_id", "")
        return ctx


class TimeSlotCreateView(AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model = TimeSlot
    template_name = "rooms/timeslot_form.html"
    fields = ["room", "name", "start_time", "end_time", "is_active"]
    success_url = reverse_lazy("timeslot_list")
