from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace_home, name='marketplace_home'),

    path('tools/', views.tools_view, name='tools_view'),
    path('tools/<int:tool_id>/', views.tool_detail, name='tool_detail'),
    path('tools/add/<int:tool_id>/', views.add_tool_to_cart, name='add_tool_to_cart'),

    path('pesticides/', views.pesticides_view, name='pesticides_view'),
    path('pesticides/<int:pesticide_id>/', views.pesticide_detail, name='pesticide_detail'),
    path('pesticides/add/<int:pesticide_id>/', views.add_pesticide_to_cart, name='add_pesticide_to_cart'),

    path('cart/', views.cart_view, name='cart_view'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('confirm_order/', views.confirm_order, name='confirm_order'),

    # UPI Payment (QR code)
    path('upi-payment/', views.upi_payment_view, name='upi_payment'),
    path('confirm-upi/', views.confirm_upi_payment, name='confirm_upi_payment'),

    # Razorpay Payment (verified automatically)
    path('razorpay-payment/', views.razorpay_payment_view, name='razorpay_payment'),
    path('razorpay-verify/', views.razorpay_verify, name='razorpay_verify'),

    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('track/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('clear-orders/', views.clear_orders, name='clear_orders'),
]