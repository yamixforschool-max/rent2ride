# Automation Setup Guide

This guide explains how to set up automated tasks for Rent2Ride using cron jobs (Linux/Mac) or Task Scheduler (Windows).

## Management Commands

The following management commands are available for automation:

### 1. Expire Unpaid Bookings
**Command**: `python manage.py expire_bookings`  
**Frequency**: Every 5 minutes  
**Purpose**: Automatically cancels bookings that haven't been paid within 15 minutes

### 2. Check License Expiration
**Command**: `python manage.py check_license_expiration`  
**Frequency**: Daily (at midnight)  
**Purpose**: Checks and updates expired driver's licenses

### 3. Send Return Reminders
**Command**: `python manage.py send_return_reminders`  
**Frequency**: Daily (at 9 AM)  
**Purpose**: Sends email reminders 24 hours before vehicle return date

### 4. Calculate Vehicle Utilization
**Command**: `python manage.py calculate_utilization`  
**Frequency**: Monthly (1st of each month)  
**Purpose**: Calculates utilization metrics for all vehicles

### 5. Unlock Expired Availability
**Command**: `python manage.py unlock_expired_availability`  
**Frequency**: Every 15 minutes  
**Purpose**: Unlocks vehicles with expired availability locks

### 6. Expire Loyalty Points
**Command**: `python manage.py expire_loyalty_points`  
**Frequency**: Daily (at midnight)  
**Purpose**: Expires loyalty points that have passed their expiration date

## Linux/Mac Setup (Cron)

### Step 1: Open Crontab
```bash
crontab -e
```

### Step 2: Add Cron Jobs
Add the following lines (adjust the path to your project):

```bash
# Expire unpaid bookings every 5 minutes
*/5 * * * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py expire_bookings >> /var/log/rent2ride_expire.log 2>&1

# Unlock expired availability every 15 minutes
*/15 * * * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py unlock_expired_availability >> /var/log/rent2ride_unlock.log 2>&1

# Check license expiration daily at midnight
0 0 * * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py check_license_expiration >> /var/log/rent2ride_license.log 2>&1

# Send return reminders daily at 9 AM
0 9 * * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py send_return_reminders >> /var/log/rent2ride_reminders.log 2>&1

# Expire loyalty points daily at midnight
0 0 * * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py expire_loyalty_points >> /var/log/rent2ride_points.log 2>&1

# Calculate utilization monthly on the 1st
0 0 1 * * cd /path/to/RENT2RIDE && /usr/bin/python3 manage.py calculate_utilization >> /var/log/rent2ride_utilization.log 2>&1
```

### Step 3: Save and Exit
Save the file and exit. Cron will automatically reload the configuration.

### Step 4: Verify
Check if cron jobs are scheduled:
```bash
crontab -l
```

## Windows Setup (Task Scheduler)

### Step 1: Open Task Scheduler
1. Press `Win + R`, type `taskschd.msc`, and press Enter
2. Click "Create Basic Task" in the right panel

### Step 2: Create Tasks for Each Command

#### Task 1: Expire Bookings (Every 5 minutes)
1. **Name**: Rent2Ride - Expire Bookings
2. **Trigger**: Daily, repeat every 5 minutes
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe` (or your Python path)
5. **Arguments**: `manage.py expire_bookings`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

#### Task 2: Unlock Availability (Every 15 minutes)
1. **Name**: Rent2Ride - Unlock Availability
2. **Trigger**: Daily, repeat every 15 minutes
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe`
5. **Arguments**: `manage.py unlock_expired_availability`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

#### Task 3: Check License Expiration (Daily at midnight)
1. **Name**: Rent2Ride - Check License Expiration
2. **Trigger**: Daily at 12:00 AM
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe`
5. **Arguments**: `manage.py check_license_expiration`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

#### Task 4: Send Return Reminders (Daily at 9 AM)
1. **Name**: Rent2Ride - Send Return Reminders
2. **Trigger**: Daily at 9:00 AM
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe`
5. **Arguments**: `manage.py send_return_reminders`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

#### Task 5: Expire Loyalty Points (Daily at midnight)
1. **Name**: Rent2Ride - Expire Loyalty Points
2. **Trigger**: Daily at 12:00 AM
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe`
5. **Arguments**: `manage.py expire_loyalty_points`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

#### Task 6: Calculate Utilization (Monthly on 1st)
1. **Name**: Rent2Ride - Calculate Utilization
2. **Trigger**: Monthly on day 1 at 12:00 AM
3. **Action**: Start a program
4. **Program**: `C:\Python\python.exe`
5. **Arguments**: `manage.py calculate_utilization`
6. **Start in**: `C:\Users\Jethro Arrubio\RENT2RIDE`

## Alternative: Using Django-Q or Celery

For more advanced task scheduling, you can use Django-Q or Celery:

### Django-Q Setup
```bash
pip install django-q2
```

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'django_q',
]
```

Configure in `settings.py`:
```python
Q_CLUSTER = {
    'name': 'rent2ride',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}
```

## Testing Commands

Test each command manually before setting up automation:

```bash
# Test expire bookings
python manage.py expire_bookings

# Test license expiration
python manage.py check_license_expiration

# Test return reminders
python manage.py send_return_reminders

# Test utilization calculation
python manage.py calculate_utilization

# Test unlock availability
python manage.py unlock_expired_availability

# Test expire loyalty points
python manage.py expire_loyalty_points
```

## Email Configuration

For return reminders to work, configure email settings in `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = 'Rent2Ride <noreply@rent2ride.com>'
```

**Note**: For Gmail, you need to use an App Password, not your regular password.

## Monitoring

Check logs regularly to ensure commands are running:
- Linux/Mac: Check `/var/log/rent2ride_*.log`
- Windows: Check Task Scheduler history
- Or add logging to Django settings

## Troubleshooting

1. **Commands not running**: Check file paths and Python executable path
2. **Permission errors**: Ensure the user running cron/tasks has proper permissions
3. **Email not sending**: Verify email configuration in settings.py
4. **Database errors**: Ensure database is accessible and migrations are applied
