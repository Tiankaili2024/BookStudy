from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from .models import Announcement


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = "announcements/list.html"
    context_object_name = "announcements"
    paginate_by = 10

    def get_queryset(self):
        now = timezone.now()
        return Announcement.objects.filter(
            Q(end_time__isnull=True) | Q(end_time__gte=now),
            start_time__lte=now
        ).order_by("-is_pinned", "-created_at")


class AnnouncementCreateView(AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model = Announcement
    template_name = "announcements/form.html"
    fields = ["title", "content", "is_pinned", "scope_type", "scope_value", "start_time", "end_time"]
    success_url = reverse_lazy("announcement_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
