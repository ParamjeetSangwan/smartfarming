# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from httpx import request
from .models import UserProfile, OTPVerification, Notification, AdminTwoFactor


def create_profile_if_missing(user):
    if not hasattr(user, 'profile'):
        UserProfile.objects.get_or_create(user=user, defaults={'name': user.username})


def send_otp_email(user, purpose):
    OTPVerification.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
    otp = OTPVerification.generate_otp()
    OTPVerification.objects.create(user=user, otp=otp, purpose=purpose)

    subject_map = {
        'register': 'SmartFarming - Verify Your Email',
        '2fa': 'SmartFarming - Admin Login OTP',
    }
    message = f"""
Hello {user.username},

Your verification code is: {otp}

This code expires in 10 minutes.

If you did not request this, please ignore this email.

— SmartFarming Team
    """
    send_mail(
        subject_map.get(purpose, 'SmartFarming OTP'),
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return otp


# ── REGISTRATION ──
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        if not email or '@' not in email:
            messages.error(request, 'Enter a valid email.')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')
        if confirm_password and password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('register')

        # FIX: Removed manual UserProfile.objects.create() here.
        # signals.py handles UserProfile creation automatically via post_save.
        user = User.objects.create_user(
            username=username, email=email, password=password,
            is_active=False
        )

        try:
            send_otp_email(user, 'register')
            request.session['otp_user_id'] = user.id
            messages.success(request, f'OTP sent to {email}. Please verify your email.')
            return redirect('verify_otp')
        except Exception:
            user.is_active = True
            user.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')

    return render(request, 'users/register.html')


def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        otp_obj = OTPVerification.objects.filter(
            user=user, purpose='register', is_used=False
        ).last()

        if otp_obj and otp_obj.is_valid() and otp_obj.otp == entered_otp:
            otp_obj.is_used = True
            otp_obj.save()
            user.is_active = True
            user.save()
            del request.session['otp_user_id']
            messages.success(request, 'Email verified! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid or expired OTP. Try again.')

    return render(request, 'users/verify_otp.html', {'email': user.email})


def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')
    try:
        user = User.objects.get(id=user_id)
        send_otp_email(user, 'register')
        messages.success(request, 'New OTP sent to your email!')
    except Exception:
        messages.error(request, 'Failed to send OTP. Try again.')
    return redirect('verify_otp')


# ── LOGIN ──
from django.core.cache import cache
from django.contrib.auth.models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_staff else 'dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'users/login.html')

        # 🔒 RATE LIMITING
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f"login_attempts_{ip}"
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            messages.error(request, "Too many attempts. Try again after 5 minutes.")
            return render(request, 'users/login.html')

        # 🔄 EMAIL LOGIN SUPPORT
        user_obj = User.objects.filter(email=username).first()
        if user_obj:
            username = user_obj.username

        user = authenticate(request, username=username, password=password)

        if user is not None:
            cache.delete(cache_key)

            # 🚫 BLOCKED USER
            if hasattr(user, 'profile') and user.profile.is_blocked:
                messages.error(request, "Your account is blocked.")
                return render(request, 'users/login.html')

            # 🔐 ADMIN 2FA (SAFE)
            if user.is_staff:
                two_factor, _ = AdminTwoFactor.objects.get_or_create(user=user)

                if two_factor.is_enabled:
                    try:
                        send_otp_email(user, '2fa')
                        request.session['2fa_user_id'] = user.id
                        request.session.set_expiry(300)
                        return redirect('verify_2fa')
                    except Exception:
                        messages.error(request, "2FA failed. Try again.")
                        return render(request, 'users/login.html')

            # ✅ LOGIN
            login(request, user)

            # 🧠 REMEMBER ME
            if request.POST.get('remember_me'):
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return redirect('admin_dashboard' if user.is_staff else 'dashboard')

        else:
            cache.set(cache_key, attempts + 1, timeout=300)
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'users/login.html')



def verify_2fa_view(request):
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()

        otp_obj = OTPVerification.objects.filter(
            user=user, purpose='2fa', is_used=False
        ).last()

        if not otp_obj:
            messages.error(request, "No OTP found.")
            return redirect('login')

        if hasattr(otp_obj, 'attempts') and otp_obj.attempts >= 5:
            messages.error(request, "Too many wrong attempts.")
            return redirect('login')

        if otp_obj.is_valid() and otp_obj.otp == entered_otp:
            otp_obj.is_used = True
            otp_obj.save()
            del request.session['2fa_user_id']
            login(request, user)
            return redirect('admin_dashboard')
        else:
            if hasattr(otp_obj, 'attempts'):
                otp_obj.attempts += 1
                otp_obj.save()
            messages.error(request, "Invalid or expired OTP.")

    return render(request, 'users/verify_2fa.html', {'email': user.email})


def logout_view(request):
    # Clear all pending messages so they don't show on login page
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    for _ in storage:
        pass  # iterating clears them
    logout(request)
    return redirect('login')


# ── DASHBOARD ──
@login_required
def dashboard_view(request):
    from apps.orders.models import Order
    from apps.ai_recommendations.models import AIQueryHistory
    from apps.users.models import Announcement
    create_profile_if_missing(request.user)
    name = request.user.profile.name
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    notifications = Notification.objects.filter(user=request.user)[:8]
    total_orders = Order.objects.filter(user=request.user).count()
    delivered_orders = Order.objects.filter(user=request.user, status='delivered').count()
    pending_orders = Order.objects.filter(user=request.user, status='pending').count()
    ai_queries = AIQueryHistory.objects.filter(user=request.user).count()
    latest_announcement = Announcement.objects.first()
    return render(request, 'dashboard.html', {
        'name': name,
        'unread_count': unread_count,
        'notifications': notifications,
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'pending_orders': pending_orders,
        'ai_queries': ai_queries,
        'latest_announcement': latest_announcement,
    })


# ── PROFILE ──
@login_required
def profile_view(request):
    create_profile_if_missing(request.user)
    profile = request.user.profile

    if request.method == 'POST':
        profile.name = request.POST.get('name', profile.name)
        profile.location = request.POST.get('location', '')
        if request.FILES.get('avatar'):
            if profile.avatar:
                import os as _os
                if _os.path.isfile(profile.avatar.path):
                    _os.remove(profile.avatar.path)
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile,
        'name': profile.name,
        'location': profile.location or ''
    })


# ── NOTIFICATIONS ──
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'total': notifications.count(),
    })


@login_required
def mark_notification_read(request, notif_id):
    try:
        notif = Notification.objects.get(id=notif_id, user=request.user)
        notif.is_read = True
        notif.save()
    except Notification.DoesNotExist:
        pass
    return redirect('notifications')


# ── ACCOUNT ACTIVATION ──
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid.")
        return redirect('login')


# ── EXTRA VIEWS ──
@login_required
def orders_view(request):
    """Redirect to the full marketplace orders page"""
    return redirect('orders:my_orders')


@login_required
def ai_recommendations_view(request):
    """Redirect to AI recommendations page"""
    return redirect('ai_recommendations:get_recommendations')