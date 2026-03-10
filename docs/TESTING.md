# Testing Guide

This document describes the testing strategy and how to run various types of tests in the Django Delights project.

## Table of Contents

- [Overview](#overview)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [E2E Tests](#e2e-tests)
- [Load Testing](#load-testing)
- [Concurrency Tests](#concurrency-tests)
- [API Contract Tests](#api-contract-tests)
- [Edge Case Tests](#edge-case-tests)
- [CI/CD Integration](#cicd-integration)

## Overview

The project uses a comprehensive testing strategy covering:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows with Playwright
- **Concurrency Tests**: Test race conditions and concurrent operations
- **API Contract Tests**: Ensure API stability
- **Load Tests**: Performance and stress testing with Locust
- **Edge Case Tests**: Boundary conditions and special cases

**Test Coverage Target**: > 80%

## Test Types

### Unit Tests

Located in `delights/tests/test_*.py` files.

```bash
# Run all unit tests
pytest

# Run specific test file
pytest delights/tests/test_models.py

# Run with coverage
pytest --cov=delights --cov-report=html
```

### Integration Tests

Located in `delights/tests/test_integration.py`.

```bash
# Run integration tests
pytest delights/tests/test_integration.py -v
```

### E2E Tests

Browser-based tests using Playwright in `delights/tests/e2e/`.

```bash
# Install Playwright browsers (first time only)
playwright install

# Run all E2E tests
pytest delights/tests/e2e/ -v -m e2e

# Run specific E2E test file
pytest delights/tests/e2e/test_auth_flow.py -v

# Run with specific browser
pytest delights/tests/e2e/ --browser chromium
pytest delights/tests/e2e/ --browser firefox
```

### Concurrency Tests

Tests for race conditions in `delights/tests/test_concurrency.py`.

```bash
# Run concurrency tests
pytest delights/tests/test_concurrency.py -v
```

### API Contract Tests

Schema and contract tests in `delights/tests/test_api_schema.py`.

```bash
# Run API contract tests
pytest delights/tests/test_api_schema.py -v

# Update schema snapshot (when intentional changes are made)
rm delights/tests/snapshots/api_schema.json
pytest delights/tests/test_api_schema.py::TestAPISchema::test_schema_matches_snapshot
```

### Edge Case Tests

Boundary condition tests in `delights/tests/test_edge_cases.py`.

```bash
# Run edge case tests
pytest delights/tests/test_edge_cases.py -v
```

## Running Tests

### Quick Test Run

```bash
# Run all tests (excluding E2E and slow tests)
pytest -m "not e2e and not slow"

# Run with coverage
pytest --cov=delights --cov-report=term-missing
```

### Full Test Suite

```bash
# Run everything including E2E tests
pytest -v

# Run with coverage report
pytest --cov=delights --cov-report=html --cov-report=term
```

### Test Markers

```bash
# Run only E2E tests
pytest -m e2e

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

### Parallel Testing

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## E2E Tests

### Prerequisites

1. Install Playwright:
   ```bash
   pip install pytest-playwright
   playwright install
   ```

2. Ensure development server can run:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

### E2E Test Structure

```
delights/tests/e2e/
├── __init__.py
├── conftest.py              # Playwright fixtures
├── test_auth_flow.py        # Authentication tests
├── test_purchase_flow.py    # Purchase workflow tests
├── test_inventory.py        # Inventory management tests
└── test_dashboard.py        # Dashboard tests
```

### Writing E2E Tests

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_example(logged_in_page: Page, live_server_url):
    page = logged_in_page
    page.goto(f"{live_server_url}/dishes/")
    expect(page.locator('h1')).to_contain_text('Dishes')
```

### E2E Test Fixtures

- `live_server_url`: URL of the test server
- `admin_user`: Admin user for testing
- `staff_user`: Staff user for testing
- `logged_in_page`: Page already logged in as admin
- `staff_logged_in_page`: Page logged in as staff

## Load Testing

### Setup

```bash
pip install locust
```

### Running Load Tests

```bash
# Start Locust web UI
locust

# Then open http://localhost:8089 in browser

# Headless mode
locust --headless -u 10 -r 2 -t 60s --host http://localhost:8000

# With HTML report
locust --headless -u 10 -r 2 -t 60s --host http://localhost:8000 --html report.html
```

### Load Test Users

The `locustfile.py` defines several user types:

- **DjangoDelightsUser**: Typical user behavior
- **APIUser**: API-only interactions
- **ReadOnlyUser**: Browse-only behavior
- **StressTestUser**: High-frequency requests

### Creating Test Data

Before load testing, create test users:

```bash
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('loadtest', 'load@test.com', 'loadtest123')
>>> User.objects.create_user('apiuser', 'api@test.com', 'apipass123')
```

## Concurrency Tests

Concurrency tests use `TransactionTestCase` and threading to test race conditions.

```bash
# Run concurrency tests
pytest delights/tests/test_concurrency.py -v

# These tests verify:
# - Inventory doesn't go negative
# - select_for_update prevents race conditions
# - Concurrent purchases are handled correctly
```

## API Contract Tests

### Schema Snapshots

API schema tests ensure the API contract doesn't change unexpectedly.

```bash
# First run creates snapshot
pytest delights/tests/test_api_schema.py::TestAPISchema::test_schema_matches_snapshot

# Subsequent runs compare against snapshot
pytest delights/tests/test_api_schema.py
```

### Updating Snapshots

When you intentionally change the API:

1. Delete the snapshot: `rm delights/tests/snapshots/api_schema.json`
2. Re-run the test to create new snapshot
3. Review the changes in git diff
4. Commit the updated snapshot

## Edge Case Tests

Edge case tests cover:

- Boundary conditions (min/max values)
- Unicode and special characters
- Zero and negative values
- Very large datasets
- Empty states
- Concurrent operations

```bash
pytest delights/tests/test_edge_cases.py -v
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests

### CI Test Jobs

1. **Lint**: Code formatting and linting
2. **Migrations**: Migration checks
3. **Test**: Unit and integration tests with coverage
4. **E2E**: End-to-end browser tests
5. **Security**: Security scans

### Manual Load Testing

Trigger load tests via GitHub Actions:

1. Go to Actions tab
2. Select "Load Test" workflow
3. Click "Run workflow"
4. Configure parameters (users, duration, etc.)

## Best Practices

### Writing Tests

1. **Use factories**: Use Factory Boy for test data
2. **Isolate tests**: Each test should be independent
3. **Clear names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Follow AAA pattern
5. **Don't test Django**: Test your code, not Django internals

### Test Data

```python
# Good: Use factories
dish = DishFactory(name="Test Dish")

# Avoid: Manual object creation
dish = Dish.objects.create(
    name="Test Dish",
    price=Decimal('10.00'),
    # ... many fields
)
```

### Fixtures

```python
# Good: Reusable fixtures
@pytest.fixture
def available_dish(db):
    return DishFactory(is_available=True)

def test_purchase(available_dish):
    # Use fixture
    pass
```

### Assertions

```python
# Good: Specific assertions
assert dish.price == Decimal('10.00')
assert dish.is_available is True

# Avoid: Generic assertions
assert dish
```

## Troubleshooting

### E2E Tests Failing

1. Check Playwright is installed: `playwright install`
2. Ensure test database is clean
3. Check for port conflicts
4. Review screenshots in `test-results/`

### Concurrency Tests Flaky

1. Increase timeouts if needed
2. Check database supports transactions
3. Verify `select_for_update` is used correctly

### Coverage Not Meeting Target

1. Run with missing report: `pytest --cov=delights --cov-report=term-missing`
2. Identify uncovered lines
3. Add tests for critical paths first

### Load Tests Failing

1. Ensure test users exist
2. Check server is running
3. Verify network connectivity
4. Review Locust logs

## Performance Baselines

Target performance metrics:

- **Response Time (p95)**: < 200ms for list endpoints
- **Response Time (p95)**: < 500ms for detail endpoints
- **Throughput**: > 100 req/s for read operations
- **Error Rate**: < 1% under normal load

Run load tests to establish baselines for your environment.

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Playwright for Python](https://playwright.dev/python/)
- [Locust documentation](https://docs.locust.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
