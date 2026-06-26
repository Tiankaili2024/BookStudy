from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "student_id", "last_name", "first_name", "role", "credit_score", "status", "date_joined"]
    list_filter = ["role", "status", "college", "date_joined"]
    search_fields = ["username", "student_id", "first_name", "phone"]
    ordering = ["-date_joined"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("额外信息", {"fields": ("student_id", "phone", "college", "major", "grade",
                                  "role", "credit_score", "status", "avatar")}),
    )
