from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "系统管理员"),
        ("front_desk", "前台管理员"),
        ("student", "学生用户"),
    )
    STATUS_CHOICES = (
        ("active", "正常"),
        ("frozen", "冻结"),
        ("banned", "黑名单"),
        ("deleted", "注销"),
    )

    student_id = models.CharField("学号/工号", max_length=30, unique=True, db_index=True)
    phone = models.CharField("手机号", max_length=20, blank=True, default="")
    college = models.CharField("学院", max_length=100, blank=True, default="")
    major = models.CharField("专业", max_length=100, blank=True, default="")
    grade = models.CharField("年级", max_length=20, blank=True, default="")
    role = models.CharField("角色", max_length=20, choices=ROLE_CHOICES, default="student")
    credit_score = models.IntegerField("信用积分", default=100, db_index=True)
    status = models.CharField("账户状态", max_length=20, choices=STATUS_CHOICES, default="active")
    avatar = models.ImageField("头像", upload_to="avatars/", blank=True)

    class Meta:
        db_table = "bs_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.last_name}{self.first_name}({self.student_id})"
