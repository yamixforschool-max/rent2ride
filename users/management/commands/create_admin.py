from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@rent2rides.online', 'admin123123')
        else:
            user = User.objects.get(username='admin')
            user.set_password('admin123123')
            user.save()
        profile = user.profile
        profile.is_admin = True
        profile.is_owner = True
        profile.save()
        self.stdout.write('Admin ready.')
