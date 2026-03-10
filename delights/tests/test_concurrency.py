import pytest
import threading
from decimal import Decimal
from django.db import transaction
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from delights.models import Ingredient, Purchase
from delights.tests.factories import (
    DishFactory,
    IngredientFactory,
    RecipeRequirementFactory,
    UserFactory,
)


class TestConcurrentPurchases(TransactionTestCase):
    """Tests for concurrent purchase handling."""

    def test_concurrent_purchases_respect_inventory(self):
        """Two concurrent purchases should not oversell inventory."""
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
                client = APIClient()
                client.force_authenticate(user=user)
                response = client.post('/api/v1/purchases/', {
                    'items': [{'dish_id': dish.id, 'quantity': 1}]
                })
                results[result_key] = response.status_code
            except Exception as e:
                errors.append(str(e))
        
        t1 = threading.Thread(target=make_purchase, args=(user1, 'user1'))
        t2 = threading.Thread(target=make_purchase, args=(user2, 'user2'))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        success_count = sum(1 for r in results.values() if r == 201)
        assert success_count == 1, f"Expected 1 success, got {success_count}"
        
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal('0')

    def test_select_for_update_prevents_race_condition(self):
        """Verify select_for_update locks prevent double-spending."""
        ingredient = IngredientFactory(quantity_available=Decimal('15'))
        
        results = []
        
        def concurrent_update():
            try:
                with transaction.atomic():
                    ing = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
                    current = ing.quantity_available
                    ing.quantity_available -= Decimal('5')
                    ing.save()
                    results.append(current)
            except Exception as e:
                results.append(f"error: {e}")
        
        threads = [threading.Thread(target=concurrent_update) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        ingredient.refresh_from_db()
        assert ingredient.quantity_available == Decimal('0')
        
        successful_updates = [r for r in results if isinstance(r, Decimal)]
        assert len(successful_updates) == 3

    def test_concurrent_inventory_updates(self):
        """Test concurrent inventory updates maintain consistency."""
        ingredient = IngredientFactory(quantity_available=Decimal('100'))
        
        def add_inventory():
            with transaction.atomic():
                ing = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
                ing.quantity_available += Decimal('10')
                ing.save()
        
        def remove_inventory():
            with transaction.atomic():
                ing = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
                ing.quantity_available -= Decimal('5')
                ing.save()
        
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=add_inventory))
            threads.append(threading.Thread(target=remove_inventory))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        ingredient.refresh_from_db()
        expected = Decimal('100') + (5 * Decimal('10')) - (5 * Decimal('5'))
        assert ingredient.quantity_available == expected

    def test_concurrent_dish_availability_check(self):
        """Test concurrent availability checks are consistent."""
        ingredient = IngredientFactory(quantity_available=Decimal('20'))
        dish = DishFactory(is_available=True)
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('10')
        )
        
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        results = []
        
        def attempt_purchase(user):
            try:
                client = APIClient()
                client.force_authenticate(user=user)
                response = client.post('/api/v1/purchases/', {
                    'items': [{'dish_id': dish.id, 'quantity': 1}]
                })
                results.append(response.status_code)
            except Exception as e:
                results.append(f"error: {e}")
        
        threads = [
            threading.Thread(target=attempt_purchase, args=(user1,)),
            threading.Thread(target=attempt_purchase, args=(user2,)),
            threading.Thread(target=attempt_purchase, args=(user3,)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        success_count = sum(1 for r in results if r == 201)
        assert success_count <= 2, "Should only allow 2 purchases with available inventory"
        
        ingredient.refresh_from_db()
        assert ingredient.quantity_available >= Decimal('0')


class TestConcurrentDatabaseOperations(TransactionTestCase):
    """Tests for general concurrent database operations."""

    def test_concurrent_purchase_creation(self):
        """Test multiple purchases can be created concurrently."""
        dish = DishFactory(is_available=True)
        users = [UserFactory() for _ in range(5)]
        
        ingredient = IngredientFactory(quantity_available=Decimal('1000'))
        RecipeRequirementFactory(
            dish=dish,
            ingredient=ingredient,
            quantity_required=Decimal('1')
        )
        
        def create_purchase(user):
            client = APIClient()
            client.force_authenticate(user=user)
            client.post('/api/v1/purchases/', {
                'items': [{'dish_id': dish.id, 'quantity': 1}]
            })
        
        threads = [threading.Thread(target=create_purchase, args=(u,)) for u in users]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        purchase_count = Purchase.objects.count()
        assert purchase_count == 5

    def test_concurrent_ingredient_creation(self):
        """Test ingredients can be created concurrently without conflicts."""
        def create_ingredient(name):
            IngredientFactory(name=name)
        
        threads = [
            threading.Thread(target=create_ingredient, args=(f"Ingredient {i}",))
            for i in range(10)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert Ingredient.objects.count() == 10
