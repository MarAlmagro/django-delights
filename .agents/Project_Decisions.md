# Django Delights – Project Decisions (Updated Draft)

This document centralizes all decisions required before implementing the Django Delights application.
---

## 1. Data Model (updated)

### Unit

* name (e.g. g, kg, ml, l, unit)
* description (e.g. gram, kilogram, milliliter, liter, unit)
* is_active (boolean; units are never deleted, only activated/deactivated)

### Ingredient

* name
* unit (FK to Unit)
* price_per_unit (cost per unit of measurement)
* quantity_available (in same unit)

### RecipeRequirement

* dish (FK)
* ingredient (FK)
* quantity_required (must match ingredient unit)
* Used for cost calculation.

### Menu

* name
* description (optional)
* dishes (many-to-many with Dish)
* cost (auto-calculated: sum of dishes costs)
* price (manual selling price, auto-filled with global margin on creation; editable only by admin)

### Dish

* name
* description (optional)
* cost (auto-calculated: sum of ingredients costs)
* price (manual selling price, auto-filled with global margin on creation; editable only by admin)

### Purchase

* user (FK to Django user)
* timestamp
* total_price_at_purchase (sum of line items)
* status (optional: e.g. completed, cancelled)
* notes (optional: free text)

### PurchaseItem

* purchase (FK to Purchase)
* dish (FK to Dish)
* quantity
* price_at_purchase (manual price copied per unit at the moment)
* subtotal (auto-calculated: quantity * price_at_purchase)

---

## 2. Business Rules (refined)

### Purchases
* A purchase is only allowed if all required ingredients are available at the moment of confirmation.
* The confirmation step is atomic. The system uses a database transaction and row locking to ensure consistency during simultaneous purchases.
* During confirmation, the system revalidates availability, deducts inventory, records Purchase and PurchaseItems, and stores price snapshots (price_at_purchase and subtotal).
* Historical purchases never change after creation, regardless of later price updates.

### Availability
* Units follow soft-delete rules via is_active.
* Only active units can be assigned to ingredients.
* Dish has a boolean is_available. It is true only if every ingredient in its RecipeRequirements has enough quantity to produce at least one unit.
* Menu has a boolean is_available. It is true only if every Dish associated is available.
* These booleans are maintained automatically when inventory changes or when recipes or ingredient prices change.
* Staff only sees items with is_available true when creating a purchase.

### Pricing
* Ingredient has only cost data (price_per_unit).
* Dish cost is computed from ingredient costs. Menu cost is computed from Dishes.
* Selling price for Dish and Menu is generated at creation using the global margin (default 0.20).
* Staff cannot edit selling prices. Only admin can edit prices after creation.
* When ingredient prices change, Dish and Menu costs and current selling prices are recalculated.
* Purchases always use the stored price_at_purchase values and never recalc past data.

### Inventory updates
* Inventory is reduced only when a purchase is confirmed.
* After inventory deduction, availability is recalculated automatically for Dishes and Menus.

### Concurrency
* Multiple users may prepare purchases in parallel.
* Only the confirmation step is exclusive, enforced through row locking of the ingredient records used in the order.
* If stock becomes insufficient while waiting for the lock, the system rejects the purchase cleanly.
* Purchase allowed only if inventory is sufficient.
* Inventory updated when purchase is recorded.
* Behaviour on simultaneous purchases.
* Behaviour when ingredient prices change.
* Cost of Dish: manual vs computed from ingredients.

---

## 3. User Roles and Permissions (updated)

### Roles

* Admin: full access to all features.
* Staff: operational access only.

### Admin Permissions

* Manage ingredients, units, menu items, recipe requirements, menus.
* Modify price_per_unit and selling prices.
* Full access to dashboard.
* Full user management.

### Staff Permissions

* Create and update Dish, RecipeRequirement, and Menu without modifying selling prices.
* Selling price is auto-generated at creation time using global margin and cannot be edited by staff.
* Register purchases.
* Adjust inventory quantities.
* View inventory, dishes, recipes, and menus.

### Pricing Constraints

* Selling price >= calculated cost.
* Staff cannot edit the selling price.
* When creating Dish or Menu, system auto-calculates the cost and generates a selling price using a global margin (e.g. 0.20).

---

## 4. Operational Flows

### Ingredient creation and modification  
* Ingredient edit separate from inventory adjustment.
* Staff may adjust inventory; only admin edits price_per_unit.
* Inventory adjustment triggers availability recalculation.

### Quantity adjustment flow  
* Dedicated view for changing quantity via +/- adjustment.

### Recipe creation workflow  
* Implemented in two steps: Two steps: create MenuItem/Menu → add ingredients.

### Purchase workflow  
* Staff selects Dishes and quantities. Only items with `is_available == true` are shown.  
* Before saving the purchase, a confirmation screen is displayed.  
* On confirmation, the system executes an atomic operation that:  
  - Locks required ingredient rows (`SELECT FOR UPDATE`).  
  - Revalidates availability in that exact moment.  
  - Deducts inventory from ingredients.  
  - Creates Purchase and PurchaseItems, storing price snapshots (`price_at_purchase` and `subtotal`).  
* After confirmation, the system redirects to the “Purchase detail” view.

### Purchase workflow error rules  
During confirmation, the purchase can fail for four reasons:

1. **Ingredient out of stock**  
   - Message: “Ingredient X is out of stock.”

2. **Dish no longer available**  
   - Triggered when one or more required ingredients no longer have sufficient quantity.  
   - Message: “Menu item Y is no longer available.”

3. **Menu no longer available**  
   - Triggered when one of its Dishes becomes unavailable.  
   - Message: “Menu Z is no longer available.”

4. **Concurrent update during confirmation**  
   - Happens when another purchase modifies stock in the same moment.  
   - User-facing message:  
     “The purchase could not be completed because stock changed during confirmation. Please try again.”

* Errors are shown in the confirmation screen.  
* No partial changes are applied if an error occurs. Everything is rolled back atomically.

---

## 5. Views and Endpoints (refined)

All views require authentication.  

Only staff and admin users have access to the application.  

Admin users have extended permissions for editing, pricing, and user administration.

### Units (admin only)
* Unit List → /units/ (ListView)
* Create Unit → /units/add/ (CreateView)
* Edit Unit → /units/<id>/edit/ (UpdateView)
* Toggle active/inactive → /units/<id>/toggle-active/ (POST view)
Units are never deleted; deactivation hides them from ingredient forms.

### Inventory (Ingredients)
Active units only appear in ingredient forms.

#### Inventory List
* Displays all ingredients with name, unit, quantity_available, and price_per_unit.  
* Staff sees the “Adjust Inventory” action.  
* Admin sees both “Edit Ingredient” and “Adjust Inventory”.

URL: `/ingredients/`  
CBV: `ListView`

#### Edit Ingredient (admin only)
Allows editing name, unit, and price_per_unit.  
Quantity is not editable here.

URL: `/ingredients/<id>/edit/`  
CBV: `UpdateView`

#### Adjust Inventory (staff + admin)
Dedicated view for increasing or decreasing stock using an adjustment field (+X or –X).  
After the update, availability for Dishes and Menus is recalculated.

URL: `/ingredients/<id>/adjust/`  
CBV: `FormView`


### Dishes (dishes)

#### Dish List
Lists all Dishes with availability status.  
Staff sees “Edit Recipe”.  
Admin sees “Edit Dish” and “Delete”.

URL: `/dishes/`  
CBV: `ListView`

#### Dish Detail
Shows description, calculated cost, selling price, availability, and all ingredients used via RecipeRequirements.  
Provides a link to manage the recipe.

URL: `/dishes/<id>/`  
CBV: `DetailView`

#### Create Dish (staff + admin)
Creates the Dish object without ingredients.  
Recipe is added later.

URL: `/dishes/add/`  
CBV: `CreateView`

#### Edit Dish (admin only)
Allows editing fields including price (admin-only action).  
Ingredients are not managed here.

URL: `/dishes/<id>/edit/`  
CBV: `UpdateView`



### Recipe Requirements

#### Manage RecipeRequirements
Allows staff/admin to add or remove ingredients and define quantity_required.  
Managed one item at a time (no formsets for simplicity).

URL: `/dishes/<id>/requirements/`  
CBV: list + form pattern (`ListView` + `CreateView` style)



### Menus

#### Menu List
Lists all Menus with availability status.  
Staff can edit the composition.  
Admin can edit price, delete, and modify all fields.

URL: `/menus/`  
CBV: `ListView`

#### Menu Detail
Shows Menu composition, total cost, selling price, and availability.  
Includes a link to manage which Dishes belong to the menu.

URL: `/menus/<id>/`  
CBV: `DetailView`

#### Create Menu (staff + admin)
Creates the Menu object.  
Dishes are added separately.

URL: `/menus/add/`  
CBV: `CreateView`

#### Edit Menu (admin only)
Admin may update name, description, and selling price.

URL: `/menus/<id>/edit/`  
CBV: `UpdateView`

#### Manage Menu Composition
Allows staff and admin to add or remove Dishes from a Menu.

URL: `/menus/<id>/items/`  
CBV: list + simple add/remove actions



### Purchases

#### Purchase List
Admin sees all purchases.  
Staff sees only their own.

URL: `/purchases/`  
CBV: `ListView`

#### Add Purchase (step 1)
Staff selects quantities of available Dishes (`is_available = true`).  
Leads to the confirmation screen.

URL: `/purchases/add/`  
CBV: `FormView`

#### Purchase Confirmation (step 2)
Shows a summary before finalizing.  
Includes a “Confirm” action.

URL: `/purchases/confirm/`  
CBV: `FormView`

#### Final Confirmation (atomic)
Runs inside `transaction.atomic()` using row locking:  
* Revalidates availability  
* Deducts stock  
* Creates Purchase + PurchaseItems with frozen prices  
Redirects to Purchase Detail.

URL: `/purchases/confirm/final/`  
CBV: POST handler

#### Purchase Detail
Displays summary of the completed purchase using historical prices.

URL: `/purchases/<id>/`  
CBV: `DetailView`

### Dashboard (admin only)
Admin-only overview with:  
* Revenue  
* Total cost  
* Profit estimate  
* Top-selling Dishes  
* Low-stock ingredients  
Rendered as a simple numeric summary.

URL: `/dashboard/`  
CBV: `TemplateView`

### Authentication and Access Control
* Entire application requires login.  
* Staff and admin share most views, but admin sees additional edit/delete/price actions.  
* Unauthorized actions show 403 or redirect to login.



### User Management (admin only)

#### User List
Shows all users with username, email, role, and active status.

URL: `/users/`  
CBV: `ListView`

#### Create User
Admin can create new staff or admin accounts.  
Uses Django’s `UserCreationForm`.

URL: `/users/add/`  
CBV: `CreateView`

#### Edit User
Admin can edit username, email, is_staff, and is_active.  
Password is not edited here.

URL: `/users/<id>/edit/`  
CBV: `UpdateView`

#### Activate / Deactivate User
Toggles `is_active` without deleting the user.

URL: `/users/<id>/toggle-active/`  
CBV: POST handler

#### Reset User Password
Admin can set a new password for any user.  
Uses Django’s `SetPasswordForm`.

URL: `/users/<id>/reset-password/`  
CBV: `FormView`


---

## 6. Navigation and Templates (refined)

### Navbar Structure
The navbar is visible to all authenticated users (staff and admin).  
It provides quick access to the main operational sections:

**Left side**
- Units → `/units/`
- Inventory → `/ingredients/`
- Dishes → `/dishes/`
- Menus → `/menus/`
- Purchases → `/purchases/`
- Dashboard (admin only) → `/dashboard/`
- User Management (admin only) → `/users/`

**Right side**
- Logged-in username  
- Logout link (`/accounts/logout/`)

The navbar indicates the active section for better usability.

### Bootstrap Base Layout
A shared `base.html` template includes:
- Bootstrap CSS/JS  
- Navbar block  
- Content block  
- Flash messages using Django’s messages framework  
- Optional footer  
- Consistent container spacing (`container` / `container-fluid`)

All other templates extend this base layout:
```django
{% extends "base.html" %}
```

### Template organization

```plaintext
templates/
    delights/
        base.html
        units/
            list.html
            add.html
            edit.html
            delete.html
        ingredients/
            list.html
            edit.html
            adjust.html
        dishes/
            list.html
            detail.html
            add.html
            edit.html
            requirements.html
        menus/
            list.html
            detail.html
            add.html
            edit.html
            items.html
        purchases/
            list.html
            add.html
            confirm.html
            detail.html
        dashboard/ (admin only)
            index.html
        users/  (admin only)
            list.html
            add.html
            edit.html
            reset_password.html
```

---

## 7. Authentication Decisions (refined)

* The entire application requires authentication; no public pages exist.  
* There is **no user self-registration**. Only admin users can create new staff/admin accounts through the internal User Management views.  
* Authentication uses Django’s built-in LoginView and LogoutView.  
* After login, users are redirected to the dashboard (admin) or the purchase list (staff).  
* Access control is enforced using Django permissions:  
  * Admin users (superusers) have full access.  
  * Staff users have restricted access: they may adjust inventory, manage recipes, manage menu compositions, and register purchases, but cannot edit prices or users.  
* Attempts to access unauthorized pages return 403 or redirect to login if unauthenticated.

---

## 8. URL Structure (refined)

Below is the complete URL structure for the Django Delights application, matching all defined views, roles, and workflows.

### Units (admin only)
- `/units/`
- `/units/add/`
- `/units/edit/`
- `/units/delete/`

### Ingredients
- `/ingredients/`  
  Ingredient list  
- `/ingredients/add/`  
  Create ingredient (admin only)  
- `/ingredients/<id>/edit/`  
  Edit ingredient (admin only)  
- `/ingredients/<id>/adjust/`  
  Adjust inventory (staff + admin)

### Dishes
- `/dishes/`  
  Dish list  
- `/dishes/add/`  
  Create Dish  
- `/dishes/<id>/`  
  Dish detail  
- `/dishes/<id>/edit/`  
  Edit Dish (admin only)  
- `/dishes/<id>/requirements/`  
  Manage RecipeRequirements (staff + admin)

### Menus
- `/menus/`  
  Menu list  
- `/menus/add/`  
  Create Menu  
- `/menus/<id>/`  
  Menu detail  
- `/menus/<id>/edit/`  
  Edit Menu (admin only)  
- `/menus/<id>/items/`  
  Manage Menu composition (staff + admin)

### Purchases
- `/purchases/`  
  Purchase list  
- `/purchases/add/`  
  Purchase creation (step 1: select items)  
- `/purchases/confirm/`  
  Purchase confirmation screen (step 2)  
- `/purchases/confirm/final/`  
  Atomic purchase submission (step 3)  
- `/purchases/<id>/`  
  Purchase detail

### Dashboard
- `/dashboard/`  
  Admin dashboard

### Authentication
- `/accounts/login/`  
  Login (Django built-in)  
- `/accounts/logout/`  
  Logout (Django built-in)

### User Management (admin only)
- `/users/`  
  User list  
- `/users/add/`  
  Create user  
- `/users/<id>/edit/`  
  Edit user  
- `/users/<id>/toggle-active/`  
  Activate/deactivate user  
- `/users/<id>/reset-password/`  
  Reset user password


---


## 9. Git Strategy (refined)

The project uses a simple and educational Git workflow with one stable main branch and short-lived feature branches.  
Commit messages follow a consistent, meaningful format.

### Branching Model
* **main**  
  The stable, production-ready branch.  
  Only merged into after features are complete and tested.

* **feature/<short-description>**  
  Used for developing individual features (e.g., `feature/dish-crud`, `feature/purchases-flow`).  
  Created from `main` and merged back through clean commits.

* **bugfix/<short-description>** (optional)  
  Used to fix specific issues found during development.



### Commit Naming Strategy
Commits follow a clear and descriptive structure inspired by conventional commit style:
    <type>: <short action summary>

* Allowed types:
    - **feat:** new feature added  
    - **fix:** a bug or incorrect behavior fixed  
    - **docs:** documentation changes (README, .md updates)  
    - **style:** formatting or template updates (no logic changes)  
    - **refactor:** code restructuring without changing behavior  
    - **chore:** dependency updates, config changes  
    - **tests:** adding or updating tests  

* Examples:
    - feat: add Dish create and detail views
    - fix: correct inventory deduction logic in purchase confirmation
    - docs: update Views and Endpoints section in decisions file
    - refactor: extract availability logic into helper service

### Commit Sequence Guidelines
* Each commit should introduce **one logical change only**.  
* Avoid mixing unrelated changes in a single commit.  
* Commit early and often during feature development.  
* Before merging into `main`, ensure:  
  – feature branch is clean  
  – commit history is readable  
  – all tests pass (if tests exist)  

### Merging Rules
* Feature branches merge into **main** via fast-forward or a small number of squashed commits for clarity.  
* Merges must not break the project state.  
* After merging, the feature branch can be deleted.    

---

## 10. Development Fixtures (refined)

Fixtures are included to simplify development, testing, and demonstration of the application.  
They provide a reproducible starting point for inventory, menu structure, and user accounts.

### Fixture Scope
The project includes fixtures for:
* **Units**  
A basic set of measurement units used across ingredients.  
Example: gram, kilogram, milliliter, liter, unit.

* **Ingredients**  
Initial inventory entries with realistic quantities and prices.  
Used to demonstrate availability and cost calculations.

* **Dishes and RecipeRequirements**  
A small selection of dishes with their associated ingredients to demonstrate:  
    * automatic cost calculation  
    * availability logic  
    * recipe editing

* **Menus**  
A minimal set of menus that combine existing Dishes.

* **Users**  
Fixtures include:
    * one **admin user** (superuser)  
    * one **staff user**  

    Passwords are set to known development values (never used in production).

### Fixture Files
Fixtures are stored in:
```plaintext
delights/fixtures/
    units.json
    ingredients.json
    dishes.json
    menus.json
    users.json
```

### Usage
Fixtures are loaded using Django’s standard command:
```CLI
python manage.py loaddata units ingredients dishes menus users
```

### Purpose
Fixtures ensure:
* a predictable environment for testing  
* a ready-to-demo application without manual data entry  
* consistent behavior across branches and collaborators
---

## 11. Testing Strategy (refined)

The project includes a focused but realistic suite of automated tests using Django’s testing framework (`django.test.TestCase`).  

The goal is to validate critical business logic, ensure correct permission handling, and demonstrate professional testing practices.

### 1. Model Tests
Focused unit tests verifying model behavior in isolation:

**Ingredient**
* price_per_unit stored correctly  
* quantity adjustments reflected properly  
* availability recalculation triggered

**Dish**
* cost computed correctly from RecipeRequirements  
* price updated using the global margin  
* availability rules (sufficient ingredients → available, otherwise not)

**Menu**
* cost computed as the sum of Dishes  
* availability based on Dishes  
* price update logic

**Purchase and PurchaseItem**
* subtotal calculation consistency  
* price_at_purchase freezing behavior

### 2. Inventory Logic Tests
Tests that directly validate the logic controlling ingredient availability and its cascading effects:

* Ingredient becomes unavailable → related Dishes become unavailable  
* Dish unavailable → related Menus become unavailable  
* Adjusting inventory updates availability correctly  
* Edge cases with exact-quantity availability

### 3. Purchase Flow Tests (Integration)
End-to-end tests covering the multi-step purchase process:

* Step 1: selecting items  
* Step 2: confirmation page  
* Step 3: atomic finalization with `transaction.atomic()`  

Tests include:
* Successful purchase reduces ingredient stock  
* Frozen prices stored correctly  
* Purchase detail page reflects historical prices  
* Attempt to buy unavailable Dish raises correct error  
* Attempt to buy an Item that became unavailable mid-process is blocked

### 4. Concurrency Tests (Advanced Optional)
Testing concurrency with Django’s transaction management:

* Two simulated users attempt the same purchase simultaneously  
* Row locking ensures only one purchase succeeds  
* Second purchase receives the concurrency-safe error message  
(Useful for demonstrating deeper Django knowledge)

### 5. Permission Tests
Ensuring correct access control for staff vs admin:

* Staff cannot edit prices  
* Staff cannot edit users  
* Staff can adjust inventory  
* Admin can access all views  
* Unauthenticated users redirected to login  
* Unauthorized actions return 403

### 6. View Tests (Optional)
Light tests verifying that key views respond correctly:

* Dish list loads  
* Menu detail loads  
* Purchase list loads (with role filtering)  
* Dashboard loads for admin only

### 7. Fixture-Based Testing Support
Test suite uses project fixtures as a repeatable baseline.  
Each test class loads fixtures for consistent data setup.

---

## Pending Notes and Decisions

(Section to accumulate interim items requiring review.)
