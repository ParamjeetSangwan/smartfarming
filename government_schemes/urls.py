# government_schemes/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.government_schemes_view, name='government_schemes'),
    path('track-apply/', views.track_apply_click, name='track_apply_click'),
    path('mark-applied/', views.mark_self_applied, name='mark_self_applied'),
]