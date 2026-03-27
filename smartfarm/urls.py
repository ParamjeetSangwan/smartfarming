# smartfarm/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Language switcher — must be outside i18n_patterns
    path('i18n/', include('django.conf.urls.i18n')),

    # Root goes to login page
    path('', user_views.login_view, name='login'),
    path('users/', include('users.urls')),
    path('weather/', include('weather.urls')),
    path('crops/', include('crops.urls')),
    path('marketplace/', include('marketplace.urls', namespace='marketplace')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('ai-recommendations/', include('ai_recommendations.urls')),
    path('profile/', user_views.profile_view, name='profile'),
    path('admin/', admin.site.urls),
    path('myadmin/', include('admin_panel.urls')),
    path('schemes/', include('government_schemes.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)