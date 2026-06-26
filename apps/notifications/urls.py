from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_notifications, name="my_notifications"),
    path("read/<int:pk>/", views.mark_read, name="mark_read"),
    path("read-all/", views.mark_all_read, name="mark_all_read"),
]
