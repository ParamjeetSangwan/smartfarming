# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('current/', views.current_orders, name='current_orders'),
    path('history/', views.order_history, name='order_history'),
    path('confirm/', views.confirm_order_view, name='confirm_order'),
    path('cart/', views.view_cart, name='view_cart'),
]