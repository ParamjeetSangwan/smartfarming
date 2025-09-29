from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    

    # Auth / Main
    path('', user_views.login_view, name='login'),  # or redirect to dashboard if logged in
    path('users/', include('users.urls')),

    # Feature Apps
    path('weather/', include('weather.urls')),
    path('crops/', include('crops.urls')),
    path('marketplace/', include('marketplace.urls', namespace='marketplace')),
    path('orders/', include('orders.urls')),
    path('ai-recommendations/', include('ai_recommendations.urls')),
    path('profile/', user_views.profile_view, name='profile'),
    path('admin/', admin.site.urls),
    path('orders/', include('orders.urls', namespace='orders')),
    # path('recommendations/', include('recommendations.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
