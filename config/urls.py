from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse


def _no_content(request):
    return HttpResponse(status=204)


def _chrome_devtools(request):
    return JsonResponse({"workspace": {"root": "", "uuid": "focusflow-dev"}})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', _no_content),
    path('.well-known/appspecific/com.chrome.devtools.json', _chrome_devtools),
    path('', include('apps.core.urls')),
    path('', include('apps.sessions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.core.views.handler404'
handler500 = 'apps.core.views.handler500'
