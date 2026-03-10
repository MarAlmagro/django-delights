# End-to-End Tests

This directory contains browser-based end-to-end tests using Playwright.

## Setup

1. Install Playwright:
   ```bash
   pip install pytest-playwright
   playwright install
   ```

2. Install browsers (one-time):
   ```bash
   playwright install chromium
   # Or install all browsers
   playwright install
   ```

## Running E2E Tests

```bash
# Run all E2E tests
pytest delights/tests/e2e/ -v -m e2e

# Run specific test file
pytest delights/tests/e2e/test_auth_flow.py -v

# Run with specific browser
pytest delights/tests/e2e/ --browser chromium
pytest delights/tests/e2e/ --browser firefox
pytest delights/tests/e2e/ --browser webkit

# Run in headed mode (see browser)
pytest delights/tests/e2e/ --headed

# Run with slow motion (for debugging)
pytest delights/tests/e2e/ --slowmo 1000
```

## Test Structure

```
e2e/
├── __init__.py
├── conftest.py              # Fixtures and configuration
├── test_auth_flow.py        # Authentication and login tests
├── test_purchase_flow.py    # Purchase workflow tests
├── test_inventory.py        # Inventory management tests
└── test_dashboard.py        # Dashboard functionality tests
```

## Available Fixtures

### `live_server_url`
URL of the test server.

```python
def test_example(live_server_url):
    url = f"{live_server_url}/dishes/"
```

### `admin_user`
Admin user for testing.

```python
def test_example(admin_user):
    assert admin_user.is_superuser
```

### `staff_user`
Staff user for testing.

```python
def test_example(staff_user):
    assert staff_user.is_staff
```

### `logged_in_page`
Page already logged in as admin.

```python
def test_example(logged_in_page: Page, live_server_url):
    page = logged_in_page
    page.goto(f"{live_server_url}/dishes/")
    # Already authenticated
```

### `staff_logged_in_page`
Page logged in as staff user.

```python
def test_example(staff_logged_in_page: Page):
    page = staff_logged_in_page
    # Already authenticated as staff
```

## Writing E2E Tests

### Basic Test Structure

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_example(logged_in_page: Page, live_server_url):
    page = logged_in_page
    
    # Navigate
    page.goto(f"{live_server_url}/dishes/")
    
    # Interact
    page.click('a:has-text("Add Dish")')
    page.fill('input[name="name"]', 'Test Dish')
    page.click('button[type="submit"]')
    
    # Assert
    expect(page.locator('.alert-success')).to_be_visible()
```

### Common Patterns

#### Navigation
```python
page.goto(f"{live_server_url}/path/")
page.click('a:has-text("Link Text")')
```

#### Form Interaction
```python
page.fill('input[name="field"]', 'value')
page.select_option('select[name="field"]', 'option')
page.check('input[type="checkbox"]')
page.click('button[type="submit"]')
```

#### Assertions
```python
# Element visibility
expect(page.locator('.element')).to_be_visible()
expect(page.locator('.element')).not_to_be_visible()

# Text content
expect(page.locator('h1')).to_contain_text('Expected')
expect(page.locator('h1')).to_have_text('Exact Text')

# URL
expect(page).to_have_url(f"{live_server_url}/expected/")

# Count
expect(page.locator('.item')).to_have_count(5)
```

#### Waiting
```python
# Wait for URL
page.wait_for_url(f"{live_server_url}/target/")

# Wait for selector
page.wait_for_selector('.element')

# Wait for load state
page.wait_for_load_state('networkidle')
```

## Test Data

Use factories to create test data:

```python
from delights.tests.factories import DishFactory, IngredientFactory

@pytest.mark.e2e
def test_with_data(logged_in_page: Page, live_server_url, db):
    # Create test data
    dish = DishFactory(name="Test Dish")
    
    page = logged_in_page
    page.goto(f"{live_server_url}/dishes/")
    
    # Verify data appears
    expect(page.locator(f'text="{dish.name}"')).to_be_visible()
```

## Debugging

### Screenshots
```python
# Take screenshot on failure (automatic in CI)
page.screenshot(path="screenshot.png")
```

### Video Recording
```python
# Videos are recorded automatically in CI
# Check test-results/ directory
```

### Trace Viewer
```python
# Run with trace
pytest delights/tests/e2e/ --tracing on

# View trace
playwright show-trace trace.zip
```

### Headed Mode
```bash
# See the browser while tests run
pytest delights/tests/e2e/ --headed --slowmo 1000
```

## Best Practices

1. **Use semantic selectors**: Prefer text content over CSS selectors
   ```python
   # Good
   page.click('a:has-text("Add Dish")')
   
   # Avoid
   page.click('#btn-123')
   ```

2. **Wait for navigation**: Use `wait_for_url` after actions that navigate
   ```python
   page.click('button[type="submit"]')
   page.wait_for_url(f"{live_server_url}/success/")
   ```

3. **Use fixtures**: Leverage provided fixtures for common setup
   ```python
   def test_example(logged_in_page: Page):
       # Already logged in
   ```

4. **Isolate tests**: Each test should be independent
   ```python
   @pytest.mark.e2e
   def test_one(db):
       # Create own data
       dish = DishFactory()
   ```

5. **Clear test names**: Describe what the test verifies
   ```python
   def test_purchase_workflow_completes_successfully():
       # Clear what this tests
   ```

## CI/CD Integration

E2E tests run automatically in CI on:
- Push to main/develop
- Pull requests

The CI workflow:
1. Sets up Python and dependencies
2. Installs Playwright browsers
3. Runs migrations
4. Executes E2E tests
5. Uploads artifacts on failure

## Troubleshooting

### Tests timing out
- Increase timeout: `expect(locator).to_be_visible(timeout=10000)`
- Check for slow database operations
- Verify selectors are correct

### Element not found
- Check selector syntax
- Verify element exists in DOM
- Wait for element: `page.wait_for_selector('.element')`

### Tests flaky
- Add explicit waits
- Use `wait_for_url` after navigation
- Check for race conditions

### Browser not installed
```bash
playwright install chromium
```

## Resources

- [Playwright Python Docs](https://playwright.dev/python/)
- [Playwright Selectors](https://playwright.dev/python/docs/selectors)
- [Playwright Assertions](https://playwright.dev/python/docs/test-assertions)
