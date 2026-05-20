from django.contrib import admin
from .models import (
    Vehicle, Booking, Payment, PromoCode, SecurityDeposit, Rating,
    IdentityVerification, VehicleDocument, SavedVehicle, DamageReport,
    DamagePhoto, Message, Refund, Commission, RentalAgreement, DriversLicense,
    Blacklist, VehicleUtilization, PeakDemand, ReturnReminder, VehicleComparison,
    AvailabilityLock, AuditLog, PayoutRequest, Invoice, Referral, LoyaltyPoints,
    LoyaltyTransaction
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['model', 'brand', 'vehicle_type', 'owner', 'price_per_day', 'status', 'is_featured', 'instant_booking', 'created_at']
    list_filter = ['vehicle_type', 'fuel_type', 'transmission_type', 'status', 'is_featured', 'instant_booking', 'created_at']
    search_fields = ['model', 'brand', 'owner__username', 'location']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_vehicles', 'reject_vehicles', 'feature_vehicles']
    
    def approve_vehicles(self, request, queryset):
        queryset.update(status='available')
    approve_vehicles.short_description = "Approve selected vehicles"
    
    def reject_vehicles(self, request, queryset):
        queryset.update(status='rejected')
    reject_vehicles.short_description = "Reject selected vehicles"
    
    def feature_vehicles(self, request, queryset):
        queryset.update(is_featured=True)
    feature_vehicles.short_description = "Feature selected vehicles"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vehicle', 'start_date', 'end_date', 'total_price', 'payment_type', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_type', 'created_at']
    search_fields = ['user__username', 'vehicle__model', 'vehicle__brand']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'booking', 'payment_amount', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['transaction_id', 'booking__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'used_count', 'max_uses', 'is_active', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at']


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['submitted_at']
    actions = ['approve_verifications', 'reject_verifications']
    
    def approve_verifications(self, request, queryset):
        from django.utils import timezone
        for verification in queryset:
            verification.status = 'approved'
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.user.profile.is_verified = True
            verification.user.profile.verified_badge = True
            verification.user.profile.save()
            verification.save()
    approve_verifications.short_description = "Approve selected verifications"
    
    def reject_verifications(self, request, queryset):
        queryset.update(status='rejected')
    reject_verifications.short_description = "Reject selected verifications"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'renter', 'vehicle_rating', 'owner_rating', 'created_at']
    list_filter = ['vehicle_rating', 'owner_rating', 'created_at']
    search_fields = ['renter__username', 'booking__vehicle__model']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SecurityDeposit)
class SecurityDepositAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'status', 'held_at', 'refunded_at']
    list_filter = ['status', 'held_at']
    search_fields = ['booking__user__username']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['booking', 'commission_amount', 'owner_earnings', 'paid_to_owner', 'created_at']
    list_filter = ['paid_to_owner', 'created_at']
    search_fields = ['booking__user__username', 'booking__vehicle__owner__username']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['booking', 'requested_by', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['booking__user__username']
    actions = ['approve_refunds', 'reject_refunds']
    
    def approve_refunds(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user)
    approve_refunds.short_description = "Approve selected refunds"
    
    def reject_refunds(self, request, queryset):
        queryset.update(status='rejected')
    reject_refunds.short_description = "Reject selected refunds"


admin.site.register(VehicleDocument)
admin.site.register(SavedVehicle)
admin.site.register(DamageReport)
admin.site.register(DamagePhoto)
admin.site.register(Message)
admin.site.register(RentalAgreement)
admin.site.register(DriversLicense)
admin.site.register(Blacklist)
admin.site.register(VehicleUtilization)
admin.site.register(PeakDemand)
admin.site.register(ReturnReminder)
admin.site.register(VehicleComparison)
admin.site.register(AvailabilityLock)
admin.site.register(AuditLog)
admin.site.register(PayoutRequest)
admin.site.register(Invoice)
admin.site.register(Referral)
admin.site.register(LoyaltyPoints)
admin.site.register(LoyaltyTransaction)