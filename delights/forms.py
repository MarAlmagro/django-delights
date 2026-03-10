from django import forms
from django.core.exceptions import ValidationError

from .models import Unit, Ingredient, Dish, RecipeRequirement, Menu

# Validation error constants
ERROR_NAME_MIN_LENGTH = "Name must be at least 2 characters."
ERROR_PRICE_NEGATIVE = "Price cannot be negative."


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "unit", "price_per_unit"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": "200",
                    "required": True,
                }
            ),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "price_per_unit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit"].queryset = Unit.objects.filter(is_active=True)

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError(ERROR_NAME_MIN_LENGTH)
        return name

    def clean_price_per_unit(self):
        price = self.cleaned_data.get("price_per_unit")
        if price is not None and price < 0:
            raise ValidationError(ERROR_PRICE_NEGATIVE)
        return price


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ["name", "description", "price"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": "200",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError(ERROR_NAME_MIN_LENGTH)
        return name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError(ERROR_PRICE_NEGATIVE)
        return price


class RecipeRequirementForm(forms.ModelForm):
    class Meta:
        model = RecipeRequirement
        fields = ["ingredient", "quantity_required"]
        widgets = {
            "ingredient": forms.Select(attrs={"class": "form-select"}),
            "quantity_required": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }

    def clean_quantity_required(self):
        quantity = self.cleaned_data.get("quantity_required")
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        ingredient = cleaned_data.get("ingredient")

        if ingredient and hasattr(ingredient, "unit") and not ingredient.unit.is_active:
            raise ValidationError(
                f'Cannot use ingredient "{ingredient.name}" - its unit is inactive.'
            )

        return cleaned_data


class InventoryAdjustmentForm(forms.Form):
    adjustment = forms.DecimalField(
        label="Adjustment",
        max_digits=10,
        decimal_places=2,
        help_text="Enter positive number to add, negative to subtract",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ["name", "description", "price"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "maxlength": "200",
                    "required": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
            if len(name) < 2:
                raise ValidationError(ERROR_NAME_MIN_LENGTH)
        return name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError(ERROR_PRICE_NEGATIVE)
        return price


class PurchaseCreateForm(forms.Form):
    """Form for selecting dishes and quantities for purchase"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        available_dishes = Dish.objects.filter(is_available=True).order_by("name")
        for dish in available_dishes:
            self.fields[f"dish_{dish.pk}"] = forms.IntegerField(
                required=False,
                min_value=0,
                initial=0,
                label=dish.name,
                widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            )

    def clean(self):
        cleaned_data = super().clean()
        selected_items = {}
        for key, value in cleaned_data.items():
            if key.startswith("dish_") and value and value > 0:
                dish_id = int(key.split("_")[1])
                selected_items[dish_id] = value

        if not selected_items:
            raise forms.ValidationError("Please select at least one dish.")

        return cleaned_data
