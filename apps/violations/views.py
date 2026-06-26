from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from .models import Violation, Appeal, BlacklistRecord


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


@login_required
def my_violations(request):
    violations = request.user.violations.all().order_by("-created_at")
    return render(request, "violations/my_list.html", {"violations": violations})


@login_required
def submit_appeal(request, violation_id):
    violation = get_object_or_404(Violation, pk=violation_id, user=request.user)

    if violation.status != "confirmed":
        messages.error(request, "该违规记录不支持申诉。")
        return redirect("my_violations")

    # Check 48-hour window
    if (timezone.now() - violation.created_at).total_seconds() > 48 * 3600:
        messages.error(request, "已超过48小时申诉窗口。")
        return redirect("my_violations")

    if request.method == "POST":
        reason = request.POST.get("reason", "")
        if not reason.strip():
            messages.error(request, "请填写申诉理由。")
            return redirect("submit_appeal", violation_id=violation_id)

        Appeal.objects.create(violation=violation, user=request.user, reason=reason)
        violation.status = "appealed"
        violation.save()
        messages.success(request, "申诉已提交，请等待管理员审核。")
        return redirect("my_violations")

    return render(request, "violations/appeal_form.html", {"violation": violation})


class AppealManageView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = Appeal
    template_name = "violations/appeal_manage.html"
    context_object_name = "appeals"
    paginate_by = 20

    def get_queryset(self):
        qs = Appeal.objects.select_related("violation", "user").all()
        status = self.request.GET.get("status", "")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")


@login_required
def review_appeal(request, appeal_id):
    if request.user.role not in ["admin", "front_desk"]:
        return redirect("home")
    appeal = get_object_or_404(Appeal, pk=appeal_id)

    if request.method == "POST":
        result = request.POST.get("result")
        comment = request.POST.get("comment", "")
        appeal.reviewer = request.user
        appeal.review_comment = comment
        appeal.reviewed_at = timezone.now()

        if result == "approve":
            appeal.status = "approved"
            appeal.violation.status = "overturned"
            # Reverse credit deduction
            pts = abs(appeal.violation.points_deducted)
            appeal.user.credit_score = min(120, appeal.user.credit_score + pts)
            appeal.user.save()
            from apps.credits.models import CreditRecord
            CreditRecord.objects.create(
                user=appeal.user, change=pts, balance=appeal.user.credit_score,
                type="appeal_reversal", description=f"申诉撤销-违规#{appeal.violation.id}"
            )
            messages.success(request, "已通过申诉，撤销违规并返还积分。")
        elif result == "reject":
            appeal.status = "rejected"
            appeal.violation.status = "confirmed"
            messages.success(request, "已驳回申诉。")
        else:
            appeal.status = "partially_approved"
            appeal.violation.status = "overturned"
            messages.success(request, "已部分通过申诉。")

        appeal.save()
        appeal.violation.save()

        # Send notification
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=appeal.user, title="申诉结果",
            content=f"您的申诉「{appeal.violation.get_type_display()}」已{'通过' if appeal.status=='approved' else '被驳回'}。{comment}",
            category="appeal"
        )
        return redirect("appeal_manage")

    return render(request, "violations/appeal_review.html", {"appeal": appeal})


class BlacklistManageView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = BlacklistRecord
    template_name = "violations/blacklist_manage.html"
    context_object_name = "records"
    paginate_by = 20

    def get_queryset(self):
        return BlacklistRecord.objects.select_related("user").all().order_by("-created_at")
