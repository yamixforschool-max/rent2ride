from django.core.management.base import BaseCommand
from django.utils import timezone
from vehicles.models import DriversLicense, Booking
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Check and update expired driver licenses, send reminders'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired_licenses = DriversLicense.objects.filter(
            expiration_date__lt=today,
            status='verified'
        )
        
        count = 0
        for license in expired_licenses:
            license.status = 'expired'
            license.save()
            count += 1
            
            # Update bookings to require new license
            Booking.objects.filter(
                user=license.user,
                status='pending',
                license_verified=True
            ).update(license_verified=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {count} expired licenses.')
        )
