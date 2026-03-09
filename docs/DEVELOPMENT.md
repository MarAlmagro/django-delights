# Development Guide

Guide for setting up the development environment, running tests, and maintaining code quality.

> **AI Disclosure:** This documentation was generated with the assistance of AI tools and reviewed by the project author.

---

## Table of Contents

- [Environment Setup](#environment-setup)
- [Settings Configuration](#settings-configuration)
- [Tests](#tests)
- [Code Quality](#code-quality)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD](#cicd)
- [Development Fixtures](#development-fixtures)
- [Useful Tools](#useful-tools)

---

## Environment Setup

### Full Development Installation

```bash
# Clone repository
git clone https://github.com/yourusername/django-delights.git
cd django-delights

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate

# Install development dependencies (includes production deps)
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env

# Install pre-commit hooks
pre-commit install

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### Dependencies

The project separates dependencies into two files:

**`requirements.txt`** — Production:
- Django 5.x
- Django REST Framework
- SimpleJWT
- drf-spectacular
- django-cors-headers
- psycopg2-binary
- dj-database-url
- gunicorn
- whitenoise
- python-dotenv

**`requirements-dev.txt`** — Development (includes production via `-r requirements.txt`):
- pytest, pytest-django, pytest-cov
- factory-boy
- pre-commit
- black, flake8, isort, mypy
- flake8-bugbear, flake8-comprehensions, flake8-simplify
- django-stubs
- bandit, safety
- ipython
- django-debug-toolbar

---

## Settings Configuration

The project has **two settings systems** that coexist:

### 1. Simple Settings (`django_delights/settings.py`)

A single file for quick development. Uses SQLite, does not include DRF or JWT. Suitable for working with the web interface only.

### 2. Split Settings (`django_delights/settings/`)

For environments that require the full REST API:

- **`base.py`** — Shared configuration: installed apps (includes DRF, SimpleJWT, drf-spectacular, corsheaders), REST Framework, JWT, CORS, logging, business settings
- **`dev.py`** — Development: DEBUG=True, SQLite, open CORS, relaxed throttling, console email backend
- **`prod.py`** — Production: DEBUG=False, PostgreSQL (via DATABASE_URL or individual variables), HTTPS security, restricted CORS, SMTP email, optional Redis

### Selecting Settings

```bash
# Use split settings (dev)
export DJANGO_SETTINGS_MODULE=django_delights.settings.dev

# Use split settings (prod)
export DJANGO_SETTINGS_MODULE=django_delights.settings.prod

# Or use the simple settings (default in manage.py)
# No configuration needed
```

For pytest, the settings module is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "django_delights.settings.dev"
```

---

## Tests

### Test Structure

```
delights/tests/
├── __init__.py
├── conftest.py          # Shared pytest fixtures
├── factories.py         # factory-boy factories for data generation
├── test_models.py       # Unit tests for models
├── test_views.py        # Web view tests
└── test_integration.py  # Integration tests (full workflows)
```

There is also `delights/tests.py` with additional tests (outside the `tests/` package).

### Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific test files
pytest delights/tests/test_models.py
pytest delights/tests/test_views.py
pytest delights/tests/test_integration.py

# Integration tests only (by marker)
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# A specific test
pytest delights/tests/test_models.py::TestDishModel::test_dish_creation -v
```

### Coverage

```bash
# Run with coverage
pytest --cov=delights --cov-report=html

# Console report
pytest --cov=delights --cov-report=term-missing

# Generate XML (for CI)
pytest --cov=delights --cov-report=xml
```

The HTML report is generated in `htmlcov/`. Coverage configuration is in `pyproject.toml`:
- **Minimum required**: 80%
- **Excludes**: migrations, tests, admin.py, `__pycache__`

### Factories

The project uses `factory-boy` to generate test data. Factories are in `delights/tests/factories.py` and produce instances of all models.

### Pytest Fixtures

Shared fixtures are in `delights/tests/conftest.py` and provide pre-created objects for tests.

---

## Code Quality

### Black (Formatting)

```bash
# Format all code
black .

# Check without modifying
black --check --diff .
```

Configuration in `pyproject.toml`:
- Line length: 88
- Target: Python 3.11, 3.12
- Excludes: migrations

### isort (Import Sorting)

```bash
# Sort imports
isort .

# Check without modifying
isort --check-only --diff .
```

Configuration in `pyproject.toml`:
- Profile: black (compatible)
- Custom sections: FUTURE, STDLIB, DJANGO, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

### flake8 (Linting)

```bash
# Full lint
flake8 .

# Critical errors only
flake8 . --select=E9,F63,F7,F82
```

Additional plugins:
- flake8-bugbear
- flake8-comprehensions
- flake8-simplify

### mypy (Type Checking)

```bash
# Type check
mypy delights/
```

Configuration in `pyproject.toml`:
- Plugin: `mypy_django_plugin`
- Strict mode: disabled
- Ignores missing imports

### bandit (Security)

```bash
# Security scan
bandit -r delights/ -ll -ii
```

### safety (Dependency Vulnerabilities)

```bash
# Check dependencies
safety check
```

---

## Pre-commit Hooks

The project uses pre-commit to run checks automatically before each commit.

### Installation

```bash
pip install pre-commit
pre-commit install
```

### Configured Hooks

1. **pre-commit-hooks** — General checks: trailing whitespace, end-of-file, valid YAML/JSON/TOML, large files, merge conflicts, private keys, debug statements
2. **isort** — Import sorting (black profile)
3. **black** — Code formatting
4. **flake8** — Linting with plugins (bugbear, comprehensions, simplify)
5. **mypy** — Type checking with django-stubs
6. **django-upgrade** — Django syntax upgrades (target 5.0)
7. **bandit** — Security analysis (excludes tests)
8. **prettier** — YAML formatting

### Manual Execution

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run black --all-files

# Update hook versions
pre-commit autoupdate
```

---

## CI/CD

The CI/CD pipeline is in `.github/workflows/ci.yml` and runs on push/PR to `main` and `develop`.

### Pipeline Jobs

```
lint ─→ test ────→ build ─→ deploy-staging (develop branch)
     ─→ security ↗         ─→ deploy-production (main branch)
```

1. **Lint** — Black, isort, flake8
2. **Test** — pytest with coverage, PostgreSQL as a service, upload to Codecov
3. **Security** — Bandit (static analysis) + Safety (dependency vulnerabilities)
4. **Build** — Docker image build + Trivy (container vulnerability scanner)
5. **Deploy Staging** — Only on push to `develop` (placeholder for Railway)
6. **Deploy Production** — Only on push to `main` (placeholder for Railway)

### Configuration

- Python: 3.12
- PostgreSQL: 15 (GitHub Actions service)
- Test-only SECRET_KEY for CI

---

## Development Fixtures

The `delights/fixtures/` directory is set up to contain sample data in JSON format.

### Loading Fixtures

```bash
# Load all (order matters due to dependencies)
python manage.py loaddata units ingredients dishes menus users

# Load individually
python manage.py loaddata units
python manage.py loaddata ingredients
```

### Creating Fixtures from Existing Data

```bash
python manage.py dumpdata delights.Unit --indent 2 > delights/fixtures/units.json
python manage.py dumpdata delights.Ingredient --indent 2 > delights/fixtures/ingredients.json
python manage.py dumpdata delights.Dish --indent 2 > delights/fixtures/dishes.json
python manage.py dumpdata delights.Menu --indent 2 > delights/fixtures/menus.json
python manage.py dumpdata auth.User --indent 2 > delights/fixtures/users.json
```

> **Note**: Fixtures are for development and testing only. Do not use in production.

---

## Useful Tools

### Enhanced Django Shell

```bash
# With IPython (if installed)
python manage.py shell

# Example: query data
>>> from delights.models import Dish
>>> Dish.objects.filter(is_available=True).count()
```

### Django Debug Toolbar

Included in `requirements-dev.txt` but disabled by default. To enable, uncomment the lines in `django_delights/settings/dev.py`:

```python
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]
```

### Development Server

```bash
# Default port (8000)
python manage.py runserver

# Specific port
python manage.py runserver 0.0.0.0:9000
```

### Django Management Commands

```bash
# View all migrations and their status
python manage.py showmigrations

# Create new migrations
python manage.py makemigrations

# Revert a migration
python manage.py migrate delights 0001

# Check configuration
python manage.py check --deploy
```
