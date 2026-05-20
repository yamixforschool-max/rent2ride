# Deployment Checklist

Use this checklist before deploying Rent2Ride to production.

## Pre-Deployment

### 1. Security Settings
- [ ] Change `SECRET_KEY` in `settings.py`
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Enable HTTPS/SSL
- [ ] Set secure cookie settings:
  ```python
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_SSL_REDIRECT = True
  ```

### 2. Database
- [ ] Migrate to production database (PostgreSQL recommended)
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Backup database

### 3. Static Files
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Configure static file serving (nginx/Apache or cloud storage)
- [ ] Configure media file serving

### 4. Environment Variables
- [ ] Set PayMongo production keys
- [ ] Configure email settings
- [ ] Set database credentials
- [ ] Configure any API keys

### 5. Dependencies
- [ ] Install all requirements: `pip install -r requirements.txt`
- [ ] Verify all packages are installed
- [ ] Check for security updates

## Feature-Specific Setup

### 6. PDF Generation
- [ ] Verify `reportlab` is installed
- [ ] Test PDF generation for agreements and invoices
- [ ] Configure PDF storage path

### 7. Email Configuration
- [ ] Configure SMTP settings in `settings.py`
- [ ] Test email sending
- [ ] Set up email templates (optional)
- [ ] Configure `DEFAULT_FROM_EMAIL`

### 8. Automation Setup
- [ ] Set up cron jobs (Linux/Mac) or Task Scheduler (Windows)
- [ ] Test all management commands manually
- [ ] Configure log file locations
- [ ] Set up monitoring for automated tasks

### 9. File Storage
- [ ] Configure media file storage
- [ ] Set up cloud storage (AWS S3, etc.) if needed
- [ ] Configure file upload limits
- [ ] Test file uploads

## Post-Deployment

### 10. Testing
- [ ] Test user registration
- [ ] Test vehicle listing
- [ ] Test booking flow (end-to-end)
- [ ] Test payment integration
- [ ] Test driver's license upload
- [ ] Test rental agreement signing
- [ ] Test PDF generation
- [ ] Test email notifications
- [ ] Test admin features

### 11. Monitoring
- [ ] Set up error logging
- [ ] Configure log rotation
- [ ] Set up uptime monitoring
- [ ] Configure backup schedule

### 12. Performance
- [ ] Enable caching (Redis/Memcached)
- [ ] Optimize database queries
- [ ] Set up CDN for static files
- [ ] Configure gzip compression

## Production Settings Template

Create a `settings_production.py`:

```python
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rent2ride_db',
        'USER': 'db_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'Rent2Ride <noreply@rent2ride.com>'

# PayMongo Production Keys
PAYMONGO_SECRET_KEY = 'sk_live_...'
PAYMONGO_PUBLIC_KEY = 'pk_live_...'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/rent2ride/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

## Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Create superuser
python manage.py createsuperuser

# 5. Test server
python manage.py runserver

# 6. Test management commands
python manage.py expire_bookings
python manage.py check_license_expiration
python manage.py send_return_reminders
```

## Common Issues

1. **Static files not loading**: Run `collectstatic` and check `STATIC_ROOT`
2. **Media files not accessible**: Check `MEDIA_ROOT` and URL configuration
3. **Email not sending**: Verify SMTP credentials
4. **PDF generation fails**: Ensure `reportlab` is installed
5. **Cron jobs not running**: Check file paths and permissions

## Support

For issues or questions, refer to:
- Django documentation: https://docs.djangoproject.com/
- ReportLab documentation: https://www.reportlab.com/docs/
- PayMongo documentation: https://developers.paymongo.com/
