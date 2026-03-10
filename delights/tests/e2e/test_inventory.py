import pytest
from decimal import Decimal
from playwright.sync_api import Page, expect

from delights.tests.factories import IngredientFactory, DishFactory


@pytest.mark.e2e
class TestInventoryManagement:
    """E2E tests for inventory management."""

    def test_view_ingredients_list(self, logged_in_page: Page, live_server_url, db):
        """Test viewing ingredients list."""
        ingredient = IngredientFactory(
            name="Test Ingredient",
            quantity_available=Decimal('50'),
            price_per_unit=Decimal('3.00')
        )
        
        page = logged_in_page
        page.goto(f"{live_server_url}/ingredients/")
        
        expect(page.locator(f'text="{ingredient.name}"')).to_be_visible()

    def test_add_ingredient(self, logged_in_page: Page, live_server_url):
        """Test adding a new ingredient."""
        page = logged_in_page
        
        page.goto(f"{live_server_url}/ingredients/")
        page.click('a:has-text("Add"), a:has-text("New")')
        
        page.fill('input[name="name"]', 'New Ingredient')
        page.fill('input[name="quantity_available"]', '100')
        page.fill('input[name="price_per_unit"]', '5.00')
        page.fill('select[name="unit"]', 'kg')
        
        page.click('button[type="submit"]')
        
        expect(page.locator('.alert-success, .success')).to_be_visible(timeout=10000)

    def test_view_dishes_list(self, logged_in_page: Page, live_server_url, db):
        """Test viewing dishes list."""
        dish = DishFactory(name="Test Dish", price=Decimal('12.00'))
        
        page = logged_in_page
        page.goto(f"{live_server_url}/dishes/")
        
        expect(page.locator(f'text="{dish.name}"')).to_be_visible()

    def test_add_dish(self, logged_in_page: Page, live_server_url, db):
        """Test adding a new dish."""
        ingredient = IngredientFactory(
            name="Ingredient for Dish",
            quantity_available=Decimal('100')
        )
        
        page = logged_in_page
        page.goto(f"{live_server_url}/dishes/")
        page.click('a:has-text("Add"), a:has-text("New")')
        
        page.fill('input[name="name"]', 'New Dish')
        page.fill('input[name="price"]', '15.00')
        page.fill('textarea[name="description"]', 'A delicious new dish')
        
        page.click('button[type="submit"]')
        
        expect(page.locator('.alert-success, .success, text="New Dish"')).to_be_visible(timeout=10000)

    def test_ingredient_low_stock_warning(self, logged_in_page: Page, live_server_url, db):
        """Test low stock ingredients show warning."""
        low_stock = IngredientFactory(
            name="Low Stock Item",
            quantity_available=Decimal('2')
        )
        
        page = logged_in_page
        page.goto(f"{live_server_url}/ingredients/")
        
        expect(page.locator('.alert-warning, .warning, .low-stock')).to_be_visible()
