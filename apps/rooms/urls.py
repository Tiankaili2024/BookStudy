from django.urls import path
from . import views

urlpatterns = [
    path("", views.RoomListView.as_view(), name="room_list"),
    path("<int:pk>/", views.room_detail_view, name="room_detail"),
    path("seats/", views.SeatManageView.as_view(), name="seat_manage"),
    path("seats/add/", views.SeatCreateView.as_view(), name="seat_add"),
    path("seats/<int:pk>/edit/", views.SeatUpdateView.as_view(), name="seat_edit"),
    path("seats/<int:pk>/delete/", views.SeatDeleteView.as_view(), name="seat_delete"),
    path("timeslots/", views.TimeSlotListView.as_view(), name="timeslot_list"),
    path("timeslots/add/", views.TimeSlotCreateView.as_view(), name="timeslot_add"),
]
