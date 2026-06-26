from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_reservations, name="my_reservations"),
    path("book/<int:seat_id>/<str:date_str>/", views.reservation_create, name="reservation_create"),
    path("cancel/<int:pk>/", views.cancel_reservation, name="cancel_reservation"),
    path("wait/<int:seat_id>/<str:date_str>/", views.join_wait_queue, name="join_wait_queue"),
    path("manage/", views.ReservationManageView.as_view(), name="reservation_manage"),
]
