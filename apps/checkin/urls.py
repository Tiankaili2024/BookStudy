from django.urls import path
from . import views

urlpatterns = [
    path("", views.checkin_qr_view, name="checkin_qr"),
    path("do/<int:reservation_id>/", views.checkin_do, name="checkin_do"),
    path("out/<int:reservation_id>/", views.checkout, name="checkout"),
    path("leave/<int:reservation_id>/", views.temp_leave, name="temp_leave"),
    path("return/<int:reservation_id>/", views.temp_return, name="temp_return"),
]
