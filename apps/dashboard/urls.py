from django.urls import path
from . import views

urlpatterns = [
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("front-desk/", views.front_desk_dashboard, name="front_desk_dashboard"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
]
