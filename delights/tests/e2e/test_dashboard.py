import pytest
from decimal import Decimal
from playwright.sync_api import Page, expect

from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    PurchaseFactory,
)


@pytest.mark.e2e
class TestDashboard:
    """E2E tests for dashboard functionality."""

    def test_dashboard_loads(self, logged_in_page: Page, live_server_url):
        """Test dashboard page loads successfully."""
        page = logged_in_page
        
        expect(page).to_have_url(f"{live_server_url}/dashboard/")
        expect(page.locator('h1, h2')).to_contain_text('Dashboard', ignore_case=True)

    def test_dashboard_shows_statistics(self, logged_in_page: Page, live_server_url, db):
        """Test dashboard displays key statistics."""
        DishFactory.create_batch(5)
        IngredientFactory.create_batch(10)
        
        page = logged_in_page
        page.goto(f"{live_server_url}/dashboard/")
        
        expect(page.locator('body')).to_contain_text('5', ignore_case=True)
        expect(page.locator('body')).to_contain_text('10', ignore_case=True)

    def test_dashboard_shows_recent_purchases(self, logged_in_page: Page, live_server_url, admin_user, db):
        """Test dashboard shows recent purchase activity."""
        dish = DishFactory(name="Dashboard Test Dish")
        purchase = PurchaseFactory(user=admin_user, dish=dish)
        
        page = logged_in_page
        page.goto(f"{live_server_url}/dashboard/")
        
        expect(page.locator('body')).to_contain_text('Purchase', ignore_case=True)

    def test_dashboard_navigation_links(self, logged_in_page: Page, live_server_url):
        """Test dashboard navigation links work."""
        page = logged_in_page
        
        page.click('a:has-text("Ingredients")')
        expect(page).to_have_url(f"{live_server_url}/ingredients/")
        
        page.goto(f"{live_server_url}/dashboard/")
        page.click('a:has-text("Dishes")')
        expect(page).to_have_url(f"{live_server_url}/dishes/")

    def test_dashboard_profit_calculation(self, logged_in_page: Page, live_server_url, admin_user, db):
        """Test dashboard shows profit calculations."""
        ingredient = IngredientFactory(
            quantity_available=Decimal('100'),
            price_per_unit=Decimal('2.00')
        )
        dish = DishFactory(price=Decimal('10.00'))
        
        page = logged_in_page
        page.goto(f"{live_server_url}/dashboard/")
        
        expect(page.locator('body')).to_contain_text('Revenue', ignore_case=True)
