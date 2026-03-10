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
def staff_user(db):
    user = User.objects.create_user(
        username='staff',
        email='staff@test.com',
        password='testpass123'
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def logged_in_page(page: Page, live_server_url, admin_user):
    """Return a page logged in as admin."""
    page.goto(f"{live_server_url}/accounts/login/")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{live_server_url}/dashboard/")
    return page


@pytest.fixture
def staff_logged_in_page(page: Page, live_server_url, staff_user):
    """Return a page logged in as staff."""
    page.goto(f"{live_server_url}/accounts/login/")
    page.fill('input[name="username"]', 'staff')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{live_server_url}/dashboard/")
    return page
