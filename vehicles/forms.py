from django import forms
from .models import (
    Vehicle, Booking, Rating, IdentityVerification, VehicleDocument, PromoCode, 
    DamageReport, Message, Refund, DriversLicense, Blacklist, PayoutRequest,
    RentalAgreement, Referral
)
from django.utils import timezone
from datetime import timedelta


class VehicleForm(forms.ModelForm):
    instant_booking = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = Vehicle
        fields = ['vehicle_type', 'model', 'brand', 'price_per_day', 'location', 
                  'seats', 'fuel_type', 'transmission_type',
                  'available_from', 'available_to', 'image_url', 'description', 'instant_booking']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50'}),
            'fuel_type': forms.Select(attrs={'class': 'form-control'}),
            'transmission_type': forms.Select(attrs={'class': 'form-control'}),
            'available_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'available_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'image_url': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class VehicleDocumentForm(forms.ModelForm):
    class Meta:
        model = VehicleDocument
        fields = ['document_type', 'document_file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BookingForm(forms.ModelForm):
    promo_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter promo code (optional)'}))
    payment_type = forms.ChoiceField(choices=[('full', 'Full Payment'), ('deposit', 'Deposit Only')], widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    include_insurance = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'payment_type']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['vehicle_rating', 'owner_rating', 'vehicle_review', 'owner_review']
        widgets = {
            'vehicle_rating': forms.Select(choices=Rating.RATING_CHOICES, attrs={'class': 'form-control'}),
            'owner_rating': forms.Select(choices=Rating.RATING_CHOICES, attrs={'class': 'form-control'}),
            'vehicle_review': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience with this vehicle...'}),
            'owner_review': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience with the owner...'}),
        }


class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ['id_document']
        widgets = {
            'id_document': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
        }


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = ['code', 'discount_type', 'discount_value', 'max_uses', 'valid_from', 'valid_until', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PROMO2024'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DamageReportForm(forms.ModelForm):
    # Note: Multiple file uploads are handled in the view, not in the form widget
    photos = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    
    class Meta:
        model = DamageReport
        fields = ['description', 'estimated_cost']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the damage in detail...'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message subject (optional)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Type your message here...'}),
        }


class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['reason', 'amount']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Please explain why you need a refund...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
        }


# New Feature Forms
class DriversLicenseForm(forms.ModelForm):
    class Meta:
        model = DriversLicense
        fields = ['license_number', 'expiration_date', 'license_image_front', 'license_image_back']
        widgets = {
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter license number'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'license_image_front': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'license_image_back': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class BlacklistForm(forms.ModelForm):
    class Meta:
        model = Blacklist
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter reason for blacklisting...'}),
        }


class PayoutRequestForm(forms.ModelForm):
    class Meta:
        model = PayoutRequest
        fields = ['amount', 'payment_method', 'payment_details']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bank Transfer, PayPal'}),
            'payment_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Account number, email, etc.'}),
        }


class RentalAgreementSignatureForm(forms.Form):
    """Form for e-signature"""
    signature = forms.CharField(widget=forms.HiddenInput())
    agreed_to_terms = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class ReferralForm(forms.Form):
    """Form for referral code entry"""
    referral_code = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter referral code'}))
