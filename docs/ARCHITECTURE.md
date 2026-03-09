# Project Architecture

Technical documentation covering the architecture, data models, permissions system, and design decisions of Django Delights.

> **AI Disclosure:** This documentation was generated with the assistance of AI tools and reviewed by the project author.

---

## Table of Contents

- [Overview](#overview)
- [Data Models](#data-models)
- [Web Views](#web-views)
- [REST API](#rest-api)
- [Permissions System](#permissions-system)
- [Business Logic](#business-logic)
- [Settings Configuration](#settings-configuration)
- [HTML Templates](#html-templates)
- [Design Decisions](#design-decisions)

---

## Overview

Django Delights is a monolithic Django application that exposes two interfaces:

1. **Web Interface** — Traditional Django views (Class-Based Views + Function-Based Views) with HTML templates
2. **REST API** — Django REST Framework ViewSets with JWT authentication

Both interfaces share the same models and business logic.

```
┌──────────────────────────────────────────────────┐
│                    Client                         │
│           (Browser / App / curl)                  │
└────────┬─────────────────────┬───────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────────┐
│   Web Views     │   │    REST API          │
│  (CBV + FBV)    │   │  (DRF ViewSets)      │
│  Session Auth   │   │  JWT Auth            │
└────────┬────────┘   └──────────┬──────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────────────┐
│              Business Logic Layer                  │
│  (views.py helper functions: cost calculation,    │
│   availability checks, inventory updates)         │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│                 Data Models                        │
│  Unit, Ingredient, Dish, RecipeRequirement,       │
│  Menu, Purchase, PurchaseItem                     │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│               Database                            │
│   SQLite (dev) / PostgreSQL (prod)                │
└──────────────────────────────────────────────────┘
```

---

## Data Models

The application defines **7 models** in `delights/models.py`:

### Entity Relationship Diagram

```
Unit (1) ──────< Ingredient (1) ──────< RecipeRequirement >────── (1) Dish
                                                                      │
                                                           Dish >─────┤
                                                                      │
                                                           Menu >─< Dish
                                                             (M2M)

User (1) ──────< Purchase (1) ──────< PurchaseItem >────── (1) Dish
```

### Unit

Represents a unit of measurement (e.g., gram, kilogram, liter, unit).

| Field | Type | Description |
|---|---|---|
| `name` | CharField(50) | Short identifier (unique), e.g. "g", "kg" |
| `description` | CharField(200) | Full name, e.g. "gram", "kilogram" |
| `is_active` | BooleanField | Soft-delete flag |

### Ingredient

Raw material with pricing and inventory tracking.

| Field | Type | Description |
|---|---|---|
| `name` | CharField(200) | Ingredient name |
| `unit` | ForeignKey(Unit) | Unit of measurement (PROTECT on delete) |
| `price_per_unit` | DecimalField(10,2) | Cost per unit |
| `quantity_available` | DecimalField(10,2) | Current stock level (default: 0) |

### Dish

A menu item with auto-calculated cost and availability.

| Field | Type | Description |
|---|---|---|
| `name` | CharField(200) | Dish name |
| `description` | TextField | Optional description |
| `cost` | DecimalField(10,2) | Auto-calculated from ingredients (default: 0) |
| `price` | DecimalField(10,2) | Selling price |
| `is_available` | BooleanField | True if all ingredients are sufficient (default: False) |

### RecipeRequirement

Links a Dish to an Ingredient with the required quantity.

| Field | Type | Description |
|---|---|---|
| `dish` | ForeignKey(Dish) | Parent dish (CASCADE on delete) |
| `ingredient` | ForeignKey(Ingredient) | Required ingredient (CASCADE on delete) |
| `quantity_required` | DecimalField(10,2) | Amount needed per dish serving |

**Constraint:** `unique_together = [["dish", "ingredient"]]`

### Menu

A composite item containing multiple dishes (like a combo meal).

| Field | Type | Description |
|---|---|---|
| `name` | CharField(200) | Menu name |
| `description` | TextField | Optional description |
| `dishes` | ManyToManyField(Dish) | Constituent dishes |
| `cost` | DecimalField(10,2) | Auto-calculated from dish costs (default: 0) |
| `price` | DecimalField(10,2) | Selling price |
| `is_available` | BooleanField | True if all dishes are available (default: False) |

### Purchase

An order record tied to a user.

| Field | Type | Description |
|---|---|---|
| `user` | ForeignKey(User) | Buyer (PROTECT on delete) |
| `timestamp` | DateTimeField | Auto-set creation time |
| `total_price_at_purchase` | DecimalField(10,2) | Total frozen at purchase time |
| `status` | CharField(20) | "completed" or "cancelled" |
| `notes` | TextField | Optional notes |

### PurchaseItem

An individual line item in a purchase with frozen price.

| Field | Type | Description |
|---|---|---|
| `purchase` | ForeignKey(Purchase) | Parent purchase (CASCADE on delete) |
| `dish` | ForeignKey(Dish) | Purchased dish (PROTECT on delete) |
| `quantity` | PositiveIntegerField | Number of units |
| `price_at_purchase` | DecimalField(10,2) | Unit price at time of purchase |
| `subtotal` | DecimalField(10,2) | quantity * price_at_purchase |

---

## Web Views

Web views are in `delights/views.py` and use a mix of Class-Based Views (CBV) and Function-Based Views (FBV).

### View Inventory

| Entity | List | Create | Update | Detail | Special |
|---|---|---|---|---|---|
| Units | `UnitListView` (CBV) | `UnitCreateView` (CBV) | `UnitUpdateView` (CBV) | — | `unit_toggle_active` (FBV) |
| Ingredients | `IngredientListView` (CBV) | `IngredientCreateView` (CBV) | `IngredientUpdateView` (CBV) | — | `inventory_adjust` (FBV) |
| Dishes | `DishListView` (CBV) | `DishCreateView` (CBV) | `DishUpdateView` (CBV) | `DishDetailView` (CBV) | `manage_recipe_requirements` (FBV) |
| Menus | `MenuListView` (CBV) | `MenuCreateView` (CBV) | `MenuUpdateView` (CBV) | `MenuDetailView` (CBV) | `manage_menu_items` (FBV) |
| Purchases | `PurchaseListView` (CBV) | `purchase_create` (FBV) | — | `PurchaseDetailView` (CBV) | `purchase_confirm`, `purchase_finalize` (FBV) |
| Users | `UserListView` (CBV) | `UserCreateView` (CBV) | `UserUpdateView` (CBV) | — | `user_toggle_active`, `user_reset_password` (FBV) |
| Dashboard | `DashboardView` (CBV) | — | — | — | — |
| Auth | `LoginView` (CBV) | — | — | — | — |

### URL Organization

URLs are split across multiple files for clarity:

- `delights/urls.py` — Units (`/units/`)
- `delights/urls_ingredients.py` — Ingredients (`/ingredients/`)
- `delights/urls_dishes.py` — Dishes (`/dishes/`)
- `delights/urls_menus.py` — Menus (`/menus/`)
- `delights/urls_purchases.py` — Purchases (`/purchases/`)
- `delights/urls_dashboard.py` — Dashboard (`/dashboard/`)
- `delights/urls_users.py` — Users (`/users/`)

All are included in `django_delights/urls.py` with their respective namespaces.

---

## REST API

The API is in `delights/api/` and consists of:

### Files

- **`views.py`** — ViewSets for all models + HealthCheckView + DashboardView
- **`serializers.py`** — DRF serializers (list, detail, create variants for each model)
- **`urls.py`** — Router-based URL configuration under `/api/v1/`
- **`permissions.py`** — Custom permission classes

### ViewSets

| ViewSet | Model | Key Features |
|---|---|---|
| `UnitViewSet` | Unit | Full CRUD, `toggle_active` action |
| `IngredientViewSet` | Ingredient | Full CRUD, `adjust` action for inventory |
| `DishViewSet` | Dish | Full CRUD, `add_requirement`, `remove_requirement`, `available` actions |
| `MenuViewSet` | Menu | Full CRUD, `add_dish`, `remove_dish` actions |
| `PurchaseViewSet` | Purchase | GET + POST only, atomic creation with inventory deduction |
| `HealthCheckView` | — | No auth required, returns `{"status": "healthy"}` |
| `DashboardView` | — | Admin only, aggregated metrics |

### Serializer Variants

Each model uses different serializers depending on the action:

- **List serializers** — Lightweight, for listing (e.g., `DishListSerializer`)
- **Detail serializers** — Full data with nested relations (e.g., `DishSerializer`)
- **Create serializers** — Write-optimized (e.g., `DishCreateSerializer`, `PurchaseCreateSerializer`)

---

## Permissions System

### Web Views

Web views use Django's built-in mixins:

- `LoginRequiredMixin` — Requires authentication
- `UserPassesTestMixin` with `is_admin()` — Restricts to superusers
- `@login_required` decorator — For function-based views
- `@user_passes_test(is_admin)` — For admin-only FBVs

A reusable `AdminRequiredMixin` is defined in `delights/mixins.py`.

### API Permissions

Custom permission classes in `delights/api/permissions.py`:

| Permission | Description |
|---|---|
| `IsAdminUser` | Only superusers |
| `IsAdminOrReadOnly` | Any authenticated user can read; only admins can write |
| `IsStaffOrAdmin` | Staff or superuser required |
| `IsOwnerOrAdmin` | Object owner or superuser (used for purchases) |
| `CanEditPrice` | Any staff can write, but only admins can include `price` in the payload |

### Permission Matrix

| Resource | Read | Create | Update | Update Price | Delete |
|---|---|---|---|---|---|
| Units | Any auth | Admin | Admin | Admin | Admin |
| Ingredients | Staff+ | Staff+ | Staff+ | Staff+ | Staff+ |
| Dishes | Any auth | Staff+ | Staff+ | Admin | Staff+ |
| Menus | Any auth | Staff+ | Staff+ | Admin | Staff+ |
| Purchases | Owner/Admin | Any auth | — | — | — |
| Dashboard | Admin | — | — | — | — |

---

## Business Logic

Business logic functions are defined in `delights/views.py` and shared between web views and the API:

### Cost Calculation

- **`calculate_dish_cost(dish)`** — Sums `ingredient.price_per_unit * requirement.quantity_required` for all recipe requirements
- **`update_menu_cost(menu)`** — Sums `dish.cost` for all dishes in the menu

### Availability Checks

- **`check_dish_availability(dish)`** — Returns `True` if every ingredient has `quantity_available >= quantity_required`
- **`check_menu_availability(menu)`** — Returns `True` if all dishes are available and the menu has at least one dish
- **`update_dish_availability(dish)`** — Recalculates cost and availability, saves the dish
- **`update_dish_availability_from_ingredient(ingredient)`** — Updates all dishes that use the given ingredient
- **`update_menu_availability(menu=None)`** — Updates one or all menus

### Global Margin

`GLOBAL_MARGIN` is set to `0.20` (20%) as a module-level constant in `views.py`. It's also configurable via the `GLOBAL_MARGIN` environment variable in the split settings (`base.py`).

When a dish's price is `0` and its cost becomes positive (after adding recipe requirements), the price is automatically suggested as `cost * (1 + GLOBAL_MARGIN)`.

---

## Settings Configuration

### Simple Settings (`django_delights/settings.py`)

A standalone file for minimal development:
- SQLite database
- Minimal INSTALLED_APPS (no DRF, no JWT)
- DEBUG=True with insecure default SECRET_KEY
- Static files from `/static/`

### Split Settings (`django_delights/settings/`)

**`base.py`** — Shared across all environments:
- Full INSTALLED_APPS including `rest_framework`, `rest_framework_simplejwt`, `drf_spectacular`, `corsheaders`
- WhiteNoise middleware for static files
- CORS middleware
- REST Framework configuration (JWT + session auth, pagination, throttling, OpenAPI schema)
- SimpleJWT configuration (token lifetimes, rotation, blacklisting)
- drf-spectacular configuration (API title, version, tags)
- Logging configuration (console handler, per-module levels)
- Business settings (GLOBAL_MARGIN, LOW_STOCK_THRESHOLD)

**`dev.py`** — Development overrides:
- DEBUG=True, permissive ALLOWED_HOSTS
- SQLite database
- Simple static file storage (no hashing)
- Console email backend
- CORS_ALLOW_ALL_ORIGINS=True
- Relaxed throttle rates (1000/10000 per hour)
- Debug-level logging
- Django Debug Toolbar ready (commented out)

**`prod.py`** — Production overrides:
- DEBUG=False, ALLOWED_HOSTS from environment
- PostgreSQL via DATABASE_URL or individual variables (with dj-database-url)
- Full HTTPS security (HSTS, secure cookies, SSL redirect, X-Frame-Options DENY)
- CSRF_TRUSTED_ORIGINS from environment
- SMTP email backend
- Restricted CORS
- Optional Redis caching and session storage
- Strict throttle rates (100/1000 per hour)
- Verbose logging format

### Settings Selection

The `DJANGO_SETTINGS_MODULE` environment variable controls which settings are loaded:
- `django_delights.settings` — Simple settings (default in `manage.py`)
- `django_delights.settings.dev` — Split development settings
- `django_delights.settings.prod` — Split production settings

---

## HTML Templates

Templates are in `templates/` and organized by feature:

### Base Template

`templates/delights/base.html` provides the layout with:
- Navigation bar
- Flash messages
- Content block
- Footer

### Template Groups

| Directory | Templates | Description |
|---|---|---|
| `delights/dashboard/` | `index.html` | Admin analytics dashboard |
| `delights/dishes/` | `list`, `add`, `edit`, `detail`, `requirements` | Dish CRUD + recipe management |
| `delights/ingredients/` | `list`, `add`, `edit`, `adjust` | Ingredient CRUD + inventory adjustment |
| `delights/menus/` | `list`, `add`, `edit`, `detail`, `items` | Menu CRUD + dish management |
| `delights/purchases/` | `list`, `add`, `confirm`, `detail` | 3-step purchase workflow |
| `delights/units/` | `list`, `add`, `edit` | Unit CRUD |
| `delights/users/` | `list`, `add`, `edit`, `reset_password` | User management |
| `registration/` | `login` | Login page |

---

## Design Decisions

### Why Two Interfaces?

The web interface provides a traditional server-rendered UI suitable for direct use by restaurant staff. The REST API enables integration with external systems, mobile apps, or SPAs.

### Why Split Settings?

The simple `settings.py` allows quick development without configuring DRF/JWT. The split settings provide a production-grade setup with proper security, database, and API configuration. Both can coexist without conflict.

### Why `select_for_update()` in Purchases?

The purchase finalization process involves reading and modifying inventory across multiple ingredients. Without row-level locking, concurrent purchases could result in negative stock (race condition). `select_for_update()` ensures serialized access to ingredient rows during the transaction.

### Why Frozen Prices in PurchaseItem?

Dish prices can change over time. Storing `price_at_purchase` ensures historical accuracy — you can always determine the exact amount charged, regardless of subsequent price changes.

### Why ForeignKey PROTECT on Critical Relations?

- `Ingredient.unit` uses PROTECT to prevent deleting units that are in use
- `PurchaseItem.dish` uses PROTECT to preserve purchase history
- `Purchase.user` uses PROTECT to prevent deleting users with purchase records

This ensures referential integrity and prevents accidental data loss.

### Why URL Files Split by Entity?

Each entity has its own URL file (e.g., `urls_dishes.py`, `urls_menus.py`) with a dedicated namespace. This keeps URL configuration modular and avoids a single large URL file.
