from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import razorpay
import json
import hmac
import hashlib

from .models import Tool, Pesticide
from apps.orders.models import Order, OrderItem, ShippingAddress


# ── Home ──
def marketplace_home(request):
    return render(request, 'marketplace/marketplace_home.html')


# ── Tools ──
@login_required
def tools_view(request):
    tools = Tool.objects.all()
    categories = Tool.objects.values_list('category', flat=True).distinct().order_by('category')
    min_price = Tool.objects.order_by('price').first().price if Tool.objects.exists() else 0
    max_price = Tool.objects.order_by('-price').first().price if Tool.objects.exists() else 1000

    selected_category = request.GET.get('category')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')

    if selected_category and selected_category != "All":
        tools = tools.filter(category=selected_category)
    if price_min:
        tools = tools.filter(price__gte=price_min)
    if price_max:
        tools = tools.filter(price__lte=price_max)

    return render(request, 'marketplace/tools.html', {
        'tools': tools, 'categories': categories,
        'min_price': min_price, 'max_price': max_price,
        'selected_category': selected_category,
        'price_min': price_min, 'price_max': price_max,
    })


@login_required
def tool_detail(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    related_tools = Tool.objects.filter(category=tool.category).exclude(id=tool_id)[:4]
    return render(request, 'marketplace/tool_detail.html', {
        'tool': tool, 'related_tools': related_tools,
    })


@login_required
def add_tool_to_cart(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    cart = request.session.get("cart", [])
    found = False
    for item in cart:
        if item["item_id"] == tool.id and item["item_type"] == "tool":
            item["quantity"] += 1
            found = True
            break
    if not found:
        cart.append({"item_type": "tool", "item_id": tool.id,
                     "name": tool.name, "price": float(tool.price), "quantity": 1})
    request.session["cart"] = cart
    request.session.modified = True
    messages.success(request, f"'{tool.name}' added to cart!")
    return redirect("marketplace:cart_view")


# ── Pesticides ──
@login_required
def pesticides_view(request):
    pesticides = Pesticide.objects.all()
    return render(request, 'marketplace/pesticides.html', {'pesticides': pesticides})


@login_required
def pesticide_detail(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    related = Pesticide.objects.exclude(id=pesticide_id)[:4]
    return render(request, 'marketplace/pesticides_detail.html', {
        'pesticide': pesticide, 'related': related,
    })


@login_required
def add_pesticide_to_cart(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    cart = request.session.get("cart", [])
    quantity = int(request.POST.get("quantity", 1))
    found = False
    for item in cart:
        if item["item_id"] == pesticide.id and item["item_type"] == "pesticide":
            item["quantity"] += quantity
            found = True
            break
    if not found:
        cart.append({"item_type": "pesticide", "item_id": pesticide.id,
                     "name": pesticide.name, "price": float(pesticide.price), "quantity": quantity})
    request.session["cart"] = cart
    request.session.modified = True
    messages.success(request, f"'{pesticide.name}' added to cart!")
    return redirect("marketplace:cart_view")


# ── Cart ──
def _build_cart_items(cart):
    """Helper to build cart items list from session cart"""
    cart_items = []
    total_price = 0
    for item in cart:
        try:
            product = None
            if item["item_type"] == "tool":
                product = Tool.objects.get(id=item["item_id"])
            elif item["item_type"] == "pesticide":
                product = Pesticide.objects.get(id=item["item_id"])
            if product:
                quantity = int(item.get("quantity", 1))
                subtotal = float(product.price) * quantity
                cart_items.append({
                    "item_id": item["item_id"], "item_type": item["item_type"],
                    "product": product, "quantity": quantity, "subtotal": subtotal,
                })
                total_price += subtotal
        except (Tool.DoesNotExist, Pesticide.DoesNotExist):
            continue
    return cart_items, total_price


@login_required
def cart_view(request):
    cart = request.session.get("cart", [])
    cart_items, total_price = _build_cart_items(cart)
    return render(request, "marketplace/cart.html", {
        "cart_items": cart_items, "total_price": total_price,
    })


@login_required
def update_cart(request):
    if request.method == "POST":
        cart = request.session.get("cart", [])
        updated_cart = []
        for i in range(len(cart)):
            item_id = request.POST.get(f"item_id_{i}")
            item_type = request.POST.get(f"item_type_{i}")
            quantity = request.POST.get(f"quantity_{i}")
            if item_id and quantity:
                try:
                    quantity = int(quantity)
                except ValueError:
                    quantity = 1
                if quantity > 0:
                    for item in cart:
                        if str(item["item_id"]) == str(item_id) and item["item_type"] == item_type:
                            item["quantity"] = quantity
                            updated_cart.append(item)
                            break
        request.session["cart"] = updated_cart
        request.session.modified = True
    return redirect("marketplace:cart_view")


# ── Checkout ──
@login_required
def checkout_view(request):
    cart = request.session.get("cart", [])
    if not cart:
        return redirect("marketplace:cart_view")

    cart_items, total_price = _build_cart_items(cart)
    saved_address = ShippingAddress.objects.filter(
        user=request.user, is_default=True
    ).first() or ShippingAddress.objects.filter(user=request.user).first()

    return render(request, "marketplace/checkout.html", {
        "cart_items": cart_items,
        "total_price": total_price,
        "saved_address": saved_address,
    })


# ── UPI QR code — set your UPI ID here ──
MERCHANT_UPI_ID = "paramjeetsangwan001@okicici"  # Change to your real UPI ID

# ── Razorpay client ──
def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

# ── Confirm Order ──
@login_required
def confirm_order(request):
    cart = request.session.get("cart", [])
    if not cart:
        return redirect("marketplace:cart_view")

    if request.method != "POST":
        return redirect("marketplace:checkout")

    full_name      = request.POST.get("full_name", "").strip()
    phone          = request.POST.get("phone", "").strip()
    alt_phone      = request.POST.get("alternate_phone", "").strip()
    address_line   = request.POST.get("address_line", "").strip()
    city           = request.POST.get("city", "").strip()
    state          = request.POST.get("state", "").strip()
    pincode        = request.POST.get("pincode", "").strip()
    landmark       = request.POST.get("landmark", "").strip()
    save_address   = request.POST.get("save_address") == "on"
    payment_method = request.POST.get("payment_method", "cod")

    if not all([full_name, phone, address_line, city, state, pincode]):
        messages.error(request, "Please fill in all required delivery details.")
        return redirect("marketplace:checkout")

    address = ShippingAddress.objects.create(
        user=request.user,
        full_name=full_name, phone=phone, alternate_phone=alt_phone,
        address_line=address_line, city=city, state=state,
        pincode=pincode, landmark=landmark,
        is_default=save_address,
    )
    if save_address:
        ShippingAddress.objects.filter(
            user=request.user, is_default=True
        ).exclude(id=address.id).update(is_default=False)

    total_price = sum(item["price"] * item["quantity"] for item in cart)

    # Online payment — create Razorpay order and redirect to payment page
    if payment_method in ["razorpay", "card", "stripe"]:
        # Check if Razorpay keys are configured
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            messages.error(request, "Online payment is not configured yet. Please use Cash on Delivery.")
            return redirect("marketplace:checkout")
        try:
            client = get_razorpay_client()
            amount_paise = int(total_price * 100)  # Razorpay uses paise
            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,  # Auto capture
                "notes": {
                    "customer": request.user.username,
                    "address": f"{city}, {state} - {pincode}",
                }
            })
            request.session["pending_order"] = {
                "full_name": full_name, "phone": phone, "alt_phone": alt_phone,
                "address_line": address_line, "city": city, "state": state,
                "pincode": pincode, "landmark": landmark,
                "address_id": address.id,
                "payment_method": payment_method,
                "total_price": total_price,
                "cart": cart,
                "razorpay_order_id": razorpay_order["id"],
            }
            request.session.modified = True
            return redirect("marketplace:razorpay_payment")
        except Exception as e:
            messages.error(request, f"Payment gateway error: {str(e)}. Please use COD.")
            return redirect("marketplace:checkout")

    # UPI — save data in session, redirect to QR payment page
    if payment_method == "upi":
        request.session["pending_order"] = {
            "full_name": full_name, "phone": phone, "alt_phone": alt_phone,
            "address_line": address_line, "city": city, "state": state,
            "pincode": pincode, "landmark": landmark,
            "address_id": address.id,
            "payment_method": payment_method,
            "total_price": total_price,
            "cart": cart,
        }
        request.session.modified = True
        return redirect("marketplace:upi_payment")

    # COD — create order immediately
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        total_price=total_price,
        payment_method=payment_method,
        status="pending",
        payment_status="pending",
    )
    for item in cart:
        OrderItem.objects.create(
            order=order, item_type=item["item_type"], item_id=item["item_id"],
            name=item["name"], price=item["price"], quantity=item["quantity"],
        )
    request.session["cart"] = []
    request.session.modified = True
    messages.success(request, f"Order #{order.id} placed successfully!")
    return redirect("marketplace:order_success", order_id=order.id)


# ── UPI Payment Page ──
@login_required
def upi_payment_view(request):
    pending = request.session.get("pending_order")
    if not pending:
        return redirect("marketplace:checkout")
    return render(request, "marketplace/upi_payment.html", {
        "total_price": pending["total_price"],
        "order_id": "PENDING",
        "upi_id": MERCHANT_UPI_ID,
        "payment_method": pending.get("payment_method", "upi"),
    })


# ── Razorpay Payment Page ──
@login_required
def razorpay_payment_view(request):
    pending = request.session.get("pending_order")
    if not pending or "razorpay_order_id" not in pending:
        return redirect("marketplace:checkout")
    return render(request, "marketplace/razorpay_payment.html", {
        "total_price": pending["total_price"],
        "razorpay_order_id": pending["razorpay_order_id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "user_name": request.user.get_full_name() or request.user.username,
        "user_email": request.user.email,
        "phone": pending.get("phone", ""),
    })


# ── Razorpay Payment Verification ──
@login_required
def razorpay_verify(request):
    if request.method != "POST":
        return redirect("marketplace:checkout")

    pending = request.session.get("pending_order")
    if not pending:
        messages.error(request, "Session expired. Please try again.")
        return redirect("marketplace:checkout")

    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id   = request.POST.get("razorpay_order_id", "")
    razorpay_signature  = request.POST.get("razorpay_signature", "")

    # Verify signature — this is the cryptographic proof payment is real
    try:
        client = get_razorpay_client()
        client.utility.verify_payment_signature({
            "razorpay_order_id":   razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature":  razorpay_signature,
        })
        payment_verified = True
    except razorpay.errors.SignatureVerificationError:
        payment_verified = False

    if not payment_verified:
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect("marketplace:checkout")

    # Payment verified — create order
    address = ShippingAddress.objects.filter(id=pending["address_id"]).first()
    total_price = pending["total_price"]
    cart = pending["cart"]
    payment_method = pending.get("payment_method", "razorpay")

    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        total_price=total_price,
        payment_method=payment_method,
        status="processing",      # Razorpay verified = go straight to processing
        payment_status="paid",    # Confirmed by signature verification
        upi_transaction_id=razorpay_payment_id,
    )
    for item in cart:
        OrderItem.objects.create(
            order=order, item_type=item["item_type"], item_id=item["item_id"],
            name=item["name"], price=item["price"], quantity=item["quantity"],
        )

    del request.session["pending_order"]
    request.session["cart"] = []
    request.session.modified = True
    messages.success(request, f"Payment successful! Order #{order.id} confirmed.")
    return redirect("marketplace:order_success", order_id=order.id)


# ── Confirm UPI Payment — requires transaction ID ──# ── Confirm UPI Payment — requires transaction ID ──
@login_required
def confirm_upi_payment(request):
    if request.method != "POST":
        return redirect("marketplace:checkout")

    pending = request.session.get("pending_order")
    if not pending:
        messages.error(request, "Session expired. Please try again.")
        return redirect("marketplace:checkout")

    # Get transaction ID — REQUIRED
    txn_id = request.POST.get("upi_transaction_id", "").strip().upper()

    # Must be present and at least 8 chars
    if not txn_id or len(txn_id) < 8:
        messages.error(request, "Please enter a valid UPI Transaction ID.")
        return redirect("marketplace:upi_payment")

    # Reject obvious fake/test IDs
    fake_patterns = ['12345678', 'TEST', 'FAKE', 'ABCDEFGH', '00000000',
                     'XXXXXXXX', '11111111', '99999999', '123456789']
    if any(txn_id.startswith(p) or txn_id == p for p in fake_patterns):
        messages.error(request, "Invalid Transaction ID. Please enter the real ID from your UPI app.")
        return redirect("marketplace:upi_payment")

    # Must contain at least one digit (real UPI txn IDs always have numbers)
    if not any(c.isdigit() for c in txn_id):
        messages.error(request, "Transaction ID must contain numbers. Please check your UPI app.")
        return redirect("marketplace:upi_payment")

    address = ShippingAddress.objects.filter(id=pending["address_id"]).first()
    total_price = pending["total_price"]
    cart = pending["cart"]
    payment_method = pending.get("payment_method", "upi")

    # Create order with pending verification status
    # Admin must verify the transaction ID before marking as paid
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        total_price=total_price,
        payment_method=payment_method,
        status="pending",           # Stays pending until admin verifies
        payment_status="pending",   # Stays pending until admin confirms payment
        upi_transaction_id=txn_id,  # Saved for admin to verify
    )
    for item in cart:
        OrderItem.objects.create(
            order=order, item_type=item["item_type"], item_id=item["item_id"],
            name=item["name"], price=item["price"], quantity=item["quantity"],
        )

    del request.session["pending_order"]
    request.session["cart"] = []
    request.session.modified = True
    messages.success(request, f"Order #{order.id} placed! Payment verification in progress.")
    return redirect("marketplace:order_success", order_id=order.id)


# ── Order Tracking ──
@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    for item in items:
        if item.item_type == 'tool':
            item.product = Tool.objects.filter(id=item.item_id).first()
        elif item.item_type == 'pesticide':
            item.product = Pesticide.objects.filter(id=item.item_id).first()
        else:
            item.product = None
    return render(request, 'marketplace/order_tracking.html', {
        'order': order, 'items': items,
    })


# ── Order Success ──
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    for item in items:
        if item.item_type == 'tool':
            item.product = Tool.objects.filter(id=item.item_id).first()
        elif item.item_type == 'pesticide':
            item.product = Pesticide.objects.filter(id=item.item_id).first()
    return render(request, 'marketplace/order_success.html', {
        'order': order, 'items': items,
    })


# ── My Orders ──
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    for order in orders:
        for item in order.items.all():
            if item.item_type == 'tool':
                item.product = Tool.objects.filter(id=item.item_id).first()
            elif item.item_type == 'pesticide':
                item.product = Pesticide.objects.filter(id=item.item_id).first()
            else:
                item.product = None
    return render(request, 'marketplace/my_orders.html', {'orders': orders})


# ── Clear Orders ──
@login_required
def clear_orders(request):
    if request.method == "POST":
        Order.objects.filter(user=request.user).delete()
        messages.success(request, "All your orders have been cleared.")
    return redirect("marketplace:my_orders")