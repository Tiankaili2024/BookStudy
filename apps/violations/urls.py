from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_violations, name="my_violations"),
    path("appeal/<int:violation_id>/", views.submit_appeal, name="submit_appeal"),
    path("appeals/manage/", views.AppealManageView.as_view(), name="appeal_manage"),
    path("appeals/review/<int:appeal_id>/", views.review_appeal, name="review_appeal"),
    path("blacklist/", views.BlacklistManageView.as_view(), name="blacklist_manage"),
]
