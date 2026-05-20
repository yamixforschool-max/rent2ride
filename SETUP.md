# Quick Setup Guide

## Initial Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin account.

4. **Set Admin Status** (Optional)
   - After creating the superuser, go to Django admin panel: `http://localhost:8000/admin/`
   - Navigate to Users → User Profiles
   - Find your user and set `is_admin = True` to access the admin dashboard

5. **Configure PayMongo**
   - Edit `rent2ride/settings.py`
   - Replace `PAYMONGO_SECRET_KEY` and `PAYMONGO_PUBLIC_KEY` with your actual keys
   - Get keys from: https://paymongo.com

6. **Run Server**
   ```bash
   python manage.py runserver
   ```

## Testing the Application

1. **Create a Regular User (Renter)**
   - Go to `/signup/`
   - Fill in the form (don't check "Vehicle Owner")
   - Sign up and log in

2. **Create a Vehicle Owner**
   - Go to `/signup/`
   - Fill in the form and check "Vehicle Owner"
   - Sign up and log in
   - Go to Dashboard → Add Vehicle
   - Submit a vehicle for approval

3. **Approve Vehicle (as Admin)**
   - Log in as admin
   - Go to `/admin-dashboard/` or `/admin/vehicles/`
   - Approve the pending vehicle

4. **Book a Vehicle (as Renter)**
   - Log in as renter
   - Browse vehicles at `/vehicles/`
   - Select a vehicle and book it
   - Complete payment (PayMongo test mode)

## Important Notes

- **PayMongo Test Mode**: Use test keys for development
- **Email**: Password reset emails will print to console in development
- **Media Files**: Uploaded images will be stored in `/media/` directory
- **Database**: SQLite database file is `db.sqlite3`

## Common Issues

**Issue**: Template not found
- **Solution**: Ensure `templates/` directory is in the project root

**Issue**: Static files not loading
- **Solution**: Run `python manage.py collectstatic` (for production)

**Issue**: PayMongo payment not working
- **Solution**: Verify API keys and check PayMongo dashboard for API logs
