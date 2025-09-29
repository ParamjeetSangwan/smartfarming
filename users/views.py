# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import UserProfile




def create_profile_if_missing(user):
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user, name=user.username)

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        if not email or '@' not in email:
            messages.error(request, 'Enter a valid email.')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')

    return render(request, 'users/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')

@login_required
def dashboard_view(request):
    create_profile_if_missing(request.user)
    name = request.user.profile.name
    return render(request, 'dashboard.html', {'name': name})

@login_required
def profile_view(request):
    create_profile_if_missing(request.user)
    profile = request.user.profile

    if request.method == 'POST':
        profile.name = request.POST['name']
        profile.location = request.POST['location']
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard')

    return render(request, 'users/profile.html', {'user': request.user, 'name': profile.name, 'location': profile.location})


@login_required
def orders_view(request):
    return render(request, 'orders.html')

@login_required
def ai_recommendations_view(request):
    return render(request, 'ai_recommendations.html')


@login_required
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated. You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid.")
        return redirect('login')