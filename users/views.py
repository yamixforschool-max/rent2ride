from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile
from .forms import SignUpForm, ProfileUpdateForm
from vehicles.models import Referral, PromoCode
import re


def signup_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Get additional fields
            phone_number = form.cleaned_data.get('phone_number')
            is_owner = form.cleaned_data.get('is_owner', False)
            
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone_number = phone_number
            profile.is_owner = is_owner
            profile.save()
            
            # Handle referral code
            referral_code = request.session.get('referral_code')
            referrer_id = request.session.get('referrer_id')
            if referral_code and referrer_id:
                try:
                    from vehicles.models import ReferralCode, Referral
                    referrer = User.objects.get(id=referrer_id)
                    # Create referral record
                    Referral.objects.create(
                        referrer=referrer,
                        referred_user=user,
                        referral_code=referral_code.upper()
                    )
                    # Create welcome promo code for new user (10% off first booking)
                    welcome_promo = PromoCode.objects.create(
                        code=f"WELCOME{user.id}",
                        discount_type='percentage',
                        discount_value=10.00,
                        max_uses=1,
                        valid_from=timezone.now(),
                        valid_until=timezone.now() + timedelta(days=30),
                        is_active=True
                    )
                    messages.success(request, f'Welcome! You received a 10% discount code: {welcome_promo.code}')
                    del request.session['referral_code']
                    del request.session['referrer_id']
                except (User.DoesNotExist, Exception):
                    pass
            
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


@login_required
def profile_view(request):
    """User profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Update user fields
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.email = form.cleaned_data.get('email', '')
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone_number': profile.phone_number,
            'profile_picture': profile.profile_picture,
        })
    
    context = {
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile.html', context)
