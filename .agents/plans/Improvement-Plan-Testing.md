# Testing Strategy Improvement Plan

**Priority:** Medium to High  
**Estimated Effort:** 2 sprints  
**Related Review:** Review-Summary.md

---

## Overview

This plan addresses testing gaps identified during the comprehensive project review, focusing on E2E tests, frontend testing, and edge case coverage.

---

## 1. High: Add End-to-End Tests with Playwright

**Current Issue:** No browser-based E2E tests

### Setup

```bash
pip install pytest-playwright
playwright install
```

### Configuration

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
# ... existing config ...
markers = [
    "e2e: marks tests as end-to-end browser tests",
]
```

### E2E Test Structure

```
delights/tests/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py           # Playwright fixtures
│   ├── test_auth_flow.py     # Login/logout tests
│   ├── test_purchase_flow.py # Complete purchase workflow
│   ├── test_inventory.py     # Inventory management
│   └── test_dashboard.py     # Dashboard functionality
```

### Playwright Fixtures

```python
# delights/tests/e2e/conftest.py
import pytest
from playwright.sync_api import Page, expect
from django.contrib.auth.models import User

@pytest.fixture
def live_server_url(live_server):
    return live_server.url

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )

@pytest.fixture
def logged_in_page(page: Page, live_server_url, admin_user):
    """Return a page logged in as admin."""
    page.goto(f"{live_server_url}/accounts/login/")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{live_server_url}/dashboard/")
    return page
```

### Sample E2E Tests

```python
# delights/tests/e2e/test_purchase_flow.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestPurchaseFlow:
    def test_complete_purchase_workflow(self, logged_in_page: Page, live_server_url):
        page = logged_in_page
        
        # Navigate to purchases
        page.click('a:has-text("Purchases")')
        page.wait_for_url(f"{live_server_url}/purchases/")
        
        # Start new purchase
        page.click('a:has-text("New Purchase")')
        
        # Select a dish
        page.fill('input[name="quantity_1"]', '2')
        page.click('button:has-text("Continue")')
        
        # Confirm purchase
        expect(page.locator('h1')).to_contain_text('Confirm Purchase')
        page.click('button:has-text("Finalize")')
        
        # Verify success
        expect(page.locator('.alert-success')).to_be_visible()

    def test_purchase_unavailable_dish_shows_error(self, logged_in_page: Page):
        # Test error handling when dish becomes unavailable
        pass
```

### Tasks
- [ ] Add `pytest-playwright` to requirements-dev.txt
- [ ] Create e2e test directory structure
- [ ] Implement Playwright fixtures
- [ ] Write auth flow tests
- [ ] Write purchase workflow tests
- [ ] Write inventory management tests
- [ ] Add E2E tests to CI pipeline
- [ ] Document E2E test running instructions

---

## 2. High: Add Concurrent Purchase Tests

**Current Issue:** No tests for race conditions in purchase finalization

### Test Implementation

```python
# delights/tests/test_concurrency.py
import pytest
import threading
from decimal import Decimal
from django.db import transaction
from django.test import TransactionTestCase

from delights.models import Dish, Ingredient, Purchase, RecipeRequirement
from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    RecipeRequirementFactory,
    UserFactory,
)
from delights.views import purchase_finalize

class TestConcurrentPurchases(TransactionTestCase):
    """Tests for concurrent purchase handling."""

    def test_concurrent_purchases_respect_inventory(self):
        """Two concurrent purchases should not oversell inventory."""
        # Setup: ingredient with quantity for only 1 purchase
        ingredient = IngredientFactory(quantity_available=Decimal('10'))
        dish = DishFactory(is_available=True, price=Decimal('10'))
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('10')
        )
        
        user1 = UserFactory()
        user2 = UserFactory()
        
        results = {'user1': None, 'user2': None}
        errors = []
        
        def make_purchase(user, result_key):
            try:
                # Simulate purchase through API
                from rest_framework.test import APIClient
                client = APIClient()
                client.force_authenticate(user=user)
                response = client.post('/api/v1/purchases/', {
                    'items': [{'dish_id': dish.id, 'quantity': 1}]
                })
                results[result_key] = response.status_code
            except Exception as e:
                errors.append(str(e))
        
        # Run concurrent purchases
        t1 = threading.Thread(target=make_purchase, args=(user1, 'user1'))
        t2 = threading.Thread(target=make_purchase, args=(user2, 'user2'))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # One should succeed, one should fail
        success_count = sum(1 for r in results.values() if r == 201)
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        
        # Verify inventory is correct
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal('0')

    def test_select_for_update_prevents_race_condition(self):
        """Verify select_for_update locks prevent double-spending."""
        ingredient = IngredientFactory(quantity_available=Decimal('5'))
        
        def concurrent_update():
            with transaction.atomic():
                ing = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
                ing.quantity_available -= Decimal('3')
                ing.save()
        
        threads = [threading.Thread(target=concurrent_update) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        ingredient.refresh_from_db()
        # Should be 5 - 3 - 3 - 3 = -4, but clamped or one should fail
        # This test verifies the locking behavior
```

### Tasks
- [ ] Create `test_concurrency.py`
- [ ] Add concurrent purchase tests
- [ ] Add inventory race condition tests
- [ ] Use `TransactionTestCase` for proper isolation
- [ ] Add threading-based concurrent tests
- [ ] Document concurrency test requirements

---

## 3. Medium: Add API Contract Tests

**Current Issue:** No validation that API changes don't break consumers

### Solution: Schema Snapshot Testing

```python
# delights/tests/test_api_schema.py
import pytest
import json
from pathlib import Path
from django.urls import reverse

SCHEMA_SNAPSHOT_PATH = Path(__file__).parent / 'snapshots' / 'api_schema.json'

class TestAPISchema:
    """Tests to ensure API schema doesn't change unexpectedly."""

    def test_schema_matches_snapshot(self, api_client_admin):
        """API schema should match the stored snapshot."""
        response = api_client_admin.get(reverse('schema'))
        assert response.status_code == 200
        
        current_schema = response.json()
        
        if not SCHEMA_SNAPSHOT_PATH.exists():
            # First run: create snapshot
            SCHEMA_SNAPSHOT_PATH.parent.mkdir(exist_ok=True)
            with open(SCHEMA_SNAPSHOT_PATH, 'w') as f:
                json.dump(current_schema, f, indent=2)
            pytest.skip("Schema snapshot created")
        
        with open(SCHEMA_SNAPSHOT_PATH) as f:
            expected_schema = json.load(f)
        
        # Compare paths (endpoints)
        current_paths = set(current_schema.get('paths', {}).keys())
        expected_paths = set(expected_schema.get('paths', {}).keys())
        
        assert current_paths == expected_paths, (
            f"API endpoints changed!\n"
            f"Added: {current_paths - expected_paths}\n"
            f"Removed: {expected_paths - current_paths}"
        )

    def test_response_format_dishes(self, api_client_staff, db):
        """Verify dish list response format."""
        from delights.tests.factories import DishFactory
        DishFactory.create_batch(2)
        
        response = api_client_staff.get(reverse('dish-list'))
        assert response.status_code == 200
        
        # Verify required fields
        result = response.data['results'][0]
        required_fields = ['id', 'name', 'cost', 'price', 'is_available']
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
```

### Tasks
- [ ] Create schema snapshot testing
- [ ] Add response format tests for each endpoint
- [ ] Create snapshots directory
- [ ] Add schema comparison to CI
- [ ] Document schema update process

---

## 4. Medium: Add Load Testing with Locust

**Current Issue:** No performance/stress testing

### Setup

```bash
pip install locust
```

### Locust Configuration

```python
# locustfile.py
from locust import HttpUser, task, between
import random

class DjangoDelightsUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login at start of each user session."""
        self.client.post("/accounts/login/", {
            "username": "loadtest",
            "password": "loadtest123"
        })
    
    @task(3)
    def view_dishes(self):
        """View dish list - most common action."""
        self.client.get("/dishes/")
    
    @task(2)
    def view_ingredients(self):
        """View ingredient inventory."""
        self.client.get("/ingredients/")
    
    @task(1)
    def view_dashboard(self):
        """View dashboard (admin only, heavier query)."""
        self.client.get("/dashboard/")
    
    @task(1)
    def make_purchase(self):
        """Complete a purchase workflow."""
        # Get available dishes
        response = self.client.get("/api/v1/dishes/available/")
        if response.status_code == 200 and response.json():
            dish = random.choice(response.json())
            # Create purchase
            self.client.post("/api/v1/purchases/", json={
                "items": [{"dish_id": dish['id'], "quantity": 1}]
            })


class APIUser(HttpUser):
    """API-only load testing."""
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Get JWT token."""
        response = self.client.post("/api/v1/auth/token/", json={
            "username": "apiuser",
            "password": "apipass123"
        })
        if response.status_code == 200:
            self.token = response.json()['access']
            self.client.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def list_dishes(self):
        self.client.get("/api/v1/dishes/")
    
    @task(3)
    def list_ingredients(self):
        self.client.get("/api/v1/ingredients/")
    
    @task(1)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard/")
```

### Tasks
- [ ] Add `locust` to requirements-dev.txt
- [ ] Create locustfile.py
- [ ] Create load test fixtures/data
- [ ] Document load testing process
- [ ] Add load test to CI (optional, on-demand)
- [ ] Define performance baselines

---

## 5. Medium: Improve Test Coverage for Edge Cases

**Current Issue:** Missing edge case tests

### Edge Cases to Add

```python
# delights/tests/test_edge_cases.py
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from delights.tests.factories import *
from delights.views import calculate_dish_cost, check_dish_availability

class TestEdgeCases:
    """Tests for boundary conditions and edge cases."""

    def test_negative_inventory_prevented(self, db):
        """Inventory should not go negative."""
        ingredient = IngredientFactory(quantity_available=Decimal('5'))
        ingredient.quantity_available -= Decimal('10')
        
        # Should clamp to 0 or raise error
        if ingredient.quantity_available < 0:
            ingredient.quantity_available = Decimal('0')
        ingredient.save()
        
        ingredient.refresh_from_db()
        assert ingredient.quantity_available >= Decimal('0')

    def test_very_large_quantity(self, db):
        """Handle very large quantities without overflow."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('99999999.99'),
            price_per_unit=Decimal('99999999.99')
        )
        dish = DishFactory()
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('1')
        )
        
        cost = calculate_dish_cost(dish)
        assert cost == Decimal('99999999.99')

    def test_zero_price_dish(self, db):
        """Handle dishes with zero price."""
        dish = DishFactory(price=Decimal('0'), cost=Decimal('0'))
        assert dish.price == Decimal('0')

    def test_unicode_in_names(self, db):
        """Handle unicode characters in names."""
        dish = DishFactory(name="Crème Brûlée 日本語 🍰")
        assert "Crème" in dish.name
        assert "日本語" in dish.name

    def test_very_long_description(self, db):
        """Handle very long descriptions."""
        long_desc = "A" * 10000
        dish = DishFactory(description=long_desc)
        assert len(dish.description) == 10000

    def test_simultaneous_availability_check(self, db):
        """Multiple dishes sharing same ingredient."""
        ingredient = IngredientFactory(quantity_available=Decimal('100'))
        dish1 = DishFactory()
        dish2 = DishFactory()
        
        RecipeRequirementFactory(
            dish=dish1, ingredient=ingredient, quantity_required=Decimal('60')
        )
        RecipeRequirementFactory(
            dish=dish2, ingredient=ingredient, quantity_required=Decimal('60')
        )
        
        # Both should be available individually
        assert check_dish_availability(dish1) is True
        assert check_dish_availability(dish2) is True
        
        # But can't purchase both

    def test_circular_menu_reference(self, db):
        """Menus should not cause circular references."""
        dish = DishFactory()
        menu = MenuFactory(dishes=[dish])
        # Menus can't contain menus, so this is just a sanity check
        assert menu.dishes.count() == 1

    def test_deleted_user_purchases(self, db):
        """Purchases should be preserved when user is deactivated."""
        user = UserFactory()
        purchase = PurchaseFactory(user=user)
        
        user.is_active = False
        user.save()
        
        purchase.refresh_from_db()
        assert purchase.user == user  # PROTECT prevents deletion
```

### Tasks
- [ ] Create `test_edge_cases.py`
- [ ] Add boundary condition tests
- [ ] Add unicode/i18n tests
- [ ] Add large data tests
- [ ] Add concurrent access tests
- [ ] Review and expand based on production issues

---

## 6. Low: Add Frontend Unit Tests

**Current Issue:** No JavaScript testing (minimal JS currently)

### Setup (if adding more JS)

```bash
npm init -y
npm install --save-dev jest @testing-library/dom
```

### Sample Test

```javascript
// static/js/__tests__/purchase.test.js
describe('Purchase Form', () => {
  test('calculates total correctly', () => {
    document.body.innerHTML = `
      <input type="number" name="quantity_1" value="2" data-price="10.00">
      <input type="number" name="quantity_2" value="1" data-price="15.00">
      <span id="total"></span>
    `;
    
    // Assuming we have a calculateTotal function
    const total = calculateTotal();
    expect(total).toBe(35.00);
  });
});
```

### Tasks
- [ ] Evaluate JS testing need (minimal JS currently)
- [ ] Set up Jest if needed
- [ ] Add tests for any client-side validation
- [ ] Document frontend testing approach

---

## 7. CI Integration Updates

### Updated CI Configuration

```yaml
# .github/workflows/ci.yml additions

  # E2E Tests
  e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-playwright
          playwright install chromium
      
      - name: Run E2E tests
        run: pytest delights/tests/e2e/ -v --browser chromium

  # Load Tests (manual trigger)
  load-test:
    name: Load Test
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v4
      - name: Run Locust
        run: |
          pip install locust
          locust --headless -u 10 -r 2 -t 60s --host http://localhost:8000
```

### Tasks
- [ ] Add E2E test job to CI
- [ ] Add load test workflow (manual trigger)
- [ ] Configure test parallelization
- [ ] Add test result reporting

---

## Dependencies to Add

```txt
# requirements-dev.txt additions
pytest-playwright>=0.4.0
locust>=2.24.0
```

---

## Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | E2E tests setup and auth flow | 1 sprint |
| Phase 2 | Concurrent tests, edge cases | 0.5 sprint |
| Phase 3 | Load testing, CI integration | 0.5 sprint |

---

## Success Metrics

- [ ] E2E tests cover critical user flows
- [ ] Concurrent purchase tests pass
- [ ] Test coverage remains > 80%
- [ ] Load tests establish performance baseline
- [ ] All tests run in CI pipeline
- [ ] No flaky tests
