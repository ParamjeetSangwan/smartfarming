from . import views
from django.urls import path
urlpatterns = [
    path('suggest/', views.crop_suggestion, name='crop_suggestion'),
]
