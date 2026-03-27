# orders/views.py
# FIX: Complete rewrite. Removed 4 broken dead functions:
#   - current_orders (used is_ordered field that doesn't exist)
#   - order_history (same)
#   - confirm_order_view (created OrderItem with wrong fields)
#   - view_cart (wrong related name + non-existent FKs)
# The working versions of all these live in marketplace/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Order


@login_required
def my_orders_view(request):
    """Simple orders list — used by orders app URL at /orders/my-orders/"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/current_orders.html', {'orders': orders})