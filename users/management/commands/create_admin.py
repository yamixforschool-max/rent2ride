from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@rent2rides.online', 'admin123123')
            self.stdout.write('Admin created.')
        else:
            self.stdout.write('Admin already exists.')
