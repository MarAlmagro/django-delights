from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Sum, Count, Q
from .models import Unit, Ingredient, Dish, RecipeRequirement, Menu, Purchase, PurchaseItem
from .forms import UnitForm, IngredientForm, DishForm, RecipeRequirementForm, InventoryAdjustmentForm, MenuForm, PurchaseCreateForm


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_authenticated and user.is_superuser


# Units CRUD (Admin only)
class UnitListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Unit
    template_name = 'delights/units/list.html'
    context_object_name = 'units'

    def test_func(self):
        return is_admin(self.request.user)


class UnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'delights/units/add.html'
    success_url = reverse_lazy('units:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Unit "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class UnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'delights/units/edit.html'
    success_url = reverse_lazy('units:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Unit "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


@login_required
@user_passes_test(is_admin)
def unit_toggle_active(request, pk):
    """Toggle active status of a unit"""
    unit = get_object_or_404(Unit, pk=pk)
    unit.is_active = not unit.is_active
    unit.save()
    status = "activated" if unit.is_active else "deactivated"
    messages.success(request, f'Unit "{unit.name}" has been {status}.')
    return redirect('units:list')


# Ingredients CRUD
class IngredientListView(LoginRequiredMixin, ListView):
    model = Ingredient
    template_name = 'delights/ingredients/list.html'
    context_object_name = 'ingredients'


class IngredientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = 'delights/ingredients/add.html'
    success_url = reverse_lazy('ingredients:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        form.instance.quantity_available = 0  # Start with 0 quantity
        messages.success(self.request, f'Ingredient "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class IngredientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = 'delights/ingredients/edit.html'
    success_url = reverse_lazy('ingredients:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f'Ingredient "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


@login_required
def inventory_adjust(request, pk):
    """Adjust inventory quantity (staff + admin)"""
    ingredient = get_object_or_404(Ingredient, pk=pk)
    
    if request.method == 'POST':
        form = InventoryAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.cleaned_data['adjustment']
            ingredient.quantity_available += adjustment
            if ingredient.quantity_available < 0:
                ingredient.quantity_available = 0
            ingredient.save()
            
            # Trigger availability recalculation for Dishes and Menus
            update_dish_availability_from_ingredient(ingredient)
            update_menu_availability()
            
            messages.success(request, f'Inventory for "{ingredient.name}" adjusted by {adjustment}. New quantity: {ingredient.quantity_available}')
            return redirect('ingredients:list')
    else:
        form = InventoryAdjustmentForm()
    
    return render(request, 'delights/ingredients/adjust.html', {
        'ingredient': ingredient,
        'form': form,
    })


# Helper functions for cost and availability calculations
GLOBAL_MARGIN = 0.20  # 20% margin


def calculate_dish_cost(dish):
    """Calculate dish cost from recipe requirements"""
    total_cost = 0
    for requirement in dish.recipe_requirements.all():
        total_cost += requirement.ingredient.price_per_unit * requirement.quantity_required
    return total_cost


def check_dish_availability(dish):
    """Check if dish is available (all ingredients have sufficient quantity)"""
    if not dish.recipe_requirements.exists():
        return False
    for requirement in dish.recipe_requirements.all():
        if requirement.ingredient.quantity_available < requirement.quantity_required:
            return False
    return True


def update_dish_availability(dish):
    """Update dish cost and availability"""
    dish.cost = calculate_dish_cost(dish)
    dish.is_available = check_dish_availability(dish) and dish.recipe_requirements.exists()
    dish.save()


def update_dish_availability_from_ingredient(ingredient):
    """Update all dishes that use this ingredient"""
    dishes = Dish.objects.filter(recipe_requirements__ingredient=ingredient).distinct()
    for dish in dishes:
        update_dish_availability(dish)


def update_menu_cost(menu):
    """Calculate menu cost from dishes"""
    total_cost = sum(dish.cost for dish in menu.dishes.all())
    return total_cost


def check_menu_availability(menu):
    """Check if menu is available (all dishes are available)"""
    return all(dish.is_available for dish in menu.dishes.all()) and menu.dishes.exists()


def update_menu_availability(menu=None):
    """Update menu cost and availability"""
    if menu:
        menus = [menu]
    else:
        menus = Menu.objects.all()
    
    for menu in menus:
        menu.cost = update_menu_cost(menu)
        menu.is_available = check_menu_availability(menu)
        menu.save()


# Dishes CRUD
class DishListView(LoginRequiredMixin, ListView):
    model = Dish
    template_name = 'delights/dishes/list.html'
    context_object_name = 'dishes'


class DishDetailView(LoginRequiredMixin, DetailView):
    model = Dish
    template_name = 'delights/dishes/detail.html'
    context_object_name = 'dish'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dish = self.get_object()
        context['recipe_requirements'] = dish.recipe_requirements.all()
        return context


class DishCreateView(LoginRequiredMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = 'delights/dishes/add.html'
    success_url = reverse_lazy('dishes:list')

    def form_valid(self, form):
        dish = form.save(commit=False)
        dish.cost = 0  # Will be calculated when recipe requirements are added
        dish.price = 0  # Will be set after cost is calculated
        dish.is_available = False
        dish.save()
        
        # Calculate price after recipe requirements are added
        # For now, set a default price
        if not dish.price:
            dish.price = 0
        
        dish.save()
        messages.success(self.request, f'Dish "{dish.name}" created. Now add recipe requirements.')
        return redirect('dishes:requirements', pk=dish.pk)


class DishUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Dish
    form_class = DishForm
    template_name = 'delights/dishes/edit.html'
    success_url = reverse_lazy('dishes:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        dish = form.save()
        update_dish_availability(dish)
        messages.success(self.request, f'Dish "{dish.name}" updated successfully.')
        return super().form_valid(form)


@login_required
def manage_recipe_requirements(request, pk):
    """Manage recipe requirements for a dish"""
    dish = get_object_or_404(Dish, pk=pk)
    requirements = dish.recipe_requirements.all()
    
    if request.method == 'POST':
        if 'add' in request.POST:
            # Add new requirement
            form = RecipeRequirementForm(request.POST)
            if form.is_valid():
                requirement = form.save(commit=False)
                requirement.dish = dish
                requirement.save()
                update_dish_availability(dish)
                
                # Set price using global margin if not set
                if dish.price == 0 and dish.cost > 0:
                    dish.price = dish.cost * (1 + GLOBAL_MARGIN)
                    dish.save()
                
                messages.success(request, f'Added {requirement.ingredient.name} to recipe.')
                return redirect('dishes:requirements', pk=dish.pk)
        elif 'delete' in request.POST:
            # Delete requirement
            requirement_id = request.POST.get('requirement_id')
            requirement = get_object_or_404(RecipeRequirement, pk=requirement_id, dish=dish)
            ingredient_name = requirement.ingredient.name
            requirement.delete()
            update_dish_availability(dish)
            messages.success(request, f'Removed {ingredient_name} from recipe.')
            return redirect('dishes:requirements', pk=dish.pk)
    
    form = RecipeRequirementForm()
    
    return render(request, 'delights/dishes/requirements.html', {
        'dish': dish,
        'requirements': requirements,
        'form': form,
    })


# Menus CRUD
class MenuListView(LoginRequiredMixin, ListView):
    model = Menu
    template_name = 'delights/menus/list.html'
    context_object_name = 'menus'


class MenuDetailView(LoginRequiredMixin, DetailView):
    model = Menu
    template_name = 'delights/menus/detail.html'
    context_object_name = 'menu'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        menu = self.get_object()
        context['dishes'] = menu.dishes.all()
        return context


class MenuCreateView(LoginRequiredMixin, CreateView):
    model = Menu
    form_class = MenuForm
    template_name = 'delights/menus/add.html'
    success_url = reverse_lazy('menus:list')

    def form_valid(self, form):
        menu = form.save(commit=False)
        menu.cost = 0  # Will be calculated when dishes are added
        menu.price = menu.cost * (1 + GLOBAL_MARGIN) if menu.cost > 0 else 0
        menu.is_available = False
        menu.save()
        
        messages.success(self.request, f'Menu "{menu.name}" created. Now add dishes.')
        return redirect('menus:items', pk=menu.pk)


class MenuUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Menu
    form_class = MenuForm
    template_name = 'delights/menus/edit.html'
    success_url = reverse_lazy('menus:list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        menu = form.save()
        update_menu_availability(menu)
        messages.success(self.request, f'Menu "{menu.name}" updated successfully.')
        return super().form_valid(form)


@login_required
def manage_menu_items(request, pk):
    """Manage dishes in a menu"""
    menu = get_object_or_404(Menu, pk=pk)
    current_dishes = menu.dishes.all()
    available_dishes = Dish.objects.exclude(pk__in=[d.pk for d in current_dishes])
    
    if request.method == 'POST':
        if 'add' in request.POST:
            # Add dish to menu
            dish_id = request.POST.get('dish_id')
            dish = get_object_or_404(Dish, pk=dish_id)
            menu.dishes.add(dish)
            update_menu_availability(menu)
            
            # Set price using global margin if not set
            if menu.price == 0 and menu.cost > 0:
                menu.price = menu.cost * (1 + GLOBAL_MARGIN)
                menu.save()
            
            messages.success(request, f'Added {dish.name} to menu.')
            return redirect('menus:items', pk=menu.pk)
        elif 'remove' in request.POST:
            # Remove dish from menu
            dish_id = request.POST.get('dish_id')
            dish = get_object_or_404(Dish, pk=dish_id)
            menu.dishes.remove(dish)
            update_menu_availability(menu)
            messages.success(request, f'Removed {dish.name} from menu.')
            return redirect('menus:items', pk=menu.pk)
    
    return render(request, 'delights/menus/items.html', {
        'menu': menu,
        'current_dishes': current_dishes,
        'available_dishes': available_dishes,
    })


# Purchases - Step 1: Purchase Creation
@login_required
def purchase_create(request):
    """Create purchase by selecting dishes and quantities"""
    available_dishes = Dish.objects.filter(is_available=True).order_by('name')
    
    if request.method == 'POST':
        # Extract selected dishes and quantities
        selected_items = {}
        for key, value in request.POST.items():
            if key.startswith('quantity_') and value and int(value) > 0:
                dish_id = int(key.replace('quantity_', ''))
                quantity = int(value)
                dish = get_object_or_404(Dish, pk=dish_id, is_available=True)
                selected_items[dish_id] = {
                    'dish': dish,
                    'quantity': quantity,
                    'price': float(dish.price),
                }
        
        if not selected_items:
            messages.error(request, 'Please select at least one dish.')
            return render(request, 'delights/purchases/add.html', {
                'available_dishes': available_dishes,
            })
        
        # Store in session for confirmation step
        purchase_data = []
        total = 0
        for dish_id, item in selected_items.items():
            purchase_data.append({
                'dish_id': dish_id,
                'quantity': item['quantity'],
                'price': item['price'],
            })
            total += item['quantity'] * item['price']
        
        request.session['purchase_data'] = purchase_data
        request.session['purchase_total'] = float(total)
        
        return redirect('purchases:confirm')
    
    return render(request, 'delights/purchases/add.html', {
        'available_dishes': available_dishes,
    })


# Purchases - Step 2: Confirmation
@login_required
def purchase_confirm(request):
    """Display purchase confirmation"""
    purchase_data = request.session.get('purchase_data')
    purchase_total = request.session.get('purchase_total')
    
    if not purchase_data:
        messages.error(request, 'No purchase data found. Please start over.')
        return redirect('purchases:add')
    
    # Load dishes for display
    purchase_items = []
    for item in purchase_data:
        try:
            dish = Dish.objects.get(pk=item['dish_id'], is_available=True)
            purchase_items.append({
                'dish': dish,
                'quantity': item['quantity'],
                'price': item['price'],
                'subtotal': item['quantity'] * item['price'],
            })
        except Dish.DoesNotExist:
            messages.error(request, f'Dish #{item["dish_id"]} is no longer available.')
            return redirect('purchases:add')
    
    return render(request, 'delights/purchases/confirm.html', {
        'purchase_items': purchase_items,
        'purchase_total': purchase_total,
    })


# Purchases - Step 3: Atomic Finalization
@login_required
@transaction.atomic
def purchase_finalize(request):
    """Atomically finalize purchase with inventory deduction"""
    if request.method != 'POST':
        return redirect('purchases:add')
    
    purchase_data = request.session.get('purchase_data')
    purchase_total = request.session.get('purchase_total')
    
    if not purchase_data:
        messages.error(request, 'No purchase data found. Please start over.')
        return redirect('purchases:add')
    
    try:
        # Prepare items and validate availability
        purchase_items = []
        ingredients_needed = {}  # ingredient_id -> total_quantity_needed
        
        for item in purchase_data:
            dish = Dish.objects.select_for_update().get(pk=item['dish_id'])
            
            # Revalidate availability
            if not dish.is_available:
                messages.error(request, f'Dish "{dish.name}" is no longer available.')
                return redirect('purchases:confirm')
            
            # Check each ingredient requirement
            for requirement in dish.recipe_requirements.select_for_update().select_related('ingredient'):
                ingredient = requirement.ingredient
                total_needed = requirement.quantity_required * item['quantity']
                
                if ingredient.pk not in ingredients_needed:
                    ingredients_needed[ingredient.pk] = {
                        'ingredient': ingredient,
                        'total': 0,
                    }
                ingredients_needed[ingredient.pk]['total'] += total_needed
            
            purchase_items.append({
                'dish': dish,
                'quantity': item['quantity'],
                'price': item['price'],
            })
        
        # Validate all ingredients have sufficient quantity
        for ing_id, ing_data in ingredients_needed.items():
            ingredient = ing_data['ingredient']
            total_needed = ing_data['total']
            
            # Lock ingredient row
            locked_ingredient = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
            
            if locked_ingredient.quantity_available < total_needed:
                messages.error(request, f'Insufficient inventory: {locked_ingredient.name} (need {total_needed}, have {locked_ingredient.quantity_available}).')
                return redirect('purchases:confirm')
        
        # All validations passed - create purchase and deduct inventory
        purchase = Purchase.objects.create(
            user=request.user,
            total_price_at_purchase=purchase_total,
            status='completed',
        )
        
        total_actual = 0
        for item in purchase_items:
            dish = item['dish']
            quantity = item['quantity']
            price = item['price']
            subtotal = quantity * price
            
            PurchaseItem.objects.create(
                purchase=purchase,
                dish=dish,
                quantity=quantity,
                price_at_purchase=price,
                subtotal=subtotal,
            )
            total_actual += subtotal
            
            # Deduct inventory for each ingredient
            for requirement in dish.recipe_requirements.all():
                ingredient = requirement.ingredient
                quantity_to_deduct = requirement.quantity_required * quantity
                
                # Use locked ingredient
                locked_ingredient = Ingredient.objects.select_for_update().get(pk=ingredient.pk)
                locked_ingredient.quantity_available -= quantity_to_deduct
                if locked_ingredient.quantity_available < 0:
                    locked_ingredient.quantity_available = 0
                locked_ingredient.save()
                
                # Update dish availability
                update_dish_availability_from_ingredient(locked_ingredient)
        
        # Update menu availability
        update_menu_availability()
        
        # Update purchase total (in case of rounding)
        purchase.total_price_at_purchase = total_actual
        purchase.save()
        
        # Clear session data
        del request.session['purchase_data']
        del request.session['purchase_total']
        
        messages.success(request, f'Purchase #{purchase.id} completed successfully!')
        return redirect('purchases:detail', pk=purchase.pk)
        
    except Dish.DoesNotExist:
        messages.error(request, 'One or more dishes are no longer available. Please try again.')
        return redirect('purchases:add')
    except Exception as e:
        messages.error(request, f'Purchase could not be completed: {str(e)}. Please try again.')
        return redirect('purchases:confirm')


# Purchases - List and Detail
class PurchaseListView(LoginRequiredMixin, ListView):
    model = Purchase
    template_name = 'delights/purchases/list.html'
    context_object_name = 'purchases'
    
    def get_queryset(self):
        queryset = Purchase.objects.select_related('user').prefetch_related('items__dish').order_by('-timestamp')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset


class PurchaseDetailView(LoginRequiredMixin, DetailView):
    model = Purchase
    template_name = 'delights/purchases/detail.html'
    context_object_name = 'purchase'
    
    def get_queryset(self):
        queryset = Purchase.objects.select_related('user').prefetch_related('items__dish')
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset


# Custom Login View with redirect logic
class LoginView(BaseLoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse_lazy('dashboard:index')
        else:
            return reverse_lazy('purchases:list')


# Dashboard (Admin only)
class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'delights/dashboard/index.html'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Revenue, cost, profit
        completed_purchases = Purchase.objects.filter(status='completed')
        total_revenue = completed_purchases.aggregate(Sum('total_price_at_purchase'))['total_price_at_purchase__sum'] or 0
        
        # Calculate cost from dish costs (using current dish costs as approximation)
        total_cost = 0
        for purchase_item in PurchaseItem.objects.filter(purchase__status='completed').select_related('dish'):
            total_cost += purchase_item.quantity * purchase_item.dish.cost
        
        profit = total_revenue - total_cost
        
        # Top selling dishes
        top_dishes = Dish.objects.annotate(
            total_sold=Sum('purchase_items__quantity', filter=Q(purchase_items__purchase__status='completed'))
        ).order_by('-total_sold')[:10]
        
        # Low stock ingredients (below 10 units)
        low_stock_ingredients = Ingredient.objects.filter(quantity_available__lt=10).order_by('quantity_available')[:10]
        
        context.update({
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'profit': profit,
            'top_dishes': top_dishes,
            'low_stock_ingredients': low_stock_ingredients,
        })
        
        return context


# User Management (Admin only)
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'delights/users/list.html'
    context_object_name = 'users'
    
    def test_func(self):
        return is_admin(self.request.user)


class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'delights/users/add.html'
    success_url = reverse_lazy('users:list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'User "{form.instance.username}" created successfully.')
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'is_staff', 'is_active']
    template_name = 'delights/users/edit.html'
    success_url = reverse_lazy('users:list')
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, f'User "{form.instance.username}" updated successfully.')
        return super().form_valid(form)


@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, pk):
    """Toggle active status of a user"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User "{user.username}" has been {status}.')
    return redirect('users:list')


@login_required
@user_passes_test(is_admin)
def user_reset_password(request, pk):
    """Reset user password (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for "{user.username}" has been reset.')
            return redirect('users:list')
    else:
        form = SetPasswordForm(user)
    
    return render(request, 'delights/users/reset_password.html', {
        'user': user,
        'form': form,
    })
