import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestAuthenticationFlow:
    """E2E tests for authentication flows."""

    def test_login_success(self, page: Page, live_server_url, admin_user):
        """Test successful login redirects to dashboard."""
        page.goto(f"{live_server_url}/accounts/login/")
        
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'testpass123')
        page.click('button[type="submit"]')
        
        page.wait_for_url(f"{live_server_url}/dashboard/")
        expect(page).to_have_url(f"{live_server_url}/dashboard/")

    def test_login_invalid_credentials(self, page: Page, live_server_url, admin_user):
        """Test login with invalid credentials shows error."""
        page.goto(f"{live_server_url}/accounts/login/")
        
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'wrongpassword')
        page.click('button[type="submit"]')
        
        expect(page.locator('.alert-danger, .error, .errorlist')).to_be_visible()

    def test_logout(self, logged_in_page: Page, live_server_url):
        """Test logout redirects to login page."""
        page = logged_in_page
        
        page.click('a[href*="logout"]')
        
        page.wait_for_url(f"{live_server_url}/accounts/login/")
        expect(page).to_have_url(f"{live_server_url}/accounts/login/")

    def test_unauthenticated_redirect(self, page: Page, live_server_url):
        """Test unauthenticated users are redirected to login."""
        page.goto(f"{live_server_url}/dashboard/")
        
        page.wait_for_url(f"{live_server_url}/accounts/login/*")
        expect(page).to_have_url(f"{live_server_url}/accounts/login/?next=/dashboard/")

    def test_login_preserves_next_parameter(self, page: Page, live_server_url, admin_user):
        """Test login redirects to originally requested page."""
        page.goto(f"{live_server_url}/ingredients/")
        
        page.wait_for_url(f"{live_server_url}/accounts/login/*")
        
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'testpass123')
        page.click('button[type="submit"]')
        
        page.wait_for_url(f"{live_server_url}/ingredients/")
        expect(page).to_have_url(f"{live_server_url}/ingredients/")
