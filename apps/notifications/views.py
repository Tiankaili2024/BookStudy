from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def my_notifications(request):
    notifs = request.user.notifications.all().order_by("-created_at")[:50]
    unread = request.user.notifications.filter(is_read=False).count()
    return render(request, "notifications/list.html", {"notifications": notifs, "unread": unread})


@login_required
def mark_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return redirect("my_notifications")


@login_required
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("my_notifications")
