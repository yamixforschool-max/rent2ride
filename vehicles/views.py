from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import requests
import json
from django.conf import settings
from .models import (
    Vehicle, Booking, Payment, PromoCode, SecurityDeposit, Rating, IdentityVerification, 
    Commission, Refund, DamageReport, DamagePhoto, Message, RentalAgreement, DriversLicense,
    Blacklist, VehicleUtilization, PeakDemand, ReturnReminder, VehicleComparison,
    AvailabilityLock, AuditLog, PayoutRequest, Invoice, Referral, LoyaltyPoints, LoyaltyTransaction
)
from .forms import (
    VehicleForm, BookingForm, RefundRequestForm, DamageReportForm, MessageForm,
    DriversLicenseForm, BlacklistForm, PayoutRequestForm, RentalAgreementSignatureForm, ReferralForm
)
from users.models import UserProfile


def home_view(request):
    """Landing page with featured vehicles"""
    featured_vehicles = Vehicle.objects.filter(status='available')[:6]
    context = {
        'featured_vehicles': featured_vehicles,
    }
    return render(request, 'home.html', context)


def vehicle_list_view(request):
    """Display all available vehicles with enhanced search filters"""
    vehicles = Vehicle.objects.filter(status='available')
    
    # Enhanced search filters
    search_query = request.GET.get('search', '')
    location = request.GET.get('location', '')
    vehicle_type = request.GET.get('vehicle_type', '')
    fuel_type = request.GET.get('fuel_type', '')
    transmission_type = request.GET.get('transmission_type', '')
    min_seats = request.GET.get('min_seats', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    if search_query:
        vehicles = vehicles.filter(
            Q(model__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if location:
        vehicles = vehicles.filter(location__icontains=location)
    
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    
    if fuel_type:
        vehicles = vehicles.filter(fuel_type=fuel_type)
    
    if transmission_type:
        vehicles = vehicles.filter(transmission_type=transmission_type)
    
    if min_seats:
        try:
            vehicles = vehicles.filter(seats__gte=int(min_seats))
        except:
            pass
    
    if min_price:
        try:
            vehicles = vehicles.filter(price_per_day__gte=Decimal(min_price))
        except:
            pass
    
    if max_price:
        try:
            vehicles = vehicles.filter(price_per_day__lte=Decimal(max_price))
        except:
            pass
    
    context = {
        'vehicles': vehicles,
        'vehicle_types': Vehicle.VEHICLE_TYPES,
        'fuel_types': Vehicle.FUEL_TYPES,
        'transmission_types': Vehicle.TRANSMISSION_TYPES,
        'current_filters': {
            'search': search_query,
            'location': location,
            'vehicle_type': vehicle_type,
            'fuel_type': fuel_type,
            'transmission_type': transmission_type,
            'min_seats': min_seats,
            'min_price': min_price,
            'max_price': max_price,
        }
    }
    return render(request, 'vehicle_list.html', context)


def vehicle_detail_view(request, vehicle_id):
    """Display vehicle details"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # Get existing bookings (confirmed or pending)
    existing_bookings = Booking.objects.filter(
        vehicle=vehicle,
        status__in=['pending', 'confirmed']
    ).order_by('start_date')
    
    # Get booked date ranges
    booked_dates = []
    for booking in existing_bookings:
        booked_dates.append({
            'start': booking.start_date,
            'end': booking.end_date,
            'status': booking.status,
            'user': booking.user.username
        })
    
    # Check if vehicle is currently booked (for today)
    today = timezone.now()
    is_currently_booked = False
    current_booking = None
    
    for booking in existing_bookings:
        if booking.start_date <= today <= booking.end_date:
            is_currently_booked = True
            current_booking = booking
            break
    
    # Calculate actual available date ranges based on bookings
    actual_available_from = None
    actual_available_to = None
    
    today_date = today.date()
    vehicle_from = vehicle.available_from.date()
    vehicle_to = vehicle.available_to.date()
    
    # Find the next available period
    if existing_bookings.exists():
        # Find gaps between bookings
        gaps = []
        
        # Start from today or vehicle available_from, whichever is later
        current_date = max(today_date, vehicle_from)
        
        # Sort bookings by start date
        sorted_bookings = list(existing_bookings.order_by('start_date'))
        
        # Check gap before first booking
        if current_date < sorted_bookings[0].start_date.date():
            gap_end = min(sorted_bookings[0].start_date.date() - timedelta(days=1), vehicle_to)
            if current_date <= gap_end:
                gaps.append({
                    'start': current_date,
                    'end': gap_end
                })
        
        # Check gaps between bookings
        for i in range(len(sorted_bookings) - 1):
            current_booking_end = sorted_bookings[i].end_date.date() + timedelta(days=1)
            next_booking_start = sorted_bookings[i + 1].start_date.date() - timedelta(days=1)
            
            if current_booking_end <= next_booking_start and current_booking_end <= vehicle_to:
                gap_start = max(current_booking_end, vehicle_from)
                gap_end = min(next_booking_start, vehicle_to)
                if gap_start <= gap_end:
                    gaps.append({
                        'start': gap_start,
                        'end': gap_end
                    })
        
        # Check gap after last booking
        last_booking_end = sorted_bookings[-1].end_date.date() + timedelta(days=1)
        if last_booking_end <= vehicle_to:
            gap_start = max(last_booking_end, current_date, vehicle_from)
            if gap_start <= vehicle_to:
                gaps.append({
                    'start': gap_start,
                    'end': vehicle_to
                })
        
        # Use the first available gap
        if gaps:
            actual_available_from = gaps[0]['start']
            actual_available_to = gaps[0]['end']
    else:
        # No bookings, use vehicle's original availability (from today onwards)
        actual_available_from = max(today_date, vehicle_from)
        actual_available_to = vehicle_to
    
    # Get next available date (if currently booked)
    next_available_date = None
    if is_currently_booked and existing_bookings.exists():
        # Find the next available slot after current bookings
        last_booking = existing_bookings.order_by('-end_date').first()
        if last_booking:
            next_available_date = last_booking.end_date + timedelta(days=1)
    
    # Check if vehicle is saved by current user
    is_saved = False
    if request.user.is_authenticated:
        from .models import SavedVehicle
        is_saved = SavedVehicle.objects.filter(user=request.user, vehicle=vehicle).exists()
    
    context = {
        'vehicle': vehicle,
        'booked_dates': booked_dates,
        'is_currently_booked': is_currently_booked,
        'current_booking': current_booking,
        'next_available_date': next_available_date,
        'existing_bookings': existing_bookings,
        'actual_available_from': actual_available_from,
        'actual_available_to': actual_available_to,
        'today': today,
        'is_saved': is_saved,
    }
    return render(request, 'vehicle_detail.html', context)


@login_required
def dashboard_view(request):
    """User dashboard - different views for renters and owners"""
    from users.models import UserProfile
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if profile.is_owner:
        # Owner dashboard
        vehicles = Vehicle.objects.filter(owner=user)
        bookings = Booking.objects.filter(vehicle__owner=user).order_by('-created_at')[:10]
    else:
        # Renter dashboard
        vehicles = None
        bookings = Booking.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'profile': profile,
        'vehicles': vehicles,
        'bookings': bookings,
    }
    return render(request, 'dashboard.html', context)


@login_required
def add_vehicle_view(request):
    """Allow vehicle owners and admins to add new vehicles"""
    from django.contrib.auth.models import User
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    is_admin = profile.is_admin
    
    # Allow owners or admins
    if not profile.is_owner and not is_admin:
        messages.error(request, 'Only vehicle owners or admins can add vehicles.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save(commit=False)
            
            # If admin, allow selecting owner; otherwise use current user
            if is_admin:
                owner_id = request.POST.get('owner')
                if owner_id:
                    try:
                        owner = User.objects.get(id=owner_id)
                        vehicle.owner = owner
                    except User.DoesNotExist:
                        messages.error(request, 'Selected owner not found.')
                        return render(request, 'add_vehicle.html', {
                            'form': form,
                            'is_admin': is_admin,
                            'users': User.objects.filter(profile__is_owner=True) if is_admin else None
                        })
                else:
                    vehicle.owner = request.user
                # Admin-added vehicles are auto-approved
                vehicle.status = 'available'
            else:
                vehicle.owner = request.user
                vehicle.status = 'pending_approval'
            
            vehicle.save()
            
            if is_admin:
                messages.success(request, f'Vehicle added successfully and auto-approved for {vehicle.owner.get_full_name() or vehicle.owner.username}!')
                return redirect('admin_vehicles')
            else:
                messages.success(request, 'Vehicle added successfully! Waiting for admin approval.')
                return redirect('dashboard')
    else:
        form = VehicleForm()
    
    # Get list of owners for admin dropdown
    users = None
    if is_admin:
        users = User.objects.filter(profile__is_owner=True).select_related('profile')
    
    return render(request, 'add_vehicle.html', {
        'form': form,
        'is_admin': is_admin,
        'users': users
    })


@login_required
def booking_view(request, vehicle_id):
    """Create a booking for a vehicle"""
    from datetime import timedelta
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, status='available')
    
    # Get existing bookings to show unavailable dates
    existing_bookings = Booking.objects.filter(
        vehicle=vehicle,
        status__in=['pending', 'confirmed']
    ).order_by('start_date')
    
    # Prepare booked dates for JavaScript (as JSON string)
    booked_dates_js = []
    for booking in existing_bookings:
        booked_dates_js.append({
            'start': booking.start_date.strftime('%Y-%m-%d'),
            'end': booking.end_date.strftime('%Y-%m-%d'),
        })
    booked_dates_json = json.dumps(booked_dates_js)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        promo_code_str = request.POST.get('promo_code', '').strip()
        payment_type = request.POST.get('payment_type', 'full')
        include_insurance = request.POST.get('include_insurance') == 'on'
        
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Normalise to aware datetimes so comparisons don't raise TypeError
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)

            # Validate dates
            if start_date >= end_date:
                messages.error(request, 'End date must be after start date.')
                return render(request, 'booking.html', {
                    'vehicle': vehicle,
                    'form': form,
                    'booked_dates_json': booked_dates_json,
                    'existing_bookings': existing_bookings
                })

            if start_date < timezone.now():
                messages.error(request, 'Start date cannot be in the past.')
                return render(request, 'booking.html', {
                    'vehicle': vehicle,
                    'form': form,
                    'booked_dates_json': booked_dates_json,
                    'existing_bookings': existing_bookings
                })
            
            # Check if user is blacklisted
            is_blacklisted, blacklist = check_user_blacklist(request.user)
            if is_blacklisted:
                messages.error(request, f'Your account has been blacklisted. Reason: {blacklist.reason}')
                return redirect('dashboard')
            
            # Check driver's license verification
            try:
                license_obj = DriversLicense.objects.get(user=request.user)
                if license_obj.status != 'verified':
                    messages.error(request, 'Your driver\'s license must be verified before making a booking.')
                    return redirect('upload_drivers_license')
                if license_obj.is_expired():
                    messages.error(request, 'Your driver\'s license has expired. Please upload a new one.')
                    return redirect('upload_drivers_license')
            except DriversLicense.DoesNotExist:
                messages.error(request, 'Please upload your driver\'s license before making a booking.')
                return redirect('upload_drivers_license')
            
            # Check identity verification for first-time renters
            if not request.user.profile.is_verified:
                messages.error(request, 'Please verify your identity before making a booking.')
                return redirect('identity_verification')
            
            # Fraud prevention - check daily booking limit
            from users.models import UserProfile
            profile = request.user.profile
            today = timezone.now().date()
            if profile.last_booking_date != today:
                profile.daily_booking_count = 0
                profile.last_booking_date = today
                profile.save()
            
            MAX_DAILY_BOOKINGS = 5
            if profile.daily_booking_count >= MAX_DAILY_BOOKINGS:
                messages.error(request, 'You have reached the daily booking limit. Please try again tomorrow.')
                return redirect('vehicle_list')
            
            # Enhanced conflict checking
            conflicting_bookings = Booking.objects.filter(
                vehicle=vehicle,
                status__in=['pending', 'confirmed'],
                start_date__lt=end_date,
                end_date__gt=start_date
            )
            
            if conflicting_bookings.exists():
                conflict = conflicting_bookings.first()
                messages.error(
                    request, 
                    f'This vehicle is already booked from {conflict.start_date.strftime("%B %d, %Y")} to {conflict.end_date.strftime("%B %d, %Y")}. Please select different dates.'
                )
                return render(request, 'booking.html', {
                    'vehicle': vehicle, 
                    'form': form,
                    'booked_dates_json': booked_dates_json,
                    'existing_bookings': existing_bookings
                })
            
            # Calculate pricing
            days = (end_date - start_date).days + 1
            rental_fee = vehicle.price_per_day * days
            
            # Calculate insurance
            insurance_amount = 0
            if include_insurance:
                insurance_amount = Decimal('500.00') * days
            
            # Apply promo code
            promo_code = None
            discount_amount = Decimal('0.00')
            if promo_code_str:
                try:
                    promo = PromoCode.objects.get(code=promo_code_str.upper())
                    if promo.is_valid():
                        if promo.discount_type == 'percentage':
                            discount_amount = (rental_fee + insurance_amount) * (promo.discount_value / 100)
                        else:
                            discount_amount = promo.discount_value
                        promo_code = promo
                        promo.used_count += 1
                        promo.save()
                        messages.success(request, f'Promo code "{promo_code_str}" applied!')
                    else:
                        messages.error(request, 'This promo code is not valid or has expired.')
                except PromoCode.DoesNotExist:
                    messages.error(request, 'Invalid promo code.')
            
            # Calculate total
            total_price = rental_fee + insurance_amount - discount_amount
            
            # If deposit only, calculate deposit (30% of total)
            deposit_amount = Decimal('0.00')
            if payment_type == 'deposit':
                deposit_amount = total_price * Decimal('0.30')
                total_price = deposit_amount  # Only charge deposit now
            
            # Set expiration (15 minutes from now)
            expires_at = timezone.now() + timedelta(minutes=15)
            
            # Lock vehicle availability during checkout
            lock_expires = timezone.now() + timedelta(minutes=15)
            availability_lock = AvailabilityLock.objects.create(
                vehicle=vehicle,
                locked_by=request.user,
                expires_at=lock_expires
            )
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                vehicle=vehicle,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price,
                deposit_amount=deposit_amount,
                insurance_amount=insurance_amount,
                discount_amount=discount_amount,
                promo_code=promo_code,
                payment_type=payment_type,
                expires_at=expires_at,
                status='pending',
                payment_status='pending',
                is_locked=True,
                locked_at=timezone.now(),
                license_verified=True  # Already checked above
            )
            
            # Update availability lock with booking
            availability_lock.booking = booking
            availability_lock.save()
            
            # Track peak demand
            PeakDemand.objects.update_or_create(
                date=start_date.date(),
                location=vehicle.location,
                vehicle_type=vehicle.vehicle_type,
                defaults={'demand_count': 1}
            )
            
            # Award loyalty points (if applicable)
            points, created = LoyaltyPoints.objects.get_or_create(user=request.user)
            points_earned = int(total_price / 100)  # 1 point per ₱100
            if points_earned > 0:
                points.total_points += points_earned
                points.save()
                
                LoyaltyTransaction.objects.create(
                    user=request.user,
                    transaction_type='earned',
                    points=points_earned,
                    description=f'Points earned from booking #{booking.id}',
                    booking=booking,
                    expires_at=timezone.now() + timedelta(days=365)  # Points expire in 1 year
                )
            
            # Update daily booking count
            profile.daily_booking_count += 1
            profile.save()
            
            # Create security deposit if full payment
            if payment_type == 'full':
                from .models import SecurityDeposit
                deposit_amount = total_price * Decimal('0.20')  # 20% security deposit
                SecurityDeposit.objects.create(
                    booking=booking,
                    amount=deposit_amount,
                    status='held'
                )
            
            # Redirect to rental agreement signing (required before payment)
            return redirect('sign_rental_agreement', booking_id=booking.id)
    else:
        form = BookingForm()
    
    return render(request, 'booking.html', {
        'vehicle': vehicle, 
        'form': form,
        'booked_dates_json': booked_dates_json,
        'existing_bookings': existing_bookings
    })


@login_required
def payment_view(request, booking_id):
    """Handle payment with PayMongo"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if rental agreement is signed
    if not booking.contract_signed:
        messages.warning(request, 'Please sign the rental agreement before proceeding to payment.')
        return redirect('sign_rental_agreement', booking_id=booking.id)
    
    # Check if user is blacklisted
    is_blacklisted, blacklist = check_user_blacklist(request.user)
    if is_blacklisted:
        messages.error(request, f'Your account has been blacklisted. Reason: {blacklist.reason}')
        return redirect('dashboard')
    
    if booking.payment_status == 'paid':
        messages.info(request, 'This booking has already been paid.')
        return redirect('booking_detail', booking_id=booking.id)
    
    if request.method == 'POST':
        # Create payment session with PayMongo
        try:
            payment_url, payment_error = create_paymongo_session(request, booking)
            if payment_url:
                return redirect(payment_url)
            else:
                messages.error(
                    request,
                    payment_error or 'Failed to create payment session. Please try again.'
                )
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
    
    context = {
        'booking': booking,
    }
    return render(request, 'payment.html', context)


def _extract_paymongo_error(response):
    """Extract the most useful error detail from a PayMongo API response."""
    try:
        payload = response.json()
    except ValueError:
        return f"PayMongo request failed with HTTP {response.status_code}."

    if not isinstance(payload, dict):
        return f"PayMongo request failed with HTTP {response.status_code}."

    errors = payload.get('errors')
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        detail = first_error.get('detail') or first_error.get('title')
        pointer = first_error.get('source', {}).get('pointer')
        if detail and pointer:
            return f"{detail} ({pointer})"
        if detail:
            return detail

    message = payload.get('message') or payload.get('error')
    if message:
        return str(message)

    return f"PayMongo request failed with HTTP {response.status_code}."


def create_paymongo_session(request, booking):
    """Create a PayMongo checkout session."""
    import base64

    url = "https://api.paymongo.com/v1/checkout_sessions"

    secret_key = settings.PAYMONGO_SECRET_KEY
    encoded_key = base64.b64encode(f"{secret_key}:".encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json",
    }

    success_url = request.build_absolute_uri(
        f"{reverse('payment_success')}?booking_id={booking.id}"
    )
    cancel_url = request.build_absolute_uri(
        f"{reverse('payment_cancel')}?booking_id={booking.id}"
    )

    user = booking.user
    phone = getattr(getattr(user, 'profile', None), 'phone_number', '') or ''

    data = {
        "data": {
            "attributes": {
                "billing": {
                    "name": user.get_full_name() or user.username,
                    "email": user.email,
                    "phone": phone,
                },
                "send_email_receipt": True,
                "show_description": True,
                "show_line_items": True,
                "line_items": [
                    {
                        "currency": "PHP",
                        "amount": int(booking.total_price * 100),
                        "name": "Rent2Ride Booking",
                        "quantity": 1,
                    }
                ],
                "payment_method_types": ["qrph", "card"],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "description": "Rent2Ride Vehicle Booking Payment",
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code >= 400:
            return None, _extract_paymongo_error(response)
        result = response.json()

        if 'data' in result and 'attributes' in result['data']:
            checkout_url = result['data']['attributes']['checkout_url']
            session_id = result['data']['id']

            Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'transaction_id': str(uuid.uuid4()),
                    'payment_amount': booking.total_price,
                    'payment_status': 'pending',
                    'paymongo_session_id': session_id,
                },
            )

            return checkout_url, None
    except requests.exceptions.RequestException as e:
        return None, f"Unable to connect to PayMongo: {str(e)}"

    return None, "PayMongo did not return a checkout URL."


@login_required
def payment_success_view(request):
    """Handle successful payment callback"""
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Update booking and payment status
    booking.status = 'confirmed'
    booking.payment_status = 'paid'
    booking.is_locked = False  # Unlock after payment
    booking.save()
    
    # Remove availability lock
    AvailabilityLock.objects.filter(booking=booking).update(is_active=False)
    
    # Restore vehicle availability (if no other active locks)
    active_locks = AvailabilityLock.objects.filter(
        vehicle=booking.vehicle,
        is_active=True
    ).exists()
    if not active_locks:
        booking.vehicle.status = 'available'
        booking.vehicle.save()
    
    if hasattr(booking, 'payment'):
        booking.payment.payment_status = 'success'
        booking.payment.save()
    
    # Calculate and create commission (automated)
    commission_percentage = Decimal('10.00')  # 10% platform commission
    commission_amount = booking.total_price * (commission_percentage / 100)
    owner_earnings = booking.total_price - commission_amount
    
    Commission.objects.update_or_create(
        booking=booking,
        defaults={
            'commission_percentage': commission_percentage,
            'commission_amount': commission_amount,
            'owner_earnings': owner_earnings,
            'paid_to_owner': False,
        }
    )
    
    # Generate invoice
    try:
        invoice = Invoice.objects.get(booking=booking)
    except Invoice.DoesNotExist:
        invoice_number = f"INV-{booking.id}-{timezone.now().strftime('%Y%m%d')}"
        invoice = Invoice.objects.create(
            booking=booking,
            invoice_number=invoice_number
        )
    
    # Log audit
    AuditLog.objects.create(
        admin_user=None,  # System action
        action_type='payment_changed',
        target_user=booking.user,
        description=f'Payment successful for booking #{booking.id}',
        new_value=f'Status: confirmed, Amount: ₱{booking.total_price}',
    )
    
    messages.success(request, 'Payment successful! Your booking is confirmed.')
    return render(request, 'payment_success.html', {'booking': booking, 'invoice': invoice})


@login_required
def payment_cancel_view(request):
    """Handle canceled payment"""
    booking_id = request.GET.get('booking_id')
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if hasattr(booking, 'payment'):
        booking.payment.payment_status = 'failed'
        booking.payment.save()
    
    messages.warning(request, 'Payment was canceled.')
    return render(request, 'payment_failure.html', {'booking': booking})


@login_required
def booking_detail_view(request, booking_id):
    """View booking details with expiration timer"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user has permission to view this booking
    if booking.user != request.user and booking.vehicle.owner != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('dashboard')
    
    # Calculate time remaining until expiration
    time_remaining = None
    if booking.expires_at and booking.status == 'pending' and booking.payment_status == 'pending':
        now = timezone.now()
        if booking.expires_at > now:
            time_remaining = booking.expires_at - now
        else:
            # Booking has expired
            booking.status = 'expired'
            booking.save()
            messages.warning(request, 'This booking has expired. Please create a new booking.')
    
    # Get related data
    refunds = Refund.objects.filter(booking=booking)
    damage_report = None
    try:
        damage_report = DamageReport.objects.get(booking=booking)
    except DamageReport.DoesNotExist:
        pass
    
    security_deposit = None
    try:
        security_deposit = SecurityDeposit.objects.get(booking=booking)
    except SecurityDeposit.DoesNotExist:
        pass
    
    context = {
        'booking': booking,
        'time_remaining': time_remaining,
        'refunds': refunds,
        'damage_report': damage_report,
        'security_deposit': security_deposit,
    }
    return render(request, 'booking_detail.html', context)


def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or (hasattr(user, 'profile') and user.profile.is_admin)
    )


@login_required
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    from django.contrib.auth.models import User
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    thirty_ago = now - timedelta(days=30)

    total_users    = User.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_bookings = Booking.objects.count()

    pending_vehicles      = Vehicle.objects.filter(status='pending_approval').count()
    pending_bookings      = Booking.objects.filter(status='pending').count()
    license_verifications = DriversLicense.objects.filter(status='pending').count()
    new_users_30d         = User.objects.filter(date_joined__gte=thirty_ago).count()
    pending_count         = pending_vehicles + pending_bookings + license_verifications

    total_revenue = Payment.objects.filter(payment_status='success').aggregate(
        t=Sum('payment_amount'))['t'] or 0
    avg_per_booking = (float(total_revenue) / total_bookings) if total_bookings else 0
    completed       = Booking.objects.filter(status='completed').count()
    completion_rate = (completed / total_bookings * 100) if total_bookings else 0

    chart_labels = []
    chart_data   = []
    for i in range(5, -1, -1):
        ms = now.replace(day=1) - timedelta(days=30 * i)
        me = ms + timedelta(days=30)
        rev = Payment.objects.filter(
            payment_status='success', created_at__gte=ms, created_at__lt=me
        ).aggregate(t=Sum('payment_amount'))['t'] or 0
        chart_labels.append(ms.strftime('%b %Y'))
        chart_data.append(float(rev))

    most_rented_vehicles = [
        {'name': v['name'], 'owner': v['owner__username'], 'bookings': v['bc']}
        for v in Vehicle.objects.annotate(
            bc=Count('bookings', filter=Q(bookings__status='completed'))
        ).order_by('-bc').values('name', 'owner__username', 'bc')[:10]
    ]

    active_locations = [
        {'name': loc['location'], 'vehicles': loc['vc'], 'bookings': loc['bc']}
        for loc in Vehicle.objects.values('location').annotate(
            vc=Count('id'),
            bc=Count('bookings', filter=Q(bookings__status='completed'))
        ).order_by('-bc')[:10]
    ]

    recent_bookings = [
        {'id': b.id, 'user': b.user.username, 'vehicle': str(b.vehicle), 'status': b.status}
        for b in Booking.objects.select_related('user', 'vehicle').order_by('-created_at')[:5]
    ]

    recent_vehicles = [
        {'model': v.name, 'owner': v.owner.username, 'status': v.status}
        for v in Vehicle.objects.select_related('owner').order_by('-created_at')[:5]
    ]

    context = {
        'pending_count':         pending_count,
        'pending_vehicles':      pending_vehicles,
        'pending_bookings':      pending_bookings,
        'license_verifications': license_verifications,
        'new_users_30d':         new_users_30d,
        'total_users':           total_users,
        'total_vehicles':        total_vehicles,
        'total_bookings':        total_bookings,
        'total_revenue':         total_revenue,
        'avg_per_booking':       avg_per_booking,
        'completion_rate':       completion_rate,
        'chart_labels':          json.dumps(chart_labels),
        'chart_data':            json.dumps(chart_data),
        'most_rented_vehicles':  most_rented_vehicles,
        'active_locations':      active_locations,
        'recent_bookings':       recent_bookings,
        'recent_vehicles':       recent_vehicles,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users_view(request):
    """Admin view to manage users"""
    from django.contrib.auth.models import User
    from users.models import UserProfile
    
    users = User.objects.all().select_related('profile')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user = User.objects.get(id=user_id)
            if action == 'delete':
                user.delete()
                messages.success(request, f'User {user.username} deleted successfully.')
            elif action == 'block':
                user.is_active = False
                user.save()
                messages.success(request, f'User {user.username} blocked successfully.')
            elif action == 'unblock':
                user.is_active = True
                user.save()
                messages.success(request, f'User {user.username} unblocked successfully.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    
    context = {
        'users': users,
    }
    return render(request, 'admin_users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_vehicles_view(request):
    """Admin view to manage vehicles"""
    vehicles = Vehicle.objects.all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        action = request.POST.get('action')
        
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            if action == 'approve':
                old_status = vehicle.status
                vehicle.status = 'available'
                vehicle.reviewed_by = request.user
                vehicle.reviewed_at = timezone.now()
                vehicle.save()
                
                # Log audit
                AuditLog.objects.create(
                    admin_user=request.user,
                    action_type='vehicle_approved',
                    target_user=vehicle.owner,
                    description=f'Vehicle {vehicle.brand} {vehicle.model} approved',
                    old_value=f'Status: {old_status}',
                    new_value='Status: available',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Vehicle {vehicle.model} approved.')
            elif action == 'delete':
                vehicle_model = vehicle.model
                vehicle_owner = vehicle.owner
                vehicle.delete()
                
                # Log audit
                AuditLog.objects.create(
                    admin_user=request.user,
                    action_type='vehicle_approved',
                    target_user=vehicle_owner,
                    description=f'Vehicle {vehicle_model} deleted',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Vehicle {vehicle_model} deleted.')
        except Vehicle.DoesNotExist:
            messages.error(request, 'Vehicle not found.')
    
    context = {
        'vehicles': vehicles,
    }
    return render(request, 'admin_vehicles.html', context)


@login_required
@user_passes_test(is_admin)
def admin_bookings_view(request):
    """Admin view to manage bookings"""
    bookings = Booking.objects.all()
    
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        
        try:
            booking = Booking.objects.get(id=booking_id)
            if action == 'confirm':
                booking.status = 'confirmed'
                booking.save()
                messages.success(request, f'Booking #{booking.id} confirmed.')
            elif action == 'cancel':
                booking.status = 'canceled'
                booking.save()
                messages.success(request, f'Booking #{booking.id} canceled.')
        except Booking.DoesNotExist:
            messages.error(request, 'Booking not found.')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'admin_bookings.html', context)


def about_us_view(request):
    """About Us page"""
    return render(request, 'about_us.html')


def contact_view(request):
    """Contact page with contact form"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you can add email sending functionality
        # For now, just show a success message
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'contact.html')


def terms_of_service_view(request):
    """Terms of Service page"""
    return render(request, 'terms_of_service.html')


def privacy_policy_view(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')


# Identity Verification Views
@login_required
def identity_verification_view(request):
    """Upload and manage identity verification"""
    from .models import IdentityVerification
    from .forms import IdentityVerificationForm
    
    try:
        verification = IdentityVerification.objects.get(user=request.user)
    except IdentityVerification.DoesNotExist:
        verification = None
    
    if request.method == 'POST':
        if verification:
            form = IdentityVerificationForm(request.POST, request.FILES, instance=verification)
        else:
            form = IdentityVerificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.status = 'pending'
            verification.save()
            messages.success(request, 'Identity document uploaded successfully. Waiting for admin approval.')
            return redirect('identity_verification')
    else:
        if verification:
            form = IdentityVerificationForm(instance=verification)
        else:
            form = IdentityVerificationForm()
    
    context = {
        'verification': verification,
        'form': form,
    }
    return render(request, 'identity_verification.html', context)


# Rating & Review Views
@login_required
def submit_rating_view(request, booking_id):
    """Submit rating and review after booking completion"""
    from .models import Rating
    from .forms import RatingForm
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status='completed')
    
    # Check if rating already exists
    try:
        rating = Rating.objects.get(booking=booking)
        form = RatingForm(instance=rating)
        is_edit = True
    except Rating.DoesNotExist:
        rating = None
        form = RatingForm()
        is_edit = False
    
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.booking = booking
            rating.renter = request.user
            rating.save()
            messages.success(request, 'Thank you for your rating!')
            return redirect('booking_detail', booking_id=booking_id)
    
    context = {
        'booking': booking,
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, 'submit_rating.html', context)


# Saved Vehicles Views
@login_required
def save_vehicle_view(request, vehicle_id):
    """Save/unsave a vehicle"""
    from .models import SavedVehicle
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            SavedVehicle.objects.get_or_create(user=request.user, vehicle=vehicle)
            messages.success(request, 'Vehicle saved to your wishlist!')
        elif action == 'unsave':
            SavedVehicle.objects.filter(user=request.user, vehicle=vehicle).delete()
            messages.success(request, 'Vehicle removed from wishlist.')
    
    return redirect('vehicle_detail', vehicle_id=vehicle_id)


@login_required
def saved_vehicles_view(request):
    """View user's saved vehicles"""
    from .models import SavedVehicle
    
    saved_vehicles = SavedVehicle.objects.filter(user=request.user).select_related('vehicle')
    
    context = {
        'saved_vehicles': saved_vehicles,
    }
    return render(request, 'saved_vehicles.html', context)


def validate_promo_code_view(request):
    """API endpoint to validate promo codes"""
    from django.http import JsonResponse
    
    code = request.GET.get('code', '').strip().upper()
    
    if not code:
        return JsonResponse({'valid': False, 'message': 'Please enter a promo code'})
    
    try:
        promo = PromoCode.objects.get(code=code)
        if promo.is_valid():
            return JsonResponse({
                'valid': True,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
                'message': 'Promo code is valid'
            })
        else:
            return JsonResponse({
                'valid': False,
                'message': 'This promo code is not valid or has expired'
            })
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Invalid promo code'
        })


@login_required
def owner_earnings_view(request):
    """Owner earnings dashboard"""
    from django.db.models import Sum, Count
    from .models import Commission
    
    profile = request.user.profile
    if not profile.is_owner:
        messages.error(request, 'Only vehicle owners can access this page.')
        return redirect('dashboard')
    
    # Get owner's vehicles
    vehicles = Vehicle.objects.filter(owner=request.user)
    
    # Calculate earnings
    commissions = Commission.objects.filter(booking__vehicle__owner=request.user)
    total_earnings = commissions.aggregate(total=Sum('owner_earnings'))['total'] or 0
    paid_earnings = commissions.filter(paid_to_owner=True).aggregate(total=Sum('owner_earnings'))['total'] or 0
    pending_earnings = total_earnings - paid_earnings
    
    # Earnings by vehicle
    # Use field names that don't clash with model @property names
    vehicle_earnings = vehicles.annotate(
        total_bookings_count=Count('bookings', filter=Q(bookings__status='completed')),
        total_earnings_amount=Sum('bookings__commission__owner_earnings', filter=Q(bookings__status='completed'))
    ).order_by('-total_earnings_amount')
    
    # Recent bookings
    recent_bookings = Booking.objects.filter(
        vehicle__owner=request.user,
        status='completed'
    ).select_related('vehicle', 'commission').order_by('-created_at')[:10]
    
    context = {
        'total_earnings': total_earnings,
        'paid_earnings': paid_earnings,
        'pending_earnings': pending_earnings,
        'vehicle_earnings': vehicle_earnings,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'owner_earnings.html', context)


@login_required
@user_passes_test(is_admin)
def admin_payments_view(request):
    """Admin view to manage payments"""
    payments = Payment.objects.all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(payment_status=status_filter)
    
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        action = request.POST.get('action')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            if action == 'approve':
                # Approve payment and confirm booking
                payment.payment_status = 'success'
                payment.save()
                payment.booking.payment_status = 'paid'
                payment.booking.status = 'confirmed'
                payment.booking.save()
                messages.success(request, f'Payment #{payment.transaction_id} approved and booking confirmed.')
            elif action == 'reject':
                # Reject payment
                payment.payment_status = 'failed'
                payment.save()
                payment.booking.payment_status = 'failed'
                payment.booking.save()
                messages.success(request, f'Payment #{payment.transaction_id} rejected.')
        except Payment.DoesNotExist:
            messages.error(request, 'Payment not found.')
    
    context = {
        'payments': payments,
    }
    return render(request, 'admin_payments.html', context)


# ========== NEW FEATURES IMPLEMENTATION ==========

# Refund Management Views
@login_required
def request_refund_view(request, booking_id):
    """User-facing view to request a refund"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if booking is eligible for refund
    if booking.status not in ['confirmed', 'completed']:
        messages.error(request, 'This booking is not eligible for a refund.')
        return redirect('booking_detail', booking_id=booking_id)
    
    # Check if refund already exists
    existing_refund = Refund.objects.filter(booking=booking, requested_by=request.user).first()
    
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            if existing_refund:
                messages.error(request, 'You have already requested a refund for this booking.')
                return redirect('booking_detail', booking_id=booking_id)
            
            refund = form.save(commit=False)
            refund.booking = booking
            refund.requested_by = request.user
            refund.amount = booking.total_price  # Full refund by default
            refund.status = 'requested'
            refund.save()
            
            messages.success(request, 'Refund request submitted successfully. Admin will review it shortly.')
            return redirect('booking_detail', booking_id=booking_id)
    else:
        form = RefundRequestForm(initial={'amount': booking.total_price})
    
    context = {
        'booking': booking,
        'form': form,
        'existing_refund': existing_refund,
    }
    return render(request, 'request_refund.html', context)


@login_required
@user_passes_test(is_admin)
def manage_refunds_view(request):
    """Admin view to manage refund requests"""
    refunds = Refund.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        refunds = refunds.filter(status=status_filter)
    
    if request.method == 'POST':
        refund_id = request.POST.get('refund_id')
        action = request.POST.get('action')
        
        try:
            refund = Refund.objects.get(id=refund_id)
            if action == 'approve':
                refund.status = 'approved'
                refund.approved_by = request.user
                refund.approved_at = timezone.now()
                refund.save()
                messages.success(request, f'Refund #{refund.id} approved.')
            elif action == 'reject':
                refund.status = 'rejected'
                refund.approved_by = request.user
                refund.approved_at = timezone.now()
                refund.save()
                messages.success(request, f'Refund #{refund.id} rejected.')
        except Refund.DoesNotExist:
            messages.error(request, 'Refund not found.')
    
    context = {
        'refunds': refunds,
    }
    return render(request, 'manage_refunds.html', context)


# Damage Reporting Views
@login_required
def report_damage_view(request, booking_id):
    """Report damage after vehicle return"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is owner or renter
    if request.user != booking.user and request.user != booking.vehicle.owner:
        messages.error(request, 'You do not have permission to report damage for this booking.')
        return redirect('dashboard')
    
    # Check if damage report already exists
    existing_report = None
    try:
        existing_report = DamageReport.objects.get(booking=booking)
    except DamageReport.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = DamageReportForm(request.POST, request.FILES)
        if form.is_valid():
            if existing_report:
                # Update existing report
                existing_report.description = form.cleaned_data['description']
                existing_report.estimated_cost = form.cleaned_data['estimated_cost']
                existing_report.save()
                report = existing_report
            else:
                # Create new report
                report = form.save(commit=False)
                report.booking = booking
                report.reported_by = request.user
                report.status = 'pending'
                report.save()
            
            # Handle multiple photo uploads
            photos = request.FILES.getlist('photos')
            for photo in photos:
                DamagePhoto.objects.create(damage_report=report, photo=photo)
            
            messages.success(request, 'Damage report submitted successfully.')
            return redirect('booking_detail', booking_id=booking_id)
    else:
        if existing_report:
            form = DamageReportForm(instance=existing_report)
        else:
            form = DamageReportForm()
    
    context = {
        'booking': booking,
        'form': form,
        'existing_report': existing_report,
    }
    return render(request, 'report_damage.html', context)


@login_required
def confirm_damage_view(request, damage_report_id):
    """Owner confirms damage report"""
    damage_report = get_object_or_404(DamageReport, id=damage_report_id)
    
    if request.user != damage_report.booking.vehicle.owner:
        messages.error(request, 'Only the vehicle owner can confirm damage reports.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            damage_report.status = 'confirmed'
            damage_report.save()
            messages.success(request, 'Damage report confirmed.')
        elif action == 'dispute':
            damage_report.status = 'disputed'
            damage_report.owner_response = request.POST.get('response', '')
            damage_report.save()
            messages.success(request, 'Damage report disputed.')
    
    return redirect('booking_detail', booking_id=damage_report.booking.id)


# Messaging System Views
@login_required
def messages_list_view(request):
    """List all conversations for the user"""
    # Get all messages where user is sender or recipient
    sent_messages = Message.objects.filter(sender=request.user).select_related('recipient', 'booking')
    received_messages = Message.objects.filter(recipient=request.user).select_related('sender', 'booking')
    
    # Get unique conversations (group by booking or other user)
    conversations = {}
    
    for msg in sent_messages:
        key = f"booking_{msg.booking.id}" if msg.booking else f"user_{msg.recipient.id}"
        if key not in conversations:
            conversations[key] = {
                'booking': msg.booking,
                'other_user': msg.recipient,
                'last_message': msg,
                'unread_count': 0,
            }
        if msg.created_at > conversations[key]['last_message'].created_at:
            conversations[key]['last_message'] = msg
    
    for msg in received_messages:
        key = f"booking_{msg.booking.id}" if msg.booking else f"user_{msg.sender.id}"
        if key not in conversations:
            conversations[key] = {
                'booking': msg.booking,
                'other_user': msg.sender,
                'last_message': msg,
                'unread_count': 0,
            }
        else:
            if msg.created_at > conversations[key]['last_message'].created_at:
                conversations[key]['last_message'] = msg
        if not msg.is_read:
            conversations[key]['unread_count'] += 1
    
    context = {
        'conversations': list(conversations.values()),
    }
    return render(request, 'messages_list.html', context)


@login_required
def conversation_view(request, booking_id):
    """View conversation for a specific booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is part of this booking
    if request.user != booking.user and request.user != booking.vehicle.owner:
        messages.error(request, 'You do not have permission to view this conversation.')
        return redirect('dashboard')
    
    # Get other user
    if request.user == booking.user:
        other_user = booking.vehicle.owner
    else:
        other_user = booking.user
    
    # Get all messages for this booking
    messages_list = Message.objects.filter(booking=booking).order_by('created_at')
    
    # Mark received messages as read
    Message.objects.filter(booking=booking, recipient=request.user, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.booking = booking
            message.sender = request.user
            message.recipient = other_user
            message.save()
            messages.success(request, 'Message sent successfully.')
            return redirect('conversation', booking_id=booking_id)
    else:
        form = MessageForm()
    
    context = {
        'booking': booking,
        'other_user': other_user,
        'messages': messages_list,
        'form': form,
    }
    return render(request, 'conversation.html', context)


# Security Deposit Management
@login_required
def security_deposit_view(request, booking_id):
    """View security deposit details"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user is part of this booking
    if request.user != booking.user and request.user != booking.vehicle.owner:
        messages.error(request, 'You do not have permission to view this deposit.')
        return redirect('dashboard')
    
    security_deposit = None
    try:
        security_deposit = SecurityDeposit.objects.get(booking=booking)
    except SecurityDeposit.DoesNotExist:
        pass
    
    context = {
        'booking': booking,
        'security_deposit': security_deposit,
    }
    return render(request, 'security_deposit.html', context)


# ========== ALL 15 NEW FEATURES IMPLEMENTATION ==========

# 1. DRIVER'S LICENSE VERIFICATION
@login_required
def upload_drivers_license_view(request):
    """Upload driver's license"""
    try:
        license_obj = DriversLicense.objects.get(user=request.user)
        form = DriversLicenseForm(instance=license_obj)
        is_edit = True
    except DriversLicense.DoesNotExist:
        license_obj = None
        form = DriversLicenseForm()
        is_edit = False
    
    if request.method == 'POST':
        form = DriversLicenseForm(request.POST, request.FILES, instance=license_obj)
        if form.is_valid():
            license_obj = form.save(commit=False)
            license_obj.user = request.user
            license_obj.status = 'pending'
            license_obj.save()
            messages.success(request, 'Driver\'s license uploaded successfully. Waiting for admin verification.')
            return redirect('dashboard')
    
    context = {
        'form': form,
        'license': license_obj,
        'is_edit': is_edit,
    }
    return render(request, 'upload_drivers_license.html', context)


@login_required
@user_passes_test(is_admin)
def verify_drivers_license_view(request, license_id):
    """Admin verify driver's license"""
    license_obj = get_object_or_404(DriversLicense, id=license_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            license_obj.status = 'verified'
            license_obj.verified_by = request.user
            license_obj.verified_at = timezone.now()
            license_obj.save()

            # Mark user as identity-verified so they can make bookings
            profile = license_obj.user.profile
            profile.is_verified = True
            profile.verified_badge = True
            profile.save()

            # Update booking license_verified flag
            Booking.objects.filter(user=license_obj.user, status='pending').update(license_verified=True)

            # Log audit
            AuditLog.objects.create(
                admin_user=request.user,
                action_type='license_verified',
                target_user=license_obj.user,
                description=f'Driver\'s license verified for {license_obj.user.username}',
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, 'Driver\'s license verified successfully.')
        elif action == 'reject':
            license_obj.status = 'rejected'
            license_obj.rejection_reason = request.POST.get('rejection_reason', '')
            license_obj.verified_by = request.user
            license_obj.verified_at = timezone.now()
            license_obj.save()
            
            AuditLog.objects.create(
                admin_user=request.user,
                action_type='license_rejected',
                target_user=license_obj.user,
                description=f'Driver\'s license rejected for {license_obj.user.username}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Driver\'s license rejected.')
        
        return redirect('admin_drivers_licenses')
    
    context = {
        'license': license_obj,
    }
    return render(request, 'verify_drivers_license.html', context)


@login_required
@user_passes_test(is_admin)
def admin_drivers_licenses_view(request):
    """Admin view all driver's licenses"""
    licenses = DriversLicense.objects.all().order_by('-uploaded_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        licenses = licenses.filter(status=status_filter)
    
    context = {
        'licenses': licenses,
    }
    return render(request, 'admin_drivers_licenses.html', context)


# 2. BLACKLIST SYSTEM
@login_required
@user_passes_test(is_admin)
def blacklist_user_view(request, user_id):
    """Blacklist a user"""
    user = get_object_or_404(User, id=user_id)
    
    # Check if already blacklisted
    try:
        blacklist = Blacklist.objects.get(user=user)
        messages.warning(request, 'User is already blacklisted.')
        return redirect('admin_users')
    except Blacklist.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = BlacklistForm(request.POST)
        if form.is_valid():
            blacklist = form.save(commit=False)
            blacklist.user = user
            blacklist.blacklisted_by = request.user
            blacklist.save()
            
            # Cancel all pending bookings
            Booking.objects.filter(user=user, status__in=['pending', 'confirmed']).update(status='canceled')
            
            # Log audit
            AuditLog.objects.create(
                admin_user=request.user,
                action_type='user_blacklisted',
                target_user=user,
                description=f'User {user.username} blacklisted: {blacklist.reason}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'User {user.username} has been blacklisted.')
            return redirect('admin_users')
    else:
        form = BlacklistForm()
    
    context = {
        'user': user,
        'form': form,
    }
    return render(request, 'blacklist_user.html', context)


@login_required
@user_passes_test(is_admin)
def unblacklist_user_view(request, user_id):
    """Remove user from blacklist"""
    user = get_object_or_404(User, id=user_id)
    blacklist = get_object_or_404(Blacklist, user=user)
    
    if request.method == 'POST':
        blacklist.is_active = False
        blacklist.save()
        
        AuditLog.objects.create(
            admin_user=request.user,
            action_type='user_blacklisted',
            target_user=user,
            description=f'User {user.username} removed from blacklist',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'User {user.username} has been removed from blacklist.')
        return redirect('admin_users')
    
    context = {
        'user': user,
        'blacklist': blacklist,
    }
    return render(request, 'unblacklist_user.html', context)


# 3. RENTAL AGREEMENT
@login_required
def sign_rental_agreement_view(request, booking_id):
    """Sign rental agreement"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if user is blacklisted
    if hasattr(booking.user, 'blacklist') and booking.user.blacklist.is_active:
        messages.error(request, 'You cannot sign agreements. Your account has been blacklisted.')
        return redirect('dashboard')
    
    # Get or create rental agreement
    try:
        agreement = RentalAgreement.objects.get(booking=booking)
    except RentalAgreement.DoesNotExist:
        # Generate contract number
        contract_number = f"R2R-{booking.id}-{timezone.now().strftime('%Y%m%d')}"
        agreement = RentalAgreement.objects.create(
            booking=booking,
            contract_number=contract_number,
            status='pending'
        )
    
    if request.method == 'POST':
        form = RentalAgreementSignatureForm(request.POST)
        if form.is_valid() and form.cleaned_data.get('agreed_to_terms'):
            signature = form.cleaned_data.get('signature')
            agreement.renter_signature = signature
            agreement.renter_signed_at = timezone.now()
            agreement.status = 'signed'

            # PDF generation is best-effort — a failure must not block signing
            try:
                from .utils import generate_rental_agreement_pdf
                from django.core.files.base import ContentFile
                pdf_buffer = generate_rental_agreement_pdf(agreement)
                agreement.pdf_file.save(
                    f'agreement_{agreement.contract_number}.pdf',
                    ContentFile(pdf_buffer.read()),
                    save=False
                )
            except Exception:
                pass

            agreement.save()

            booking.contract_signed = True
            booking.save()

            messages.success(request, 'Rental agreement signed successfully!')
            return redirect('payment', booking_id=booking.id)
    else:
        form = RentalAgreementSignatureForm()
    
    context = {
        'booking': booking,
        'agreement': agreement,
        'form': form,
    }
    return render(request, 'sign_rental_agreement.html', context)


# 4. VEHICLE COMPARISON
@login_required
def compare_vehicles_view(request):
    """Compare selected vehicles"""
    vehicle_ids = request.GET.getlist('vehicles')
    
    if not vehicle_ids or len(vehicle_ids) < 2:
        messages.error(request, 'Please select at least 2 vehicles to compare.')
        return redirect('vehicle_list')
    
    if len(vehicle_ids) > 3:
        messages.warning(request, 'You can compare up to 3 vehicles. Showing first 3.')
        vehicle_ids = vehicle_ids[:3]
    
    vehicles = Vehicle.objects.filter(id__in=vehicle_ids, status='available')
    
    if vehicles.count() < 2:
        messages.error(request, 'Not enough valid vehicles found for comparison.')
        return redirect('vehicle_list')
    
    # Save comparison for user
    if request.user.is_authenticated:
        comparison, created = VehicleComparison.objects.get_or_create(user=request.user)
        comparison.vehicles.set(vehicles)
    
    context = {
        'vehicles': vehicles,
    }
    return render(request, 'compare_vehicles.html', context)


# 5. PAYOUT REQUEST
@login_required
def request_payout_view(request):
    """Owner request payout"""
    profile = request.user.profile
    if not profile.is_owner:
        messages.error(request, 'Only vehicle owners can request payouts.')
        return redirect('dashboard')
    
    # Calculate available earnings
    from django.db.models import Sum
    commissions = Commission.objects.filter(
        booking__vehicle__owner=request.user,
        paid_to_owner=False
    )
    available_earnings = commissions.aggregate(total=Sum('owner_earnings'))['total'] or Decimal('0.00')
    
    if request.method == 'POST':
        form = PayoutRequestForm(request.POST)
        if form.is_valid():
            payout = form.save(commit=False)
            payout.owner = request.user
            payout.amount = available_earnings
            payout.status = 'pending'
            payout.save()
            
            messages.success(request, 'Payout request submitted successfully. Admin will review it shortly.')
            return redirect('owner_earnings')
    else:
        form = PayoutRequestForm(initial={'amount': available_earnings})
    
    context = {
        'form': form,
        'available_earnings': available_earnings,
    }
    return render(request, 'request_payout.html', context)


@login_required
@user_passes_test(is_admin)
def manage_payouts_view(request):
    """Admin manage payout requests"""
    payouts = PayoutRequest.objects.all().order_by('-requested_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        payouts = payouts.filter(status=status_filter)
    
    if request.method == 'POST':
        payout_id = request.POST.get('payout_id')
        action = request.POST.get('action')
        
        try:
            payout = PayoutRequest.objects.get(id=payout_id)
            if action == 'approve':
                payout.status = 'approved'
                payout.approved_by = request.user
                payout.approved_at = timezone.now()
                payout.save()
                
                # Mark commissions as paid
                Commission.objects.filter(
                    booking__vehicle__owner=payout.owner,
                    paid_to_owner=False
                ).update(paid_to_owner=True, paid_at=timezone.now())
                
                AuditLog.objects.create(
                    admin_user=request.user,
                    action_type='payment_changed',
                    target_user=payout.owner,
                    description=f'Payout approved: ₱{payout.amount}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, f'Payout #{payout.id} approved.')
            elif action == 'reject':
                payout.status = 'rejected'
                payout.approved_by = request.user
                payout.approved_at = timezone.now()
                payout.rejection_reason = request.POST.get('rejection_reason', '')
                payout.save()
                
                messages.success(request, f'Payout #{payout.id} rejected.')
        except PayoutRequest.DoesNotExist:
            messages.error(request, 'Payout not found.')
    
    context = {
        'payouts': payouts,
    }
    return render(request, 'manage_payouts.html', context)


# 6. VEHICLE UTILIZATION TRACKING
@login_required
@user_passes_test(is_admin)
def vehicle_utilization_view(request):
    """View vehicle utilization analytics"""
    from django.db.models import Count, Sum, Avg
    from datetime import datetime
    
    month = request.GET.get('month')
    if month:
        try:
            month_date = datetime.strptime(month, '%Y-%m').date()
        except:
            month_date = timezone.now().date().replace(day=1)
    else:
        month_date = timezone.now().date().replace(day=1)
    
    # Get utilization data
    utilizations = VehicleUtilization.objects.filter(month=month_date).select_related('vehicle')
    
    # Calculate totals
    total_vehicles = Vehicle.objects.filter(status='available').count()
    total_days_rented = utilizations.aggregate(total=Sum('days_rented'))['total'] or 0
    total_revenue = utilizations.aggregate(total=Sum('total_revenue'))['total'] or Decimal('0.00')
    avg_utilization = utilizations.aggregate(avg=Avg('utilization_percentage'))['avg'] or 0
    
    context = {
        'utilizations': utilizations,
        'month': month_date,
        'total_vehicles': total_vehicles,
        'total_days_rented': total_days_rented,
        'total_revenue': total_revenue,
        'avg_utilization': avg_utilization,
    }
    return render(request, 'vehicle_utilization.html', context)


# 7. PEAK DEMAND HEATMAP
@login_required
@user_passes_test(is_admin)
def peak_demand_heatmap_view(request):
    """View peak demand heatmap"""
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Get date range (last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Aggregate peak demand data
    peak_demands = PeakDemand.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'location', 'vehicle_type').annotate(
        total_demand=Sum('demand_count')
    ).order_by('-total_demand')[:50]
    
    # Top locations
    top_locations = PeakDemand.objects.filter(
        date__gte=start_date
    ).values('location').annotate(
        total=Sum('demand_count')
    ).order_by('-total')[:10]
    
    # Top vehicle types
    top_vehicle_types = PeakDemand.objects.filter(
        date__gte=start_date
    ).values('vehicle_type').annotate(
        total=Sum('demand_count')
    ).order_by('-total')
    
    context = {
        'peak_demands': peak_demands,
        'top_locations': top_locations,
        'top_vehicle_types': top_vehicle_types,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'peak_demand_heatmap.html', context)


# 8. REFERRAL SYSTEM
@login_required
def referral_view(request):
    """Referral system"""
    from .models import ReferralCode
    
    # Get or create referral code
    try:
        referral_code_obj = ReferralCode.objects.get(user=request.user)
    except ReferralCode.DoesNotExist:
        # Generate unique referral code
        code = f"REF{request.user.id}{timezone.now().strftime('%Y%m%d')}"
        referral_code_obj = ReferralCode.objects.create(
            user=request.user,
            code=code
        )
    
    # Get referrals made (actual referrals where someone used the code)
    referrals_made = Referral.objects.filter(referrer=request.user)
    
    context = {
        'referral_code': referral_code_obj,
        'referrals_made': referrals_made,
    }
    return render(request, 'referral.html', context)


@login_required
def apply_referral_view(request):
    """Apply referral code during signup"""
    from .models import ReferralCode
    
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['referral_code'].upper()
            try:
                referral_code_obj = ReferralCode.objects.get(code=code)
                # Store in session for signup
                request.session['referral_code'] = code
                request.session['referrer_id'] = referral_code_obj.user.id
                messages.success(request, 'Referral code applied! You will receive a discount after signup.')
                return redirect('signup')
            except ReferralCode.DoesNotExist:
                messages.error(request, 'Invalid referral code.')
    else:
        form = ReferralForm()
    
    return render(request, 'apply_referral.html', {'form': form})


# 9. LOYALTY POINTS
@login_required
def loyalty_points_view(request):
    """View loyalty points"""
    points, created = LoyaltyPoints.objects.get_or_create(user=request.user)
    transactions = LoyaltyTransaction.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    # Calculate available points (not expired)
    from django.utils import timezone
    available_points = points.total_points - points.redeemed_points - points.expired_points
    
    context = {
        'points': points,
        'available_points': available_points,
        'transactions': transactions,
    }
    return render(request, 'loyalty_points.html', context)


# 10. AUDIT LOG
@login_required
@user_passes_test(is_admin)
def audit_log_view(request):
    """View audit logs"""
    logs = AuditLog.objects.all().order_by('-created_at')[:100]
    
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    context = {
        'logs': logs,
        'action_types': AuditLog.ACTION_TYPES,
    }
    return render(request, 'audit_log.html', context)


# 11. INVOICE GENERATION
@login_required
def generate_invoice_view(request, booking_id):
    """Generate invoice for booking"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check permission
    if booking.user != request.user and booking.vehicle.owner != request.user:
        messages.error(request, 'You do not have permission to view this invoice.')
        return redirect('dashboard')
    
    # Get or create invoice
    try:
        invoice = Invoice.objects.get(booking=booking)
    except Invoice.DoesNotExist:
        invoice_number = f"INV-{booking.id}-{timezone.now().strftime('%Y%m%d')}"
        invoice = Invoice.objects.create(
            booking=booking,
            invoice_number=invoice_number
        )
    
    # Generate PDF if not exists or regenerate on request
    if request.GET.get('pdf') == '1' or not invoice.pdf_file:
        from .utils import generate_invoice_pdf
        from django.core.files.base import ContentFile
        pdf_buffer = generate_invoice_pdf(invoice)
        invoice.pdf_file.save(
            f'invoice_{invoice.invoice_number}.pdf',
            ContentFile(pdf_buffer.read()),
            save=True
        )
        if request.GET.get('pdf') == '1':
            from django.http import HttpResponse
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            return response
    
    context = {
        'booking': booking,
        'invoice': invoice,
    }
    return render(request, 'invoice.html', context)


# Helper function to check blacklist
def check_user_blacklist(user):
    """Check if user is blacklisted"""
    try:
        blacklist = Blacklist.objects.get(user=user, is_active=True)
        return True, blacklist
    except Blacklist.DoesNotExist:
        return False, None
