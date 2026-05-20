from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from vehicles.models import Booking, ReturnReminder
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send return reminders 24 hours before booking end date'

    def handle(self, *args, **options):
        # Get bookings ending in 24 hours
        reminder_time = timezone.now() + timedelta(hours=24)
        bookings = Booking.objects.filter(
            status='confirmed',
            end_date__lte=reminder_time,
            end_date__gte=timezone.now()
        )
        
        count = 0
        for booking in bookings:
            # Check if reminder already sent
            if not ReturnReminder.objects.filter(
                booking=booking,
                reminder_type='24h',
                is_sent=True
            ).exists():
                # Create reminder record
                reminder = ReturnReminder.objects.create(
                    booking=booking,
                    reminder_type='24h',
                    sent_via='email',
                    is_sent=True
                )
                
                # Send email (if email backend configured)
                try:
                    send_mail(
                        subject=f'Return Reminder - Booking #{booking.id}',
                        message=f'''
Hello {booking.user.get_full_name() or booking.user.username},

This is a reminder that your rental period for {booking.vehicle.brand} {booking.vehicle.model} 
is ending soon.

Return Date: {booking.end_date.strftime("%B %d, %Y at %I:%M %p")}

Please return the vehicle on time to avoid late penalties.

Thank you,
Rent2Ride Team
                        ''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[booking.user.email],
                        fail_silently=True,
                    )
                    count += 1
                except:
                    pass  # Email sending failed, but reminder is recorded
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {count} return reminders.')
        )
