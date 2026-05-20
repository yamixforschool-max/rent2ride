# Rent2Ride - Vehicle Rental Platform

A comprehensive web-based vehicle rental platform where users can search, book, and rent vehicles directly from vehicle owners.

## Features

- **User Authentication**: Sign up, login, logout, and password reset functionality
- **Vehicle Listings**: Browse and search vehicles by location, type, and price
- **Booking System**: Book vehicles with date/time selection and automatic price calculation
- **Payment Integration**: PayMongo payment gateway integration for secure transactions
- **User Roles**: 
  - **Renters**: Search and book vehicles
  - **Vehicle Owners**: List and manage their vehicles
  - **Admins**: Full platform management capabilities
- **Admin Dashboard**: Manage users, vehicles, bookings, and payments
- **Responsive Design**: Bootstrap 5 for modern, mobile-friendly UI

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (default)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Payment**: PayMongo API
- **Image Handling**: Pillow

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Navigate to Project Directory

```bash
cd RENT2RIDE
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account. After creation, you can:
- Access the admin panel at `http://localhost:8000/admin/`
- Set `is_admin=True` in the UserProfile for admin dashboard access

### Step 5: Configure PayMongo

1. Sign up for a PayMongo account at https://paymongo.com
2. Get your API keys (Secret Key and Public Key)
3. Open `rent2ride/settings.py`
4. Update the PayMongo settings:

```python
PAYMONGO_SECRET_KEY = 'sk_test_your_actual_secret_key'
PAYMONGO_PUBLIC_KEY = 'pk_test_your_actual_public_key'
```

**Note**: Update the success and cancel URLs in `vehicles/views.py` (create_paymongo_session function) with your actual domain in production.

### Step 6: Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Project Structure

```
rent2ride/
├── manage.py
├── rent2ride/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── ...
├── users/
│   ├── models.py            # UserProfile model
│   ├── views.py             # Authentication views
│   ├── forms.py             # Signup and profile forms
│   └── urls.py              # User-related URLs
├── vehicles/
│   ├── models.py            # Vehicle, Booking, Payment models
│   ├── views.py             # Vehicle and booking views
│   ├── forms.py             # Vehicle and booking forms
│   └── urls.py              # Vehicle-related URLs
├── templates/               # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── vehicle_list.html
│   ├── booking.html
│   ├── admin_dashboard.html
│   └── ...
├── static/                  # Static files (CSS, JS, images)
│   ├── css/
│   └── js/
├── media/                   # User-uploaded files
└── requirements.txt         # Python dependencies
```

## Usage Guide

### For Renters

1. **Sign Up**: Create an account (don't check "Vehicle Owner")
2. **Browse Vehicles**: Use the search filters to find vehicles
3. **Book Vehicle**: Select dates and proceed to payment
4. **Complete Payment**: Redirected to PayMongo for secure payment
5. **View Bookings**: Check your dashboard for booking history

### For Vehicle Owners

1. **Sign Up**: Create an account and check "Vehicle Owner"
2. **Add Vehicle**: Go to Dashboard → Add Vehicle
3. **Wait for Approval**: Admin will review and approve your listing
4. **Manage Bookings**: View and manage bookings for your vehicles

### For Admins

1. **Access Admin Dashboard**: Navigate to `/admin-dashboard/`
2. **Manage Users**: View, block, or delete users
3. **Approve Vehicles**: Review and approve pending vehicle listings
4. **Manage Bookings**: Confirm or cancel bookings
5. **View Payments**: Monitor all payment transactions

## Key URLs

- Home: `/`
- Browse Vehicles: `/vehicles/`
- Login: `/login/`
- Sign Up: `/signup/`
- Dashboard: `/dashboard/`
- Admin Dashboard: `/admin-dashboard/`
- Admin Panel: `/admin/`

## Database Models

### UserProfile
- Extends Django's User model
- Fields: phone_number, is_owner, is_admin, profile_picture

### Vehicle
- Fields: owner, vehicle_type, model, brand, price_per_day, location, available_from, available_to, image_url, description, status

### Booking
- Fields: user, vehicle, start_date, end_date, total_price, status, payment_status

### Payment
- Fields: booking, transaction_id, payment_amount, payment_status, paymongo_session_id

## Payment Flow

1. User selects vehicle and dates
2. Booking is created with status "pending"
3. User is redirected to PayMongo payment page
4. On successful payment, booking status changes to "confirmed"
5. Payment record is created/updated

## Development Notes

- **Email Configuration**: Currently set to console backend for development. Configure SMTP settings in `settings.py` for production.
- **Static Files**: Run `python manage.py collectstatic` in production.
- **Media Files**: Ensure `media/` directory has proper permissions for file uploads.
- **Security**: Change `SECRET_KEY` in production and set `DEBUG=False`.

## Troubleshooting

### Migration Issues
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files Not Loading
```bash
python manage.py collectstatic
```

### PayMongo Integration Issues
- Verify API keys are correct
- Check that success/cancel URLs are accessible
- Review PayMongo API documentation for latest changes

## License

This project is created for educational purposes.

## Support

For issues or questions, please refer to the Django and PayMongo documentation.
