from django.core.management.base import BaseCommand
from django.utils import timezone
from vehicles.models import LoyaltyPoints, LoyaltyTransaction


class Command(BaseCommand):
    help = 'Expire loyalty points that have passed their expiration date'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_transactions = LoyaltyTransaction.objects.filter(
            transaction_type='earned',
            expires_at__lt=now,
            points__gt=0
        )
        
        count = 0
        total_expired = 0
        
        for transaction in expired_transactions:
            if transaction.points > 0:
                # Update user's loyalty points
                points, created = LoyaltyPoints.objects.get_or_create(user=transaction.user)
                points.expired_points += transaction.points
                points.save()
                
                # Mark transaction as expired
                transaction.transaction_type = 'expired'
                transaction.points = 0
                transaction.save()
                
                # Create expiration transaction
                LoyaltyTransaction.objects.create(
                    user=transaction.user,
                    transaction_type='expired',
                    points=transaction.points,
                    description=f'Points expired from booking #{transaction.booking.id if transaction.booking else "N/A"}',
                )
                
                total_expired += transaction.points
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully expired {total_expired} points from {count} transactions.')
        )
