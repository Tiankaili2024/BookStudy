from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import User
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm

# ---------- Auth ----------

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "student"
            user.save()
            login(request, user)
            messages.success(request, "注册成功，初始信用分100分！")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserLoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            if user.status == "banned":
                messages.error(request, "账户已被列入黑名单，请联系管理员。")
                return render(request, "users/login.html", {"form": form})
            login(request, user)
            messages.success(request, f"欢迎回来，{user.last_name}{user.first_name}！")
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
    else:
        form = UserLoginForm(request=request)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "已退出登录。")
    return redirect("login")


# ---------- Profile ----------

@login_required
def profile_view(request):
    return render(request, "users/profile.html", {"profile_user": request.user})


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人信息已更新。")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "users/profile_edit.html", {"form": form})


# ---------- Admin: User Management ----------

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ["admin", "front_desk"]


class SuperAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == "admin"


class UserListView(SuperAdminRequiredMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search", "")
        role = self.request.GET.get("role", "")
        status = self.request.GET.get("status", "")
        if search:
            qs = qs.filter(
                Q(student_id__icontains=search) |
                Q(last_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(college__icontains=search)
            )
        if role:
            qs = qs.filter(role=role)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("search", "")
        ctx["role_filter"] = self.request.GET.get("role", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        return ctx
