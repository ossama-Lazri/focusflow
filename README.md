# FocusFlow

Track focused work sessions. Built with Django, HTMX, and AlpineJS.

## Setup (WSL)

```bash
# Navigate to the project — adjust the path to match your Windows mount
cd /mnt/c/Users/ossam/OneDrive/Documents/side-projects/focusflow

# Create and activate a virtual environment
python3 -m venv focusflow-venv
source focusflow-venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and set a secret key
cp .env.example .env

# Run migrations
python manage.py migrate

# Start the dev server
python manage.py runserver
```

Open **http://127.0.0.1:8000/**

## Stack

- Django 5 · Django REST Framework · django-htmx
- HTMX 2 · AlpineJS 3 · Vanilla CSS
- SQLite
