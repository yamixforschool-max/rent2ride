# Rent2Ride - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python manage.py migrate
```

### 3. Create Admin User
```bash
python manage.py createsuperuser
```
Enter username, email, and password when prompted.

### 4. Configure PayMongo (Optional for Testing)
Edit `rent2ride/settings.py` and add your PayMongo API keys:
```python
PAYMONGO_SECRET_KEY = 'sk_test_your_key_here'
PAYMONGO_PUBLIC_KEY = 'pk_test_your_key_here'
```

### 5. Run the Server
```bash
python manage.py runserver
```

Visit: **http://localhost:8000**

## 📋 User Roles Setup

### Make a User an Admin
1. Go to: http://localhost:8000/admin/
2. Login with superuser credentials
3. Navigate to: **Users → User Profiles**
4. Find your user and check `is_admin` checkbox
5. Save

### Create a Vehicle Owner
1. Go to: http://localhost:8000/signup/
2. Fill the form and **check "Vehicle Owner"** checkbox
3. Sign up and login

### Create a Renter
1. Go to: http://localhost:8000/signup/
2. Fill the form **without** checking "Vehicle Owner"
3. Sign up and login

## 🎯 Testing the Flow

### As Vehicle Owner:
1. Login → Dashboard
2. Click "Add Vehicle"
3. Fill vehicle details and submit
4. Wait for admin approval

### As Admin:
1. Login → Admin Dashboard
2. Go to "Manage Vehicles"
3. Approve pending vehicles

### As Renter:
1. Login → Browse Vehicles
2. Select a vehicle → View Details
3. Click "Book Now"
4. Select dates and proceed to payment
5. Complete payment via PayMongo

## 🔑 Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home/Landing Page |
| `/vehicles/` | Browse All Vehicles |
| `/login/` | User Login |
| `/signup/` | User Registration |
| `/dashboard/` | User Dashboard |
| `/admin-dashboard/` | Admin Dashboard |
| `/admin/` | Django Admin Panel |

## ⚙️ Configuration

### Email Settings (Password Reset)
Currently set to console backend. To enable email:
1. Edit `rent2ride/settings.py`
2. Configure SMTP settings (see README.md)

### PayMongo URLs
Update success/cancel URLs in `vehicles/views.py` (create_paymongo_session function) for production.

## 🐛 Troubleshooting

**Static files not loading?**
- Run: `python manage.py collectstatic`

**Template errors?**
- Ensure `templates/` folder is in project root
- Check `TEMPLATES` setting in `settings.py`

**Database errors?**
- Run: `python manage.py makemigrations`
- Then: `python manage.py migrate`

**PayMongo not working?**
- Verify API keys are correct
- Check PayMongo dashboard for API logs
- Ensure success/cancel URLs are accessible

## 📚 Next Steps

- Read `README.md` for detailed documentation
- Read `SETUP.md` for comprehensive setup guide
- Customize templates in `templates/` folder
- Add more features as needed!

Happy Coding! 🎉
