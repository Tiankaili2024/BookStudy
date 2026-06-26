from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_credits, name="my_credits"),
    path("manage/", views.CreditManageView.as_view(), name="credit_manage"),
]
