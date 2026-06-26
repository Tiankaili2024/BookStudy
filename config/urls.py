from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.dashboard.views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("users/", include("apps.users.urls")),
    path("rooms/", include("apps.rooms.urls")),
    path("reservations/", include("apps.reservations.urls")),
    path("checkin/", include("apps.checkin.urls")),
    path("violations/", include("apps.violations.urls")),
    path("credits/", include("apps.credits.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("announcements/", include("apps.announcements.urls")),
    path("feedback/", include("apps.feedback.urls")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
