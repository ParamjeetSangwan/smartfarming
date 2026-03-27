# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # FIX: removed confirm_order_view — it was a broken dead function
    # The working confirm_order lives in marketplace/views.py
    path('my-orders/', views.my_orders_view, name='my_orders'),
]