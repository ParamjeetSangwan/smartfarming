# orders/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Order, OrderItem, ShippingAddress


@login_required
def my_orders_view(request):
    """Simple orders list — used by orders app URL at /orders/my-orders/"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/current_orders.html', {'orders': orders})


@login_required
def current_orders(request):
    """View current/active orders for the user"""
    orders = Order.objects.filter(
        user=request.user,
        status__in=['pending', 'processing', 'shipped']
    ).order_by('-created_at')
    context = {
        'orders': orders,
        'page_title': 'Current Orders',
        'order_status': 'active'
    }
    return render(request, 'orders/current_orders.html', context)


@login_required
def order_history(request):
    """View order history for the user (completed/cancelled orders)"""
    orders = Order.objects.filter(
        user=request.user,
        status__in=['delivered', 'cancelled', 'returned']
    ).order_by('-created_at')
    context = {
        'orders': orders,
        'page_title': 'Order History',
        'order_status': 'history'
    }
    return render(request, 'orders/order_history.html', context)


@login_required
def confirm_order_view(request):
    """Process and confirm order before payment"""
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        if not cart:
            messages.error(request, 'Your cart is empty!')
            return redirect('marketplace:cart_view')
        
        # Get shipping address
        shipping_address_id = request.POST.get('shipping_address')
        if not shipping_address_id:
            messages.error(request, 'Please select a shipping address!')
            return redirect('marketplace:checkout_view')
        
        shipping_address = get_object_or_404(ShippingAddress, id=shipping_address_id, user=request.user)
        
        # Calculate total
        total_price = sum(item['price'] * item['quantity'] for item in cart)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            total_price=total_price,
            payment_method=request.POST.get('payment_method', 'cod'),
            status='pending'
        )
        
        # Create order items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                item_type=item.get('item_type', 'tool'),
                item_id=item['item_id'],
                name=item['name'],
                price=item['price'],
                quantity=item['quantity']
            )
        
        # Clear cart
        request.session['cart'] = []
        request.session.modified = True
        
        messages.success(request, f'Order #{order.id} confirmed!')
        return redirect('marketplace:order_success_view', order_id=order.id)
    
    return redirect('marketplace:checkout_view')


@login_required
def view_cart(request):
    """View current shopping cart"""
    cart = request.session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    
    context = {
        'cart_items': cart,
        'total_price': total_price,
        'cart_count': len(cart)
    }
    return render(request, 'marketplace/cart.html', context)