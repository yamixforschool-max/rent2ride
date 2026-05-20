"""
Management command to expire unpaid bookings
Run this via cron job every 5 minutes: python manage.py expire_bookings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from vehicles.models import Booking, AvailabilityLock


class Command(BaseCommand):
    help = 'Expires unpaid bookings that have passed their expiration time'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_bookings = Booking.objects.filter(
            status='pending',
            payment_status='pending',
            expires_at__lt=now
        )
        
        count = expired_bookings.count()
        
        for booking in expired_bookings:
            booking.status = 'expired'
            booking.payment_status = 'failed'
            booking.is_locked = False
            booking.save()
            
            # Remove availability locks
            AvailabilityLock.objects.filter(booking=booking).update(is_active=False)
            
            # Restore vehicle availability
            active_locks = AvailabilityLock.objects.filter(
                vehicle=booking.vehicle,
                is_active=True
            ).exists()
            if not active_locks:
                booking.vehicle.status = 'available'
                booking.vehicle.save()
            
            self.stdout.write(
                self.style.WARNING(f'Expired booking #{booking.id} for {booking.user.username}')
            )
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {count} booking(s)')
            )
        else:
            self.stdout.write('No bookings to expire')
