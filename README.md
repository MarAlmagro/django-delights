# Django Delights

[![CI](https://github.com/yourusername/django-delights/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/django-delights/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/django-delights/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/django-delights)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready restaurant inventory and ordering management system built with Django 5.2, featuring REST API with JWT authentication, Docker support, and comprehensive testing.

## Features

### Core Functionality
- **Inventory Management**: Track ingredients with units, prices, and quantities
- **Menu Items (Dishes)**: Create dishes with recipe requirements and auto-calculated costs
- **Composite Menus**: Bundle multiple dishes with combined pricing
- **Purchase Workflow**: 3-step atomic purchase flow with inventory deduction
- **Admin Dashboard**: Revenue, cost, profit metrics, top-selling items, low-stock alerts

### Technical Highlights
- **REST API**: Full CRUD API with Django REST Framework
- **JWT Authentication**: Secure token-based authentication
- **Swagger/OpenAPI**: Interactive API documentation
- **Role-Based Access**: Admin and Staff permission levels
- **Atomic Transactions**: Row-level locking prevents race conditions
- **Docker Ready**: Multi-stage builds for production deployment
- **CI/CD**: GitHub Actions with testing, linting, and security scans
- **80%+ Test Coverage**: Comprehensive unit, view, and integration tests

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 5.2 |
| API | Django REST Framework |
| Auth | JWT (SimpleJWT) |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Testing | pytest, pytest-django, factory-boy |
| Code Quality | black, flake8, isort, mypy |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Documentation | drf-spectacular (OpenAPI 3) |

## Quick Start

### Prerequisites
- Python 3.11+
- pip or pipx

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/django-delights.git
cd django-delights

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python manage.py loaddata units ingredients dishes menus users

# Start development server
python manage.py runserver
```

### Access Points
- **Web Application**: http://localhost:8000/
- **Django Admin**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **API (v1)**: http://localhost:8000/api/v1/

### Default Fixture Users
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser |
| staff | staff123 | Staff |

## Docker Development

```bash
# Development mode (with hot reload)
docker-compose up

# Production-like environment
docker-compose -f docker-compose.yml up --build

# Run migrations in container
docker-compose exec web python manage.py migrate
```

## API Usage

### Authentication

```bash
# Get JWT tokens
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access": "...", "refresh": "..."}

# Use access token
curl http://localhost:8000/api/v1/dishes/ \
  -H "Authorization: Bearer <access_token>"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -d '{"refresh": "<refresh_token>"}'
```

### API Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/v1/units/` | GET, POST | Units management (admin) |
| `/api/v1/ingredients/` | GET, POST, PUT, PATCH | Ingredient CRUD |
| `/api/v1/ingredients/{id}/adjust/` | POST | Adjust inventory |
| `/api/v1/dishes/` | GET, POST, PUT, PATCH | Dish CRUD |
| `/api/v1/dishes/available/` | GET | Available dishes only |
| `/api/v1/menus/` | GET, POST, PUT, PATCH | Menu CRUD |
| `/api/v1/purchases/` | GET, POST | Purchase orders |
| `/api/v1/dashboard/` | GET | Analytics (admin only) |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=delights --cov-report=html

# Run specific test file
pytest delights/tests/test_models.py -v

# Run integration tests only
pytest -m integration
```

## Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run all checks manually
pre-commit run --all-files

# Format code
black .

# Sort imports
isort .

# Lint
flake8 .

# Type check
mypy delights/
```

## Project Structure

```
django-delights/
├── delights/                   # Main application
│   ├── api/                    # REST API
│   │   ├── serializers.py      # DRF serializers
│   │   ├── views.py            # API viewsets
│   │   ├── urls.py             # API routing
│   │   └── permissions.py      # Custom permissions
│   ├── tests/                  # Test suite
│   │   ├── conftest.py         # Pytest fixtures
│   │   ├── factories.py        # Factory Boy factories
│   │   ├── test_models.py      # Model tests
│   │   ├── test_views.py       # View tests
│   │   └── test_integration.py # Integration tests
│   ├── models.py               # Data models
│   ├── views.py                # Web views
│   ├── forms.py                # Django forms
│   └── admin.py                # Admin configuration
├── django_delights/            # Project settings
│   └── settings/
│       ├── base.py             # Shared settings
│       ├── dev.py              # Development settings
│       └── prod.py             # Production settings
├── templates/                  # HTML templates
├── .github/workflows/          # CI/CD configuration
├── Dockerfile                  # Production container
├── docker-compose.yml          # Container orchestration
├── pyproject.toml              # Python project config
└── requirements.txt            # Dependencies
```

## Business Rules

### Availability
- **Dish**: Available if ALL required ingredients have sufficient quantity
- **Menu**: Available if ALL constituent dishes are available
- Availability updates automatically when inventory changes

### Pricing
- Dish cost = Sum of (ingredient price x quantity required)
- Menu cost = Sum of dish costs
- Selling price = cost x (1 + margin) [default margin: 20%]
- Prices are frozen at purchase time

### Purchases
- Atomic transactions with row-level locking
- Inventory deducted upon confirmation
- Concurrent purchases handled safely

## User Roles

### Admin (Superuser)
- Full access to all features
- Can manage units, ingredients, dishes, menus
- Can edit prices
- Can manage users
- Access to dashboard analytics

### Staff
- View and adjust inventory
- Create/edit dishes and menus (except prices)
- Create purchases
- View own purchases only

## Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set SECRET_KEY=<your-secret>
railway variables set DJANGO_ENV=prod
railway variables set ALLOWED_HOSTS=your-app.railway.app

# Deploy
railway up
```

### Docker (Self-hosted)

```bash
# Build production image
docker build -t django-delights:latest .

# Run with environment file
docker run -d \
  --env-file .env.production \
  -p 8000:8000 \
  django-delights:latest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost` |
| `DATABASE_URL` | Database connection URL | SQLite |
| `GLOBAL_MARGIN` | Pricing margin | `0.20` |
| `LOW_STOCK_THRESHOLD` | Low stock alert level | `10` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Token lifetime (minutes) | `60` |

See `.env.example` for full list.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`pre-commit run --all-files`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django & Django REST Framework communities
- Built as a portfolio project demonstrating enterprise patterns
