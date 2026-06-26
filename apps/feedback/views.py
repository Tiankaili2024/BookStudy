from django.views.generic import ListView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Feedback


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    template_name = "feedback/form.html"
    fields = ["type", "title", "content", "attachment"]
    success_url = reverse_lazy("my_feedback")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MyFeedbackView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/my_list.html"
    context_object_name = "feedbacks"
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.feedbacks.all().order_by("-created_at")


class FeedbackManageView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/manage_list.html"
    context_object_name = "feedbacks"
    paginate_by = 20

    def get_queryset(self):
        qs = Feedback.objects.select_related("user").all()
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")


@login_required
def feedback_detail(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if request.method == "POST" and request.user.role in ["admin", "front_desk"]:
        reply = request.POST.get("reply", "")
        new_status = request.POST.get("status", feedback.status)
        if reply:
            feedback.reply = reply
        feedback.handler = request.user
        feedback.status = new_status
        feedback.save()
        messages.success(request, "已回复反馈。")
        return redirect("feedback_manage")
    return render(request, "feedback/detail.html", {"feedback": feedback})
