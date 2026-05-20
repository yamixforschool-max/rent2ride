"""
Management command to calculate late return penalties
Run daily: python manage.py calculate_late_penalties
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from vehicles.models import Booking


class Command(BaseCommand):
    help = 'Calculates late return penalties for overdue bookings'

    def handle(self, *args, **options):
        now = timezone.now()
        overdue_bookings = Booking.objects.filter(
            status='confirmed',
            end_date__lt=now,
            actual_return_date__isnull=True
        )
        
        PENALTY_PER_HOUR = Decimal('50.00')
        count = 0
        
        for booking in overdue_bookings:
            hours_late = (now - booking.end_date).total_seconds() / 3600
            if hours_late > 0:
                penalty = Decimal(str(hours_late)) * PENALTY_PER_HOUR
                booking.late_penalty = penalty
                booking.save()
                count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Booking #{booking.id}: {hours_late:.1f} hours late, penalty: ₱{penalty}'
                    )
                )
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Calculated penalties for {count} booking(s)')
            )
        else:
            self.stdout.write('No overdue bookings')
