from django.test import TestCase
from django.contrib.auth.models import User
from .models import Unit, Ingredient, Dish, RecipeRequirement, Menu, Purchase, PurchaseItem
from .views import calculate_dish_cost, check_dish_availability, update_dish_availability, update_menu_availability


class UnitModelTest(TestCase):
    """Test Unit model"""
    def test_unit_creation(self):
        unit = Unit.objects.create(name='g', description='gram', is_active=True)
        self.assertEqual(str(unit), 'g')
        self.assertTrue(unit.is_active)


class IngredientModelTest(TestCase):
    """Test Ingredient model"""
    def setUp(self):
        self.unit = Unit.objects.create(name='g', description='gram', is_active=True)
    
    def test_ingredient_creation(self):
        ingredient = Ingredient.objects.create(
            name='Flour',
            unit=self.unit,
            price_per_unit=0.50,
            quantity_available=1000
        )
        self.assertEqual(str(ingredient), 'Flour (1000.00 g)')
        self.assertEqual(ingredient.quantity_available, 1000)


class DishModelTest(TestCase):
    """Test Dish model and cost calculation"""
    def setUp(self):
        self.unit = Unit.objects.create(name='g', description='gram', is_active=True)
        self.ingredient1 = Ingredient.objects.create(
            name='Flour',
            unit=self.unit,
            price_per_unit=0.50,
            quantity_available=1000
        )
        self.ingredient2 = Ingredient.objects.create(
            name='Sugar',
            unit=self.unit,
            price_per_unit=0.75,
            quantity_available=500
        )
        self.dish = Dish.objects.create(
            name='Cookie',
            description='A delicious cookie',
            cost=0,
            price=0,
            is_available=False
        )
    
    def test_dish_creation(self):
        self.assertEqual(str(self.dish), 'Cookie')
    
    def test_dish_cost_calculation(self):
        RecipeRequirement.objects.create(
            dish=self.dish,
            ingredient=self.ingredient1,
            quantity_required=100
        )
        RecipeRequirement.objects.create(
            dish=self.dish,
            ingredient=self.ingredient2,
            quantity_required=50
        )
        
        cost = calculate_dish_cost(self.dish)
        expected_cost = (100 * 0.50) + (50 * 0.75)  # 50 + 37.5 = 87.5
        self.assertEqual(cost, expected_cost)
    
    def test_dish_availability(self):
        # Initially unavailable (no ingredients)
        self.assertFalse(check_dish_availability(self.dish))
        
        # Add requirement that exceeds available quantity
        RecipeRequirement.objects.create(
            dish=self.dish,
            ingredient=self.ingredient1,
            quantity_required=2000  # More than available (1000)
        )
        self.assertFalse(check_dish_availability(self.dish))
        
        # Add requirement within available quantity
        RecipeRequirement.objects.create(
            dish=self.dish,
            ingredient=self.ingredient2,
            quantity_required=100  # Less than available (500)
        )
        update_dish_availability(self.dish)
        # Should still be unavailable because ingredient1 is insufficient
        self.assertFalse(self.dish.is_available)


class PurchaseModelTest(TestCase):
    """Test Purchase and PurchaseItem models"""
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.unit = Unit.objects.create(name='unit', description='unit', is_active=True)
        self.ingredient = Ingredient.objects.create(
            name='Test Ingredient',
            unit=self.unit,
            price_per_unit=1.00,
            quantity_available=100
        )
        self.dish = Dish.objects.create(
            name='Test Dish',
            cost=1.00,
            price=1.20,
            is_available=True
        )
        RecipeRequirement.objects.create(
            dish=self.dish,
            ingredient=self.ingredient,
            quantity_required=1
        )
        self.purchase = Purchase.objects.create(
            user=self.user,
            total_price_at_purchase=1.20,
            status='completed'
        )
    
    def test_purchase_creation(self):
        self.assertEqual(str(self.purchase), f'Purchase #{self.purchase.id} by testuser on {self.purchase.timestamp.strftime("%Y-%m-%d %H:%M")}')
    
    def test_purchase_item_creation(self):
        item = PurchaseItem.objects.create(
            purchase=self.purchase,
            dish=self.dish,
            quantity=1,
            price_at_purchase=1.20,
            subtotal=1.20
        )
        self.assertEqual(item.subtotal, 1.20)
        self.assertEqual(str(item), f'1x Test Dish @ 1.20 (Purchase #{self.purchase.id})')
