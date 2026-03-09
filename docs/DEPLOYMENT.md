# Deployment Guide

Instructions for deploying Django Delights across different environments.

> **AI Disclosure:** This documentation was generated with the assistance of AI tools and reviewed by the project author.

---

## Table of Contents

- [Environment Variables](#environment-variables)
- [Docker (Development)](#docker-development)
- [Docker (Production)](#docker-production)
- [Railway](#railway)
- [Manual Deployment (VPS)](#manual-deployment-vps)
- [Production Checklist](#production-checklist)

---

## Environment Variables

All configuration is managed through a `.env` file. Copy `.env.example` as a starting point:

```bash
cp .env.example .env
```

### Core Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `SECRET_KEY` | Django secret key | **Yes** (production) | Insecure key in dev |
| `DEBUG` | Debug mode | No | `True` (dev) / `False` (prod) |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | **Yes** (production) | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL | No | SQLite local |
| `DJANGO_ENV` | Environment: `dev` or `prod` | No | `dev` |

### Business Variables

| Variable | Description | Default |
|---|---|---|
| `GLOBAL_MARGIN` | Pricing margin (0.20 = 20%) | `0.20` |
| `LOW_STOCK_THRESHOLD` | Low-stock alert threshold | `10` |

### JWT Variables

| Variable | Description | Default |
|---|---|---|
| `JWT_ACCESS_TOKEN_LIFETIME` | Access token lifetime (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh token lifetime (days) | `7` |

### CORS Variables

| Variable | Description | Default |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:3000` |

### Database Variables (Alternative to DATABASE_URL)

If not using `DATABASE_URL`, you can configure PostgreSQL with individual variables:

| Variable | Description | Default |
|---|---|---|
| `DB_ENGINE` | Database engine | `django.db.backends.postgresql` |
| `DB_NAME` | Database name | `django_delights` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | — |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

### Production Variables

| Variable | Description | Default |
|---|---|---|
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `True` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | — |
| `REDIS_URL` | Redis URL (for cache and sessions) | — |
| `LOG_LEVEL` | Logging level | `INFO` |

### Email Variables (Optional)

| Variable | Description |
|---|---|
| `EMAIL_HOST` | SMTP server |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_USE_TLS` | Use TLS |
| `EMAIL_HOST_USER` | SMTP user |
| `EMAIL_HOST_PASSWORD` | SMTP password |

### Generate a SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Docker (Development)

The development Docker environment automatically starts:

- **Web**: Django development server with hot-reload
- **PostgreSQL 15**: Database
- **Redis 7**: Cache (optional)
- **Mailhog**: Email capture for testing

### Start the Environment

```bash
# Start all services
docker-compose up

# Start in the background
docker-compose up -d

# View logs
docker-compose logs -f web
```

The `docker-compose.override.yml` file is applied automatically and configures:
- Uses `Dockerfile.dev` instead of production
- Mounts source code for hot-reload
- Django development server (`runserver`)
- Exposed ports for PostgreSQL (5432) and Redis (6379)
- Mailhog on ports 1025 (SMTP) and 8025 (Web UI)

### Useful Commands

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run tests
docker-compose exec web pytest

# Open Django shell
docker-compose exec web python manage.py shell

# Stop all services
docker-compose down

# Stop and remove volumes (resets database)
docker-compose down -v
```

---

## Docker (Production)

The production image uses an optimized multi-stage build:

- **Stage 1 (builder)**: Compiles dependencies as wheels
- **Stage 2 (production)**: Final slim image with only runtime dependencies

### Production Image Features

- Based on `python:3.12-slim`
- Non-root user (`appuser`) for security
- Gunicorn with 4 workers and threads
- WhiteNoise for serving static files
- Built-in health check
- Static files collected automatically (`collectstatic`)

### Manual Build and Run

```bash
# Build the image
docker build -t django-delights:latest .

# Run with an environment file
docker run -d \
  --name django-delights \
  --env-file .env.production \
  -p 8000:8000 \
  django-delights:latest
```

### Production with Docker Compose

For a full production environment with Nginx as reverse proxy:

```bash
# Base services only (no development override)
docker-compose -f docker-compose.yml up --build -d

# With Nginx (production profile)
docker-compose -f docker-compose.yml --profile production up --build -d
```

The production `docker-compose.yml` includes:
- Health checks for all services
- Automatic restart (`unless-stopped`)
- Isolated network (`django-delights-network`)
- Persistent volumes for PostgreSQL, Redis, and static files
- Database initialization script (`scripts/init-db.sql`)

### Required Production Variables

Make sure to set these before deploying:

```env
SECRET_KEY=<generated-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgres://user:password@db:5432/django_delights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=django_delights
```

---

## Railway

The project includes configuration for deployment on [Railway](https://railway.app/).

### Configuration File

The `railway.toml` file defines:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn django_delights.wsgi:application --bind 0.0.0.0:$PORT"
healthcheckPath = "/api/v1/health/"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 5
```

### Deployment Steps

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Log in
railway login

# 3. Initialize project
railway init

# 4. Add a PostgreSQL service from the Railway dashboard

# 5. Set environment variables
railway variables set SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
railway variables set DJANGO_ENV=prod
railway variables set ALLOWED_HOSTS=your-app.railway.app
railway variables set DJANGO_SETTINGS_MODULE=django_delights.settings.prod

# 6. Deploy
railway up
```

Railway automatically provides the `DATABASE_URL` variable when you add a PostgreSQL service.

---

## Manual Deployment (VPS)

For deploying on a Linux server (Ubuntu/Debian):

### 1. Prepare the Server

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.12 python3.12-venv python3-pip postgresql nginx -y
```

### 2. Configure PostgreSQL

```bash
sudo -u postgres psql -c "CREATE DATABASE django_delights;"
sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'secure-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE django_delights TO app_user;"
```

### 3. Set Up the Application

```bash
# Clone repository
git clone https://github.com/yourusername/django-delights.git /opt/django-delights
cd /opt/django-delights

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Migrations and static files
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. Configure Gunicorn as a Service

Create `/etc/systemd/system/django-delights.service`:

```ini
[Unit]
Description=Django Delights Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/django-delights
EnvironmentFile=/opt/django-delights/.env
ExecStart=/opt/django-delights/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --threads 2 \
    django_delights.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable django-delights
sudo systemctl start django-delights
```

### 5. Configure Nginx

Create `/etc/nginx/sites-available/django-delights`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /opt/django-delights/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/django-delights /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Production Checklist

Before deploying to production, verify:

- [ ] `SECRET_KEY` generated and configured (do not use the development key)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` set with your domain
- [ ] PostgreSQL database configured and accessible
- [ ] `python manage.py migrate` executed
- [ ] `python manage.py collectstatic` executed
- [ ] Superuser created
- [ ] HTTPS configured (SSL certificate)
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] CORS variables set correctly
- [ ] Health check accessible at `/api/v1/health/`
- [ ] Logging configured and accessible
- [ ] Database backups scheduled
