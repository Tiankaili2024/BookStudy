from django.core.exceptions import ValidationError
import re


def validate_student_id(value):
    if not re.match(r"^[A-Za-z0-9]{4,20}$", value):
        raise ValidationError("学号/工号为4-20位字母或数字")


def validate_phone_cn(value):
    if value and not re.match(r"^1[3-9]\d{9}$", value):
        raise ValidationError("请输入有效的中国大陆手机号")
