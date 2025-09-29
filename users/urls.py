from django.urls import path
from . import views
from .views import dashboard_view
from django.contrib.auth.views import LogoutView  
from .views import orders_view


urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('ai/', views.ai_recommendations_view, name='ai_recommendations'),
    path('orders/', orders_view, name='orders'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),


]
