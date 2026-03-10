import pytest
from decimal import Decimal
from playwright.sync_api import Page, expect

from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    RecipeRequirementFactory,
)


@pytest.mark.e2e
class TestPurchaseFlow:
    """E2E tests for purchase workflows."""

    @pytest.fixture
    def available_dish(self, db):
        """Create a dish with sufficient inventory."""
        ingredient = IngredientFactory(
            name="Test Ingredient",
            quantity_available=Decimal('100'),
            price_per_unit=Decimal('2.00')
        )
        dish = DishFactory(
            name="Test Dish",
            is_available=True,
            price=Decimal('15.00')
        )
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('5')
        )
        return dish

    def test_complete_purchase_workflow(self, logged_in_page: Page, live_server_url, available_dish):
        """Test complete purchase workflow from start to finish."""
        page = logged_in_page
        
        page.goto(f"{live_server_url}/purchases/")
        
        page.click('a:has-text("New Purchase"), a:has-text("Add Purchase")')
        
        expect(page.locator('h1, h2')).to_contain_text('Purchase', ignore_case=True)
        
        page.fill(f'input[name*="quantity"][name*="{available_dish.id}"]', '2')
        page.click('button[type="submit"]')
        
        expect(page.locator('.alert-success, .success')).to_be_visible(timeout=10000)

    def test_purchase_shows_dish_list(self, logged_in_page: Page, live_server_url, available_dish):
        """Test purchase page displays available dishes."""
        page = logged_in_page
        
        page.goto(f"{live_server_url}/purchases/")
        
        expect(page.locator(f'text="{available_dish.name}"')).to_be_visible()

    def test_purchase_unavailable_dish_not_shown(self, logged_in_page: Page, live_server_url, db):
        """Test unavailable dishes are not shown in purchase list."""
        unavailable_dish = DishFactory(name="Unavailable Dish", is_available=False)
        
        page = logged_in_page
        page.goto(f"{live_server_url}/purchases/")
        
        expect(page.locator(f'text="{unavailable_dish.name}"')).not_to_be_visible()

    def test_purchase_history_displays(self, logged_in_page: Page, live_server_url):
        """Test purchase history page loads and displays purchases."""
        page = logged_in_page
        
        page.goto(f"{live_server_url}/purchases/")
        
        expect(page.locator('h1, h2')).to_be_visible()
