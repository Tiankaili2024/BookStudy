from django.urls import path
from . import views

urlpatterns = [
    path("", views.MyFeedbackView.as_view(), name="my_feedback"),
    path("add/", views.FeedbackCreateView.as_view(), name="feedback_add"),
    path("manage/", views.FeedbackManageView.as_view(), name="feedback_manage"),
    path("<int:pk>/", views.feedback_detail, name="feedback_detail"),
]
