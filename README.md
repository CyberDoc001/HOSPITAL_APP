# NUAM CARE — Hospital Management

This repository contains the NUAM CARE Django application. Below are quick instructions to push to GitHub and deploy to PythonAnywhere.

## Prepare repository for GitHub

1. Initialize git (if not already):

```bash
cd /home/cyberdoc/Documents/HOSPITAL_APP
git init
git add .
git commit -m "Initial commit: NUAM CARE hospital app"
# create repo on GitHub and add remote, for example:
git remote add origin git@github.com:<your-username>/nuam-care.git
git push -u origin main
```

2. Ensure you do NOT commit sensitive files like `.env` (we added `.gitignore` to help).

## Requirements

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Deploy to PythonAnywhere (quick guide)

1. Create an account and log in to PythonAnywhere.
2. Open the **Files** tab and clone your GitHub repo into your home directory, or upload your code.
3. Create a virtualenv (pick a Python version available on PythonAnywhere, e.g. 3.11):

```bash
python3.11 -m venv --clear ~/venv/nuamcare
source ~/venv/nuamcare/bin/activate
pip install -r /home/yourusername/nuam-care/requirements.txt
```

4. In the **Web** tab on PythonAnywhere:
   - Set the source code path to your project directory (where `manage.py` lives).
   - Configure the virtualenv path to the one you created.
   - Edit the WSGI configuration file to point to your Django app. Example wsgi snippet (edit paths):

```python
import os
import sys
path = '/home/yourusername/nuam-care'
if path not in sys.path:
    sys.path.insert(0, path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'nuam_project.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. Static files: run `collectstatic` once and map the `/static/` URL in the Web tab to the `static` folder created by `collectstatic`.

```bash
source ~/venv/nuamcare/bin/activate
cd /home/yourusername/nuam-care
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

6. Environment variables and secrets:
   - Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `ALLOWED_HOSTS` in the PythonAnywhere **Web** tab (or use a `.env` file and load it in `settings.py`).

7. Reload the web app from the PythonAnywhere **Web** tab.

## Notes
- If you plan to use PostgreSQL on production, update `DATABASES` in `nuam_project/settings.py` and ensure `psycopg[binary]` is installed.
- For static file efficiency, `whitenoise` is included in `requirements.txt`. On PythonAnywhere you can also use the built-in static mapping.

If you'd like, I can (1) create a GitHub remote and push, and (2) run the exact commands to prepare a PythonAnywhere-friendly WSGI file and instructions customized to your username. Which would you prefer me to do next?
# NUAM - Hospital Patient Management System

NUAM is a professional Django-based hospital patient management web application built with Python, HTML, CSS, and PostgreSQL.

## Features

- Patient profiles with contact, demographics, and primary physician assignment
- Appointment scheduling and tracking
- Medical records management
- Dashboard with metrics for patients and appointments
- PostgreSQL-ready settings with environment variable configuration

## Setup

1. Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the repository root or copy `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials. If you already created `nuam_database` and granted all privileges to `nuam_user`, set `DATABASE_PASSWORD=nuam@23` in your `.env` file.

If you still need to create the database and user locally, use the provided SQL script or run these commands:

```bash
sudo -u postgres psql -c "CREATE DATABASE nuam_database;"
sudo -u postgres psql -c "CREATE USER nuam_user WITH PASSWORD 'nuam@23';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nuam_database TO nuam_user;"
```

Alternatively, run the schema script:

```bash
psql -f database/nuam_database_schema.sql
```

NUAM requires PostgreSQL and will not use SQLite. Ensure the Postgres database and user match your `.env` settings before running migrations.

Then run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

## Future Improvements

- User authentication with role-based access (admin, doctor, nurse, receptionist)
- Patient portal for appointment requests and prescription history
- Billing, invoicing, and insurance claim tracking
- Pharmacy inventory and lab result integration
- REST API endpoints for mobile and external system integration
- Audit logs, notifications, and appointment reminders
