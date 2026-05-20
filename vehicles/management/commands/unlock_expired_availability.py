from django.core.management.base import BaseCommand
from django.utils import timezone
from vehicles.models import AvailabilityLock, Vehicle


class Command(BaseCommand):
    help = 'Unlock vehicles with expired availability locks'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_locks = AvailabilityLock.objects.filter(
            expires_at__lt=now,
            is_active=True
        )
        
        count = 0
        for lock in expired_locks:
            lock.is_active = False
            lock.save()
            
            # Restore vehicle availability if no active locks
            active_locks = AvailabilityLock.objects.filter(
                vehicle=lock.vehicle,
                is_active=True
            ).exists()
            
            if not active_locks:
                # Check if vehicle has any confirmed bookings
                has_bookings = Booking.objects.filter(
                    vehicle=lock.vehicle,
                    status__in=['pending', 'confirmed']
                ).exists()
                
                if not has_bookings:
                    lock.vehicle.status = 'available'
                    lock.vehicle.save()
            
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully unlocked {count} vehicles.')
        )
