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
    path("confirm_order/", views.confirm_order, name="confirm_order"),
    path('cart/', views.cart_view, name='cart_view'),
    path("checkout/", views.checkout_view, name="checkout"),
    path('place_order/', views.place_order, name='place_order'),
    path("my_orders/", views.my_orders, name="my_orders"),
    path("update-cart/", views.update_cart, name="update_cart"),
    path("clear-orders/", views.clear_orders, name="clear_orders"),
]
