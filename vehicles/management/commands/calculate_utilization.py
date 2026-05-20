from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from vehicles.models import Vehicle, Booking, VehicleUtilization
from django.db.models import Count, Sum, Q


class Command(BaseCommand):
    help = 'Calculate vehicle utilization metrics for the current month'

    def handle(self, *args, **options):
        # Get current month
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Get all available vehicles
        vehicles = Vehicle.objects.filter(status='available')
        
        count = 0
        for vehicle in vehicles:
            # Get bookings for this month
            bookings = Booking.objects.filter(
                vehicle=vehicle,
                status='completed',
                start_date__gte=month_start,
                end_date__lte=today
            )
            
            # Calculate days rented
            days_rented = 0
            total_revenue = 0
            for booking in bookings:
                days = (booking.end_date.date() - booking.start_date.date()).days + 1
                days_rented += days
                total_revenue += float(booking.total_price)
            
            # Calculate utilization percentage
            days_in_month = today.day
            utilization_percentage = (days_rented / days_in_month * 100) if days_in_month > 0 else 0
            idle_days = days_in_month - days_rented
            
            # Suggest price adjustment based on utilization
            suggested_price = None
            if utilization_percentage < 30:
                # Low utilization - suggest lower price
                suggested_price = vehicle.price_per_day * Decimal('0.90')  # 10% reduction
            elif utilization_percentage > 80:
                # High utilization - suggest higher price
                suggested_price = vehicle.price_per_day * Decimal('1.10')  # 10% increase
            
            # Create or update utilization record
            VehicleUtilization.objects.update_or_create(
                vehicle=vehicle,
                month=month_start,
                defaults={
                    'days_rented': days_rented,
                    'total_revenue': total_revenue,
                    'utilization_percentage': utilization_percentage,
                    'idle_days': idle_days,
                    'suggested_price': suggested_price,
                }
            )
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully calculated utilization for {count} vehicles.')
        )
