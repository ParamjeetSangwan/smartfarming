from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order
from django.shortcuts import render, redirect
from orders.models import Order, OrderItem
from marketplace.models import Tool




@login_required
def current_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=False).order_by('-created_at')
    return render(request, 'orders/current_orders.html', {'orders': orders})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Order

@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {'orders': orders})



@login_required
def confirm_order_view(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')  # nothing to confirm

    total_price = 0
    items = []

    for product_id, item in cart.items():
        try:
            product = Tool.objects.get(id=product_id)
            quantity = item['quantity']
            price = product.price * quantity
            total_price += price

            items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
            })
        except Tool.DoesNotExist:
            continue

    # Create the order
    order = Order.objects.create(user=request.user, total_price=total_price)

    # Create the OrderItems
    for item in items:
        OrderItem.objects.create(
            order=order,
            user=request.user,
            product=item['product'],
            quantity=item['quantity'],
        )

    # Clear the session cart
    request.session['cart'] = {}

    return render(request, 'marketplace/confirmation.html', {'order': order})



@login_required
def view_cart(request):
    orders = Order.objects.filter(user=request.user, is_ordered=False).prefetch_related('order_items__pesticide', 'order_items__tool')
    return render(request, 'orders/view_cart.html', {'orders': orders})