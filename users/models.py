from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with additional fields"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Identity verification status
    verified_badge = models.BooleanField(default=False)  # Display verified badge
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fraud prevention fields
    daily_booking_count = models.PositiveIntegerField(default=0)
    last_booking_date = models.DateField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {'Owner' if self.is_owner else 'Renter'}"
    
    @property
    def average_rating(self):
        """Calculate average rating as owner"""
        from vehicles.models import Rating
        ratings = Rating.objects.filter(booking__vehicle__owner=self.user, owner_rating__isnull=False)
        if ratings.exists():
            return sum(r.owner_rating for r in ratings) / ratings.count()
        return None

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        if hasattr(instance, 'profile'):
            instance.profile.save()
