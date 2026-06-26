from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import CreditRecord


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


@login_required
def my_credits(request):
    records = request.user.credit_records.all().order_by("-created_at")[:100]
    return render(request, "credits/my_list.html", {
        "records": records, "score": request.user.credit_score
    })


class CreditManageView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model = CreditRecord
    template_name = "credits/manage_list.html"
    context_object_name = "records"
    paginate_by = 20

    def get_queryset(self):
        return CreditRecord.objects.select_related("user").all().order_by("-created_at")
