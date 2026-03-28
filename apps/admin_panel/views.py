# admin_panel/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import json

from apps.marketplace.models import Tool, Pesticide
from apps.orders.models import Order, OrderItem
from apps.crops.models import Crop
from apps.ai_recommendations.models import AIQueryHistory
from apps.users.models import UserProfile, Notification, Announcement, AdminTwoFactor
from apps.government_schemes.models import SchemeInterest

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Admin only.')
            return redirect('login')  # FIX: was redirect('dashboard') — sent to user dashboard
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper



# ──────────────────────────────────────────────
# ADD THIS IMPORT at the top of admin_panel/views.py
# (add alongside the existing imports)
# ──────────────────────────────────────────────
# from apps.government_schemes.models import SchemeInterest

@admin_required
def admin_schemes_view(request):
    from apps.government_schemes.models import SchemeInterest
    from django.db.models import Count

    interests = SchemeInterest.objects.select_related('user').order_by('-updated_at')

    # Filters
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    if search:
        interests = interests.filter(
            Q(scheme_name__icontains=search) | Q(user__username__icontains=search)
        )
    if status_filter:
        interests = interests.filter(status=status_filter)

    # Stats
    total_interests = SchemeInterest.objects.count()
    total_applied = SchemeInterest.objects.filter(self_marked_applied=True).count()
    total_clicked = SchemeInterest.objects.filter(clicked_apply=True).count()
    total_users_engaged = SchemeInterest.objects.values('user').distinct().count()

    # Most popular schemes
    popular_schemes = (
        SchemeInterest.objects.values('scheme_name')
        .annotate(
            interest_count=Count('id'),
            applied_count=Count('id', filter=Q(self_marked_applied=True)),
            click_count=Count('id', filter=Q(clicked_apply=True)),
        )
        .order_by('-interest_count')[:10]
    )

    context = {
        'interests': interests,
        'search': search,
        'status_filter': status_filter,
        'total_interests': total_interests,
        'total_applied': total_applied,
        'total_clicked': total_clicked,
        'total_users_engaged': total_users_engaged,
        'popular_schemes': popular_schemes,
    }
    return render(request, 'admin_panel/schemes.html', context)


@admin_required
def admin_scheme_delete_interest(request, interest_id):
    from apps.government_schemes.models import SchemeInterest
    interest = get_object_or_404(SchemeInterest, id=interest_id)
    if request.method == 'POST':
        interest.delete()
        messages.success(request, "Interest record deleted.")
    return redirect('admin_schemes')




# ──────────────────────────────────────────────
# 1. DASHBOARD
# ──────────────────────────────────────────────
@admin_required
def dashboard_view(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = User.objects.count()
    total_tools = Tool.objects.count()
    total_pesticides = Pesticide.objects.count()
    total_products = total_tools + total_pesticides
    total_crops = Crop.objects.count()
    total_ai_queries = AIQueryHistory.objects.count()
    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_this_week = Order.objects.filter(created_at__gte=week_ago).count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    new_users_month = User.objects.filter(date_joined__gte=month_ago).count()
    user_growth = round((new_users_month / max(total_users - new_users_month, 1)) * 100, 1)

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_ai_queries = AIQueryHistory.objects.select_related('user').order_by('-timestamp')[:5]

    revenue_by_day = (
        Order.objects.filter(created_at__gte=month_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day').annotate(total=Sum('total_price')).order_by('day')
    )
    revenue_labels, revenue_values = [], []
    for i in range(30):
        day = (now - timedelta(days=29 - i)).date()
        revenue_labels.append(day.strftime('%b %d'))
        found = next((r['total'] for r in revenue_by_day if r['day'] == day), 0)
        revenue_values.append(float(found or 0))  # FIX: was missing this append — chart was always zero

    tools_by_cat = list(Tool.objects.values('category').annotate(count=Count('id')))
    cat_labels = [t['category'] for t in tools_by_cat] + ['Pesticides']
    cat_values = [t['count'] for t in tools_by_cat] + [total_pesticides]

    # Real revenue = delivered orders only
    delivered_revenue = Order.objects.filter(status='delivered').aggregate(t=Sum('total_price'))['t'] or 0
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_tools': total_tools,
        'total_pesticides': total_pesticides,
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_this_week': orders_this_week,
        'total_revenue': total_revenue,
        'delivered_revenue': delivered_revenue,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_crops': total_crops,
        'total_ai_queries': total_ai_queries,
        'user_growth': user_growth,
        'new_users_month': new_users_month,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'recent_ai_queries': recent_ai_queries,
        'revenue_chart_data': json.dumps({'labels': revenue_labels, 'values': revenue_values}),
        'category_chart_data': json.dumps({'labels': cat_labels, 'values': cat_values}),
        # Notification JSON for topbar bell
        'recent_orders_json': json.dumps([
            {'username': o.user.username, 'total': str(o.total_price), 'time': o.created_at.strftime('%b %d, %H:%M')}
            for o in recent_orders[:3]
        ]),
        'recent_users_json': json.dumps([
            {'username': u.username, 'time': u.date_joined.strftime('%b %d, %H:%M')}
            for u in recent_users[:2]
        ]),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ──────────────────────────────────────────────
# 2. ACTIVITY
# ──────────────────────────────────────────────
@admin_required
def admin_activity_view(request):
    activities = []
    for order in Order.objects.select_related('user').order_by('-created_at')[:20]:
        activities.append({
            'type': 'order', 'icon': 'shopping-bag',
            'text': f'<strong>{order.user.username}</strong> placed an order worth ₹{order.total_price}',
            'time': order.created_at, 'link': f'/myadmin/orders/{order.id}/',
        })
    for user in User.objects.order_by('-date_joined')[:20]:
        activities.append({
            'type': 'user', 'icon': 'user-plus',
            'text': f'<strong>{user.username}</strong> joined SmartFarm',
            'time': user.date_joined, 'link': f'/myadmin/users/{user.id}/',
        })
    for query in AIQueryHistory.objects.select_related('user').order_by('-timestamp')[:20]:
        activities.append({
            'type': 'product', 'icon': 'robot',
            'text': f'<strong>{query.user.username}</strong> asked AI: "{query.prompt[:60]}..."',
            'time': query.timestamp, 'link': None,
        })
    activities.sort(key=lambda x: x['time'], reverse=True)
    activities = activities[:50]
    return render(request, 'admin_panel/activity.html', {
        'activities': activities, 'total_activities': len(activities),
    })


# ──────────────────────────────────────────────
# 3. USER MANAGEMENT
# ──────────────────────────────────────────────
@admin_required
def admin_users_view(request):
    users = User.objects.annotate(order_count=Count('orders')).order_by('-date_joined')
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    elif status == 'staff':
        users = users.filter(is_staff=True)
    elif status == 'blocked':
        users = users.filter(profile__is_blocked=True)
    context = {
        'users': users, 'search': search, 'status': status,
        'total': users.count(),
        'active_count': User.objects.filter(is_active=True).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'blocked_count': UserProfile.objects.filter(is_blocked=True).count(),
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=user_obj).order_by('-created_at')
    ai_queries = AIQueryHistory.objects.filter(user=user_obj).order_by('-timestamp')[:10]
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    two_factor = AdminTwoFactor.objects.filter(user=user_obj).first()
    context = {
        'user_obj': user_obj, 'orders': orders,
        'ai_queries': ai_queries, 'total_spent': total_spent,
        'order_count': orders.count(),
        'two_factor': two_factor,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def admin_user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate yourself!")
        return redirect('admin_users')
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    messages.success(request, f"User {user_obj.username} {'activated' if user_obj.is_active else 'deactivated'}.")
    return redirect('admin_users')


@admin_required
def admin_user_delete(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot delete yourself!")
        return redirect('admin_users')
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"User '{username}' deleted.")
    return redirect('admin_users')


@admin_required
def admin_user_make_staff(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_staff = not user_obj.is_staff
    user_obj.save()
    messages.success(request, f"{user_obj.username} is now {'admin' if user_obj.is_staff else 'regular user'}.")
    return redirect('admin_users')


@admin_required
def admin_user_block(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot block yourself!")
        return redirect('admin_users')
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Violated terms of service')
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
        profile.is_blocked = True
        profile.blocked_reason = reason
        profile.save()
        user_obj.is_active = False
        user_obj.save()
        Notification.objects.create(
            user=user_obj,
            title='Account Blocked',
            message=f'Your account has been blocked. Reason: {reason}',
            notification_type='alert'
        )
        messages.success(request, f"User '{user_obj.username}' has been blocked.")
    return redirect('admin_users')


@admin_required
def admin_user_unblock(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
        profile.is_blocked = False
        profile.blocked_reason = None
        profile.save()
        user_obj.is_active = True
        user_obj.save()
        Notification.objects.create(
            user=user_obj,
            title='Account Unblocked',
            message='Your account has been unblocked. Welcome back!',
            notification_type='info'
        )
        messages.success(request, f"User '{user_obj.username}' has been unblocked.")
    return redirect('admin_users')


@admin_required
def admin_user_toggle_2fa(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    two_factor, _ = AdminTwoFactor.objects.get_or_create(user=user_obj)
    two_factor.is_enabled = not two_factor.is_enabled
    two_factor.save()
    status = "enabled" if two_factor.is_enabled else "disabled"
    messages.success(request, f"2FA {status} for {user_obj.username}.")
    return redirect('admin_user_detail', user_id=user_id)


# ──────────────────────────────────────────────
# 4. PRODUCT MANAGEMENT
# ──────────────────────────────────────────────
@admin_required
def admin_products_view(request):
    tools = Tool.objects.all()
    pesticides = Pesticide.objects.all()
    search = request.GET.get('q', '')
    product_type = request.GET.get('type', '')
    if search:
        tools = tools.filter(Q(name__icontains=search) | Q(description__icontains=search))
        pesticides = pesticides.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if product_type == 'tools':
        pesticides = Pesticide.objects.none()
    elif product_type == 'pesticides':
        tools = Tool.objects.none()
    context = {
        'tools': tools, 'pesticides': pesticides,
        'search': search, 'product_type': product_type,
        'total_tools': Tool.objects.count(),
        'total_pesticides': Pesticide.objects.count(),
        'categories': Tool.objects.values_list('category', flat=True).distinct(),
    }
    return render(request, 'admin_panel/products.html', context)


@admin_required
def admin_product_add_view(request):
    if request.method == 'POST':
        product_type = request.POST.get('product_type')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        if product_type == 'tool':
            Tool.objects.create(name=name, description=description, price=price,
                                category=request.POST.get('category', 'General'), image=image)
            messages.success(request, f"Tool '{name}' added!")
        elif product_type == 'pesticide':
            Pesticide.objects.create(name=name, description=description, price=price,
                                     category=request.POST.get('category', 'General'), image=image)
            messages.success(request, f"Pesticide '{name}' added!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_add.html')


@admin_required
def admin_tool_edit_view(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        tool.name = request.POST.get('name')
        tool.description = request.POST.get('description')
        tool.price = request.POST.get('price')
        tool.category = request.POST.get('category', 'General')
        if request.FILES.get('image'):
            tool.image = request.FILES.get('image')
        tool.save()
        messages.success(request, f"Tool '{tool.name}' updated!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_edit.html', {'product': tool, 'product_type': 'tool'})


@admin_required
def admin_pesticide_edit_view(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    if request.method == 'POST':
        pesticide.name = request.POST.get('name')
        pesticide.description = request.POST.get('description')
        pesticide.price = request.POST.get('price')
        pesticide.category = request.POST.get('category', 'General')
        if request.FILES.get('image'):
            pesticide.image = request.FILES.get('image')
        pesticide.save()
        messages.success(request, f"Pesticide '{pesticide.name}' updated!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_edit.html', {'product': pesticide, 'product_type': 'pesticide'})


@admin_required
def admin_tool_delete_view(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        name = tool.name
        tool.delete()
        messages.success(request, f"Tool '{name}' deleted!")
    return redirect('admin_products')


@admin_required
def admin_pesticide_delete_view(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    if request.method == 'POST':
        name = pesticide.name
        pesticide.delete()
        messages.success(request, f"Pesticide '{name}' deleted!")
    return redirect('admin_products')


# ──────────────────────────────────────────────
# 5. ORDER MANAGEMENT
# ──────────────────────────────────────────────
@admin_required
def admin_orders_view(request):
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if search:
        orders = orders.filter(Q(user__username__icontains=search) | Q(id__icontains=search))
    if status_filter:
        orders = orders.filter(status=status_filter)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    context = {
        'orders': orders, 'search': search,
        'status_filter': status_filter,
        'date_from': date_from, 'date_to': date_to,
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total_price'))['total'] or 0,
    }
    return render(request, 'admin_panel/orders.html', context)


@admin_required
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    for item in items:
        if item.item_type == 'tool':
            item.product = Tool.objects.filter(id=item.item_id).first()
        elif item.item_type == 'pesticide':
            item.product = Pesticide.objects.filter(id=item.item_id).first()
    return render(request, 'admin_panel/order_detail.html', {'order': order, 'items': items})


@admin_required
def admin_order_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment = request.POST.get('payment_status')
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']

        if new_status in valid_statuses:
            old_status = order.status
            order.status = new_status

            # Update payment status if provided
            if new_payment in ['pending', 'paid', 'failed', 'refunded']:
                order.payment_status = new_payment

            # If delivered → mark payment as paid for COD automatically
            if new_status == 'delivered' and order.payment_method == 'cod':
                order.payment_status = 'paid'

            order.save()

            # Send notification to user when status changes
            status_messages = {
                'processing': ('Order Processing', f'Your order #{order.id} is being prepared for shipment.', 'info'),
                'shipped':    ('Order Shipped!', f'Your order #{order.id} is on its way! Expected delivery in 2-3 days.', 'info'),
                'delivered':  ('Order Delivered!', f'Your order #{order.id} has been delivered successfully. Thank you for shopping with SmartFarming!', 'info'),
                'cancelled':  ('Order Cancelled', f'Your order #{order.id} has been cancelled. If you paid online, a refund will be initiated.', 'alert'),
                'returned':   ('Order Returned', f'Your order #{order.id} return has been processed.', 'info'),
            }
            if new_status in status_messages and old_status != new_status:
                title, msg, notif_type = status_messages[new_status]
                Notification.objects.create(
                    user=order.user,
                    title=title,
                    message=msg,
                    notification_type=notif_type
                )

            messages.success(request, f"Order #{order_id} updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('admin_order_detail', order_id=order_id)


@admin_required
def admin_order_delete_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, f"Order #{order_id} deleted!")
    return redirect('admin_orders')


# ──────────────────────────────────────────────
# 5b. ORDER ANALYTICS
# ──────────────────────────────────────────────
@admin_required
def admin_order_analytics_view(request):
    from django.db.models import Count
    from datetime import timedelta

    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    all_orders = Order.objects.all()

    # Status breakdown
    status_list = [
        ('pending','Pending','gold'),
        ('processing','Processing','blue'),
        ('shipped','Shipped','orange'),
        ('delivered','Delivered','green'),
        ('cancelled','Cancelled','red'),
        ('returned','Returned','red'),
    ]
    status_data = []
    for status, label, color in status_list:
        count = all_orders.filter(status=status).count()
        revenue = all_orders.filter(status=status).aggregate(t=Sum('total_price'))['t'] or 0
        pct = round((count / max(all_orders.count(), 1)) * 100, 1)
        status_data.append({'status': status, 'label': label, 'color': color,
                            'count': count, 'revenue': revenue, 'pct': pct})

    total_orders = all_orders.count()

    # REAL revenue = delivered orders only
    delivered_orders = all_orders.filter(status='delivered')
    real_revenue = delivered_orders.aggregate(t=Sum('total_price'))['t'] or 0
    cod_revenue = all_orders.filter(status='delivered', payment_method='cod').aggregate(t=Sum('total_price'))['t'] or 0
    online_revenue = all_orders.filter(status='delivered').exclude(payment_method='cod').aggregate(t=Sum('total_price'))['t'] or 0

    # Payment method breakdown
    payment_breakdown = all_orders.values('payment_method').annotate(
        count=Count('id'), total=Sum('total_price')
    ).order_by('-count')

    # Time stats
    orders_today  = all_orders.filter(created_at__date=today).count()
    orders_week   = all_orders.filter(created_at__gte=week_ago).count()
    orders_month  = all_orders.filter(created_at__gte=month_ago).count()
    rev_today     = all_orders.filter(created_at__date=today, status='delivered').aggregate(t=Sum('total_price'))['t'] or 0
    rev_week      = all_orders.filter(created_at__gte=week_ago, status='delivered').aggregate(t=Sum('total_price'))['t'] or 0
    rev_month     = all_orders.filter(created_at__gte=month_ago, status='delivered').aggregate(t=Sum('total_price'))['t'] or 0

    # Recent 25 orders
    recent_orders = all_orders.select_related('user','shipping_address').order_by('-created_at')[:25]

    context = {
        'status_data': status_data,
        'total_orders': total_orders,
        'real_revenue': real_revenue,
        'cod_revenue': cod_revenue,
        'online_revenue': online_revenue,
        'payment_breakdown': payment_breakdown,
        'orders_today': orders_today,
        'orders_week': orders_week,
        'orders_month': orders_month,
        'rev_today': rev_today,
        'rev_week': rev_week,
        'rev_month': rev_month,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_panel/order_analytics.html', context)


# ──────────────────────────────────────────────
# 6. CROP MANAGEMENT
# ──────────────────────────────────────────────
@admin_required
def admin_crops_view(request):
    crops = Crop.objects.all().order_by('country', 'crop')
    search = request.GET.get('q', '')
    country_filter = request.GET.get('country', '')
    season_filter = request.GET.get('season', '')
    if search:
        crops = crops.filter(Q(crop__icontains=search) | Q(country__icontains=search))
    if country_filter:
        crops = crops.filter(country=country_filter)
    if season_filter:
        crops = crops.filter(season__icontains=season_filter)
    paginator = Paginator(crops, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    context = {
        'crops': crops, 'page_obj': page_obj,
        'search': search, 'country_filter': country_filter, 'season_filter': season_filter,
        'countries': Crop.objects.values_list('country', flat=True).distinct().order_by('country'),
        'seasons': Crop.objects.values_list('season', flat=True).distinct(),
        'total': Crop.objects.count(),
    }
    return render(request, 'admin_panel/crops.html', context)


@admin_required
def admin_crop_add_view(request):
    if request.method == 'POST':
        Crop.objects.create(
            country=request.POST.get('country'), crop=request.POST.get('crop'),
            soil_type=request.POST.get('soil_type'), temperature=request.POST.get('temperature'),
            season=request.POST.get('season'), category=request.POST.get('category'),
        )
        messages.success(request, "Crop added!")
        return redirect('admin_crops')
    return render(request, 'admin_panel/crop_add.html')


@admin_required
def admin_crop_edit_view(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    if request.method == 'POST':
        crop.country = request.POST.get('country')
        crop.crop = request.POST.get('crop')
        crop.soil_type = request.POST.get('soil_type')
        crop.temperature = request.POST.get('temperature')
        crop.season = request.POST.get('season')
        crop.category = request.POST.get('category')
        crop.save()
        messages.success(request, f"Crop '{crop.crop}' updated!")
        return redirect('admin_crops')
    return render(request, 'admin_panel/crop_edit.html', {'crop': crop})


@admin_required
def admin_crop_delete_view(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    if request.method == 'POST':
        name = crop.crop
        crop.delete()
        messages.success(request, f"Crop '{name}' deleted!")
    return redirect('admin_crops')


# ──────────────────────────────────────────────
# 7. AI HISTORY
# ──────────────────────────────────────────────
@admin_required
def admin_ai_history_view(request):
    queries = AIQueryHistory.objects.select_related('user').order_by('-timestamp')
    search = request.GET.get('q', '')
    user_filter = request.GET.get('user', '')
    if search:
        queries = queries.filter(Q(prompt__icontains=search) | Q(response__icontains=search))
    if user_filter:
        queries = queries.filter(user__username__icontains=user_filter)
    context = {
        'queries': queries, 'search': search, 'user_filter': user_filter,
        'total': AIQueryHistory.objects.count(),
        'total_users_queried': AIQueryHistory.objects.values('user').distinct().count(),
    }
    return render(request, 'admin_panel/ai_history.html', context)


@admin_required
def admin_ai_delete_view(request, query_id):
    query = get_object_or_404(AIQueryHistory, id=query_id)
    if request.method == 'POST':
        query.delete()
        messages.success(request, "AI query deleted.")
    return redirect('admin_ai_history')


# ──────────────────────────────────────────────
# 8. ANNOUNCEMENTS
# ──────────────────────────────────────────────
@admin_required
def admin_announcements_view(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/announcements.html', {'announcements': announcements})


@admin_required
def admin_announcement_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        send_email = request.POST.get('send_email') == 'on'

        announcement = Announcement.objects.create(
            title=title, message=message,
            created_by=request.user, send_email=send_email
        )

        users = User.objects.filter(is_active=True)
        Notification.objects.bulk_create([
            Notification(
                user=user,
                title=f'📢 {title}',
                message=message,
                notification_type='announcement'
            ) for user in users
        ])

        if send_email:
            user_emails = list(users.exclude(email='').values_list('email', flat=True))
            if user_emails:
                try:
                    send_mail(
                        f'SmartFarming: {title}',
                        f'{message}\n\n— SmartFarming Admin Team',
                        settings.DEFAULT_FROM_EMAIL,
                        user_emails,
                        fail_silently=True,
                    )
                except Exception:
                    pass

        messages.success(request, f'Announcement sent to {users.count()} users!')
        return redirect('admin_announcements')

    return render(request, 'admin_panel/announcement_create.html')


@admin_required
def admin_announcement_delete(request, ann_id):
    announcement = get_object_or_404(Announcement, id=ann_id)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "Announcement deleted.")
    return redirect('admin_announcements')


# ──────────────────────────────────────────────
# 9. REPORTS
# ──────────────────────────────────────────────
@admin_required
def admin_reports_view(request):
    top_products = (
        OrderItem.objects.values('name')
        .annotate(total_sold=Sum('quantity'), revenue=Sum('price'))
        .order_by('-total_sold')[:10]
    )
    top_customers = (
        Order.objects.values('user__username')
        .annotate(order_count=Count('id'), total_spent=Sum('total_price'))
        .order_by('-total_spent')[:10]
    )
    context = {
        'top_products': top_products, 'top_customers': top_customers,
        'total_revenue': Order.objects.aggregate(t=Sum('total_price'))['t'] or 0,
        'total_orders': Order.objects.count(),
        'total_users': User.objects.count(),
        'total_crops': Crop.objects.count(),
    }
    return render(request, 'admin_panel/reports.html', context)


# ──────────────────────────────────────────────
# 10. SETTINGS
# ──────────────────────────────────────────────
@admin_required
def admin_settings_view(request):
    return render(request, 'admin_panel/settings.html')