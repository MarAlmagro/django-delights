from locust import HttpUser, task, between
import random


class DjangoDelightsUser(HttpUser):
    """Simulates typical user behavior on the Django Delights application."""
    
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
    def view_purchases(self):
        """View purchase history."""
        self.client.get("/purchases/")
    
    @task(1)
    def make_purchase(self):
        """Complete a purchase workflow."""
        response = self.client.get("/api/v1/dishes/available/")
        if response.status_code == 200:
            try:
                dishes = response.json()
                if dishes and len(dishes) > 0:
                    dish = random.choice(dishes)
                    self.client.post("/api/v1/purchases/", json={
                        "items": [{"dish_id": dish['id'], "quantity": 1}]
                    })
            except Exception:
                pass


class APIUser(HttpUser):
    """API-only load testing for external integrations."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Get JWT token for API authentication."""
        response = self.client.post("/api/v1/auth/token/", json={
            "username": "apiuser",
            "password": "apipass123"
        })
        if response.status_code == 200:
            try:
                self.token = response.json()['access']
                self.client.headers = {"Authorization": f"Bearer {self.token}"}
            except Exception:
                self.token = None
    
    @task(5)
    def list_dishes(self):
        """List all dishes via API."""
        self.client.get("/api/v1/dishes/")
    
    @task(3)
    def list_ingredients(self):
        """List all ingredients via API."""
        self.client.get("/api/v1/ingredients/")
    
    @task(2)
    def list_menus(self):
        """List all menus via API."""
        self.client.get("/api/v1/menus/")
    
    @task(1)
    def get_dashboard(self):
        """Get dashboard statistics via API."""
        self.client.get("/api/v1/dashboard/")
    
    @task(1)
    def get_available_dishes(self):
        """Get only available dishes."""
        self.client.get("/api/v1/dishes/available/")
    
    @task(1)
    def create_purchase(self):
        """Create a purchase via API."""
        dishes_response = self.client.get("/api/v1/dishes/available/")
        if dishes_response.status_code == 200:
            try:
                dishes = dishes_response.json()
                if dishes and len(dishes) > 0:
                    dish = random.choice(dishes)
                    self.client.post("/api/v1/purchases/", json={
                        "items": [{"dish_id": dish['id'], "quantity": 1}]
                    })
            except Exception:
                pass


class ReadOnlyUser(HttpUser):
    """Simulates read-only users (customers browsing)."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as regular user."""
        self.client.post("/accounts/login/", {
            "username": "readonly",
            "password": "readonly123"
        })
    
    @task(5)
    def browse_dishes(self):
        """Browse available dishes."""
        self.client.get("/dishes/")
    
    @task(3)
    def view_menus(self):
        """View menu offerings."""
        self.client.get("/menus/")
    
    @task(1)
    def view_dashboard(self):
        """View dashboard."""
        self.client.get("/dashboard/")


class StressTestUser(HttpUser):
    """High-frequency user for stress testing."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Quick login."""
        self.client.post("/accounts/login/", {
            "username": "stress",
            "password": "stress123"
        })
    
    @task(10)
    def rapid_dish_requests(self):
        """Rapid dish list requests."""
        self.client.get("/api/v1/dishes/")
    
    @task(5)
    def rapid_ingredient_requests(self):
        """Rapid ingredient requests."""
        self.client.get("/api/v1/ingredients/")
    
    @task(1)
    def rapid_purchase_attempts(self):
        """Rapid purchase attempts."""
        self.client.get("/api/v1/dishes/available/")
