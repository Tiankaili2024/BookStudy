from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Decorator: require specific role(s)"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.role not in roles:
                raise PermissionDenied("权限不足")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def ajax_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
