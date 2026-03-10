# Django Delights

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready restaurant inventory and ordering management system built with Django 5.2. Features a full web interface, REST API with JWT authentication, Docker support, and a comprehensive test suite with pytest.

> **AI Disclosure:** This project was developed with the assistance of artificial intelligence tools (Windsurf Cascade, Claude, GitHub Copilot) for code generation, documentation, testing, and review. All AI-generated output has been reviewed, adapted, and validated by the project author.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Application Usage](#application-usage)
- [Additional Documentation](#additional-documentation)
- [Project Structure](#project-structure)
- [Business Rules](#business-rules)
- [Testing & Code Quality](#testing--code-quality)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Functionality

- **Inventory Management** — Ingredients with units of measurement, prices, and stock quantities
- **Dishes** — Create dishes with recipe requirements and auto-calculated costs
- **Composite Menus** — Bundle multiple dishes into menus with combined pricing
- **3-Step Purchase Workflow** — Selection, confirmation, and atomic finalization with inventory deduction
- **Admin Dashboard** — Revenue, cost, profit metrics, top-selling items, and low-stock alerts
- **User Management** — Create, edit, activate/deactivate users, and reset passwords

### Technical Highlights

- **Full REST API** — CRUD for all models with Django REST Framework
- **JWT Authentication** — Access and refresh tokens via SimpleJWT
- **OpenAPI Documentation** — Swagger UI and ReDoc auto-generated with drf-spectacular
- **Role-Based Access Control** — Granular permissions for Admin and Staff (includes price-editing control)
- **Atomic Transactions** — Row-level locking (`select_for_update`) to prevent race conditions
- **Production-Ready Docker** — Multi-stage builds with Gunicorn, Nginx, PostgreSQL, and Redis
- **CI/CD** — GitHub Actions with linting, testing, security scanning, and Docker image builds
- **Comprehensive Test Suite** — Unit, integration, E2E (Playwright), concurrency, API contract, and load tests (Locust)

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | Django 5.2 |
| API | Django REST Framework 3.14+ |
| API Authentication | SimpleJWT (access + refresh tokens) |
| API Documentation | drf-spectacular (OpenAPI 3.0, Swagger UI, ReDoc) |
| Database | SQLite (development) / PostgreSQL 15 (production) |
| Testing | pytest, pytest-django, pytest-cov, factory-boy, pytest-playwright, locust |
| Code Quality | black, flake8, isort, mypy, bandit, pre-commit |
| Containers | Docker (multi-stage), Docker Compose |
| Production Server | Gunicorn + WhiteNoise |
| Reverse Proxy | Nginx (optional, `production` profile) |
| Cache | Redis 7 (optional) |
| CI/CD | GitHub Actions |
| Deployment | Railway / Docker self-hosted |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **pip**
- **Git**
- (Optional) **Docker** and **Docker Compose** for containerized environments

### Local Installation (Development)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/django-delights.git
cd django-delights

# 2. Create a virtual environment
python -m venv venv

# Activate on Linux/Mac:
source venv/bin/activate
# Activate on Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your values (or keep the defaults for development)

# 5. Run migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

### Docker Installation (Development)

```bash
# Start all services (web + PostgreSQL + Redis + Mailhog)
docker-compose up

# In another terminal, run migrations
docker-compose exec web python manage.py migrate

# Create a superuser
docker-compose exec web python manage.py createsuperuser
```

### Access Points

| Service | URL |
|---|---|
| Web Application | http://localhost:8000/ |
| Django Admin | http://localhost:8000/admin/ |
| API Swagger (docs) | http://localhost:8000/api/docs/ |
| API ReDoc | http://localhost:8000/api/redoc/ |
| API v1 | http://localhost:8000/api/v1/ |
| Mailhog (Docker dev only) | http://localhost:8025/ |

---

## Application Usage

### User Roles

The application has two access levels:

**Admin (Superuser)**
- Full access to all features
- Manage units, ingredients, dishes, and menus
- Edit prices
- Manage users (create, edit, activate/deactivate, reset passwords)
- Dashboard with analytics

**Staff**
- View and adjust ingredient inventory
- Create and edit dishes and menus (except prices)
- Create purchases
- View only own purchases

### Typical Workflow

1. **Admin sets up units of measurement** (grams, liters, units, etc.)
2. **Admin/Staff creates ingredients** with unit, price, and initial quantity
3. **Dishes are created** with name and description, then recipe requirements are added (ingredient + quantity needed)
4. **Dish cost is auto-calculated** from ingredients. The selling price can be set manually or is suggested with a configurable margin (default 20%)
5. **Menus are created** by grouping multiple dishes, with cost and availability calculated automatically
6. **Users make purchases** by selecting available dishes, confirming, then finalizing (with atomic inventory deduction)
7. **The Dashboard** displays revenue, costs, profit, top-selling dishes, and low-stock alerts

### REST API

The API allows all operations to be performed programmatically. See the full guide in **[docs/API.md](docs/API.md)**.

Quick authentication example:

```bash
# Get JWT tokens
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Use the access token
curl http://localhost:8000/api/v1/dishes/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Additional Documentation

| Document | Description |
|---|---|
| **[docs/API.md](docs/API.md)** | Full REST API guide: endpoints, authentication, examples |
| **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Deployment guide: Docker, Railway, environment variables |
| **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** | Development guide: setup, tests, code quality, pre-commit |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Project architecture: models, permissions, settings, design decisions |

---

## Project Structure

```
django-delights/
├── delights/                    # Main application
│   ├── api/                     # REST API
│   │   ├── serializers.py       # DRF serializers
│   │   ├── views.py             # API viewsets
│   │   ├── urls.py              # API routing
│   │   └── permissions.py       # Custom permissions
│   ├── tests/                   # Test suite
│   │   ├── e2e/                 # E2E tests with Playwright
│   │   ├── snapshots/           # API schema snapshots
│   │   ├── conftest.py          # Pytest fixtures
│   │   ├── factories.py         # Factory Boy factories
│   │   ├── test_models.py       # Model tests
│   │   ├── test_views.py        # View tests
│   │   ├── test_integration.py  # Integration tests
│   │   ├── test_concurrency.py  # Concurrency tests
│   │   ├── test_api_schema.py   # API contract tests
│   │   └── test_edge_cases.py   # Edge case tests
│   ├── fixtures/                # Sample data for development
│   ├── models.py                # Data models (7 models)
│   ├── views.py                 # Web views (CBV + FBV)
│   ├── forms.py                 # Django forms
│   ├── mixins.py                # Reusable permission mixins
│   ├── admin.py                 # Django admin configuration
│   ├── urls.py                  # Unit URLs
│   ├── urls_ingredients.py      # Ingredient URLs
│   ├── urls_dishes.py           # Dish URLs
│   ├── urls_menus.py            # Menu URLs
│   ├── urls_purchases.py        # Purchase URLs
│   ├── urls_dashboard.py        # Dashboard URLs
│   └── urls_users.py            # User management URLs
├── django_delights/             # Project configuration
│   ├── settings/                # Split settings by environment
│   │   ├── base.py              # Shared configuration
│   │   ├── dev.py               # Development configuration
│   │   └── prod.py              # Production configuration
│   ├── settings.py              # Default settings (simple development)
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI entry point
│   └── asgi.py                  # ASGI entry point
├── templates/                   # HTML templates
│   ├── delights/                # App templates
│   │   ├── base.html            # Base template
│   │   ├── dashboard/           # Admin dashboard
│   │   ├── dishes/              # Dish CRUD
│   │   ├── ingredients/         # Ingredient CRUD
│   │   ├── menus/               # Menu CRUD
│   │   ├── purchases/           # Purchase workflow
│   │   ├── units/               # Unit CRUD
│   │   └── users/               # User management
│   └── registration/            # Authentication templates
├── static/                      # Static files
├── scripts/                     # Helper scripts
│   └── init-db.sql              # PostgreSQL initialization
├── docs/                        # Detailed documentation
├── .github/workflows/           # CI/CD with GitHub Actions
│   └── ci.yml                   # Pipeline: lint > test > security > build > deploy
├── Dockerfile                   # Production image (multi-stage)
├── Dockerfile.dev               # Development image
├── docker-compose.yml           # Production orchestration
├── docker-compose.override.yml  # Development overrides
├── pyproject.toml               # Project and tool configuration
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── railway.toml                 # Railway deployment configuration
├── .env.example                 # Example environment variables
├── .pre-commit-config.yaml      # Pre-commit hooks
└── LICENSE                      # MIT License
```

---

## Business Rules

### Availability

- **Dish** — Available if **all** required ingredients have sufficient stock, and the dish has at least one recipe requirement
- **Menu** — Available if **all** constituent dishes are available, and the menu has at least one dish
- Availability is recalculated automatically when inventory is adjusted, recipe requirements change, or purchases are made

### Pricing

- **Dish cost** = Sum of (ingredient price_per_unit x quantity_required)
- **Menu cost** = Sum of all dish costs
- **Selling price** = Can be set manually or suggested as cost x (1 + margin). Default global margin is 20% (configurable via `GLOBAL_MARGIN`)
- **Frozen prices** — When a purchase is made, prices are recorded as they were at that moment (`price_at_purchase`)

### Purchases (3-Step Atomic Flow)

1. **Selection** — User picks available dishes and quantities
2. **Confirmation** — Summary displayed with prices and total
3. **Finalization** — Atomic transaction with `select_for_update()`:
   - Re-validates dish availability
   - Verifies sufficient stock for all ingredients
   - Creates purchase record with frozen prices
   - Deducts inventory
   - Recalculates dish and menu availability

---

## Testing & Code Quality

### Test Suite

The project includes comprehensive testing:

- **Unit Tests** — Model, view, and service layer tests
- **Integration Tests** — Component interaction tests
- **E2E Tests** — Browser-based tests with Playwright
- **Concurrency Tests** — Race condition and locking tests
- **API Contract Tests** — Schema stability tests
- **Load Tests** — Performance testing with Locust
- **Edge Case Tests** — Boundary conditions and special cases

```bash
# Run all tests
pytest

# Run with coverage (target: >80%)
pytest --cov=delights --cov-report=html

# Run specific test types
pytest delights/tests/test_models.py -v
pytest -m integration
pytest -m e2e                           # E2E tests (requires Playwright)
pytest delights/tests/test_concurrency.py

# E2E tests with Playwright
playwright install                      # First time setup
pytest delights/tests/e2e/ -v -m e2e

# Load testing
locust --headless -u 10 -r 2 -t 60s --host http://localhost:8000

# Code quality
pre-commit run --all-files   # All checks
black .                       # Formatting
isort .                       # Import sorting
flake8 .                      # Linting
mypy delights/                # Type checking
```

See **[docs/TESTING.md](docs/TESTING.md)** for comprehensive testing guide and **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** for development details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`pre-commit run --all-files && pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Maria del Mar Almagro Moreno**

---

## Acknowledgments

- **Django** and **Django REST Framework** communities
- AI tools used during development: **Windsurf Cascade**, **Claude (Anthropic)**, **GitHub Copilot**
- Built as a portfolio project demonstrating professional development patterns
