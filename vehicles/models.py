from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('suv', 'SUV'),
        ('van', 'Van'),
        ('truck', 'Truck'),
    ]

    FUEL_TYPES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('cng', 'CNG'),
    ]

    TRANSMISSION_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('not_available', 'Not Available'),
        ('pending_approval', 'Pending Approval'),
        ('rejected', 'Rejected'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    model = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    location = models.CharField(max_length=200)
    seats = models.PositiveIntegerField(default=4, help_text='Number of seats')
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, default='petrol')
    transmission_type = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, default='manual')
    available_from = models.DateTimeField()
    available_to = models.DateTimeField()
    image_url = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    # Enhanced features
    is_featured = models.BooleanField(default=False)
    instant_booking = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vehicles')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_average_rating(self):
        """Calculate average rating for vehicle"""
        # Access through booking relationship
        from django.db.models import Avg
        avg = Rating.objects.filter(booking__vehicle=self).aggregate(Avg('vehicle_rating'))['vehicle_rating__avg']
        return round(avg, 2) if avg else None
    
    @property
    def total_bookings(self):
        """Total number of completed bookings"""
        return self.bookings.filter(status='completed').count()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.model} - {self.owner.username}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(null=True, blank=True)  # Actual return time
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    late_penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=20, choices=[('full', 'Full Payment'), ('deposit', 'Deposit Only')], default='full')
    expires_at = models.DateTimeField(null=True, blank=True)  # Booking expiration
    is_locked = models.BooleanField(default=False)  # Lock during checkout
    locked_at = models.DateTimeField(null=True, blank=True)
    contract_signed = models.BooleanField(default=False)  # Rental agreement signed
    license_verified = models.BooleanField(default=False)  # Driver's license verified
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} - {self.vehicle.model}"

    def calculate_total_price(self):
        """Calculate total price based on rental days"""
        from datetime import timedelta
        days = (self.end_date - self.start_date).days + 1
        return self.vehicle.price_per_day * days


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paymongo_session_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.transaction_id} - {self.payment_status}"


# New Models for Enhanced Features

class VehicleDocument(models.Model):
    """Documents uploaded by vehicle owners for approval"""
    DOCUMENT_TYPES = [
        ('or_cr', 'OR/CR (Official Receipt/Certificate of Registration)'),
        ('insurance', 'Insurance Certificate'),
        ('id', 'Owner ID'),
        ('other', 'Other'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='vehicle_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.vehicle}"


class IdentityVerification(models.Model):
    """User identity verification"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='identity_verification')
    id_document = models.FileField(upload_to='identity_documents/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"Verification - {self.user.username} - {self.status}"


class Rating(models.Model):
    """Ratings and reviews for vehicles and owners"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='rating')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    vehicle_rating = models.IntegerField(choices=RATING_CHOICES)
    owner_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    vehicle_review = models.TextField(blank=True)
    owner_review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating - {self.booking.vehicle} - {self.vehicle_rating} stars"


class SecurityDeposit(models.Model):
    """Security deposit holds for bookings"""
    STATUS_CHOICES = [
        ('held', 'Held'),
        ('refunded', 'Refunded'),
        ('deducted', 'Deducted'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='security_deposit')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='held')
    paymongo_hold_id = models.CharField(max_length=200, blank=True, null=True)
    held_at = models.DateTimeField(auto_now_add=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    deducted_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deduction_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"Deposit - Booking #{self.booking.id} - {self.status}"


class Commission(models.Model):
    """Platform commission tracking"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='commission')
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    owner_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    paid_to_owner = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Commission - Booking #{self.booking.id} - ₱{self.commission_amount}"


class PromoCode(models.Model):
    """Discount promo codes"""
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_promo_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}%"
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True


class SavedVehicle(models.Model):
    """User's saved/bookmarked vehicles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'vehicle']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.vehicle}"


class DamageReport(models.Model):
    """Damage reports after vehicle return"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed by Owner'),
        ('disputed', 'Disputed'),
        ('resolved', 'Resolved'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='damage_report')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='damage_reports')
    description = models.TextField()
    damage_photos = models.ManyToManyField('DamagePhoto', blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    owner_response = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Damage Report - Booking #{self.booking.id}"


class DamagePhoto(models.Model):
    """Photos uploaded for damage reports"""
    damage_report = models.ForeignKey(DamageReport, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='damage_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo - {self.damage_report}"


class Message(models.Model):
    """In-app messaging between users"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"


class Refund(models.Model):
    """Refund management"""
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='refunds')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    paymongo_refund_id = models.CharField(max_length=200, blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund - Booking #{self.booking.id} - {self.status}"


# ========== NEW FEATURES MODELS ==========

class RentalAgreement(models.Model):
    """Digital rental agreement/contract"""
    STATUS_CHOICES = [
        ('pending', 'Pending Signature'),
        ('signed', 'Signed'),
        ('expired', 'Expired'),
    ]
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='rental_agreement')
    contract_number = models.CharField(max_length=50, unique=True)
    renter_signature = models.TextField(blank=True, null=True)  # Base64 encoded signature
    renter_signed_at = models.DateTimeField(null=True, blank=True)
    owner_signature = models.TextField(blank=True, null=True)
    owner_signed_at = models.DateTimeField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='rental_agreements/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    terms_and_conditions = models.TextField(default='Standard rental terms apply.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Agreement #{self.contract_number} - Booking #{self.booking.id}"


class DriversLicense(models.Model):
    """Driver's license verification"""
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='drivers_license')
    license_number = models.CharField(max_length=100)
    license_image_front = models.ImageField(upload_to='drivers_licenses/', blank=True, null=True)
    license_image_back = models.ImageField(upload_to='drivers_licenses/', blank=True, null=True)
    expiration_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_licenses')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"License - {self.user.username} - {self.status}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now().date() > self.expiration_date


class Blacklist(models.Model):
    """Blacklisted users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='blacklist')
    reason = models.TextField()
    blacklisted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blacklisted_users')
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Blacklisted: {self.user.username}"


class VehicleUtilization(models.Model):
    """Track vehicle utilization metrics"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='utilization_records')
    month = models.DateField()  # First day of month
    days_rented = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    utilization_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    idle_days = models.IntegerField(default=0)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['vehicle', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"Utilization - {self.vehicle} - {self.month}"


class PeakDemand(models.Model):
    """Track peak demand data"""
    date = models.DateField()
    location = models.CharField(max_length=200)
    vehicle_type = models.CharField(max_length=20)
    demand_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date', 'location', 'vehicle_type']
        ordering = ['-date', '-demand_count']
    
    def __str__(self):
        return f"Peak Demand - {self.date} - {self.location} - {self.vehicle_type}"


class ReturnReminder(models.Model):
    """Return reminder tracking"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='return_reminders')
    reminder_type = models.CharField(max_length=20, choices=[
        ('24h', '24 Hours Before'),
        ('late_penalty', 'Late Penalty Warning'),
        ('return_confirmation', 'Return Confirmation'),
    ])
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_via = models.CharField(max_length=20, choices=[('email', 'Email'), ('sms', 'SMS')], default='email')
    is_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reminder - Booking #{self.booking.id} - {self.reminder_type}"


class VehicleComparison(models.Model):
    """Store user vehicle comparisons"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_comparisons')
    vehicles = models.ManyToManyField(Vehicle, related_name='comparisons')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comparison - {self.user.username}"


class AvailabilityLock(models.Model):
    """Lock vehicle availability during checkout"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='availability_locks')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='availability_lock', null=True, blank=True)
    locked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Lock - {self.vehicle} - Expires: {self.expires_at}"


class AuditLog(models.Model):
    """Audit log for admin actions"""
    ACTION_TYPES = [
        ('booking_modified', 'Booking Modified'),
        ('vehicle_approved', 'Vehicle Approved'),
        ('vehicle_rejected', 'Vehicle Rejected'),
        ('payment_changed', 'Payment Changed'),
        ('user_role_changed', 'User Role Changed'),
        ('user_blacklisted', 'User Blacklisted'),
        ('refund_approved', 'Refund Approved'),
        ('refund_rejected', 'Refund Rejected'),
        ('license_verified', 'License Verified'),
        ('license_rejected', 'License Rejected'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs_target')
    description = models.TextField()
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Audit - {self.action_type} - {self.created_at}"


class PayoutRequest(models.Model):
    """Owner payout requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payouts')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=100, blank=True)  # Bank account, PayPal, etc.
    payment_details = models.TextField(blank=True)  # Account number, etc.
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Payout - {self.owner.username} - ₱{self.amount} - {self.status}"


class Invoice(models.Model):
    """Invoice and receipt generation"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - Booking #{self.booking.id}"


class ReferralCode(models.Model):
    """User's referral code"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_code')
    code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Referral Code - {self.user.username}: {self.code}"


class Referral(models.Model):
    """Referral tracking - when someone uses a referral code"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    referral_code = models.CharField(max_length=50)
    discount_applied = models.BooleanField(default=False)
    reward_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('referrer', 'referred_user')
    
    def __str__(self):
        return f"Referral - {self.referrer.username} -> {self.referred_user.username}"


class LoyaltyPoints(models.Model):
    """Loyalty points system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_points')
    total_points = models.IntegerField(default=0)
    redeemed_points = models.IntegerField(default=0)
    expired_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loyalty - {self.user.username} - {self.total_points} points"


class LoyaltyTransaction(models.Model):
    """Loyalty points transactions"""
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()
    description = models.TextField()
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.user.username} - {self.points} points"
