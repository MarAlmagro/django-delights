
# Structured Development Roadmap for Django Delights


# Development Phases

There are six sequential phases.

---

## Phase 1 — Project Setup & Core Models

**Purpose**  
Set up a clean Django project, define all core data models (Units, Ingredients, MenuItems, Menus, Purchases), and ensure migrations run correctly. This provides the foundation for all later features.

### Main tasks

#### 1. Create Django project and app
**Subtasks**
- Start project (`django-delights`)
- Create app (`delights`)
- Configure settings, templates path, static files, environment variables

#### 2. Implement all models
**Subtasks**
- `Unit` (with `is_active`)
- `Ingredient`
- `MenuItem` + `RecipeRequirements`
- `Menu`
- `Purchase` + `PurchaseItem`

#### 3. Create initial migrations and validate schema
**Subtasks**
- Run `makemigrations`
- Run `migrate`
- Fix any schema issues early

---

## Phase 2 — Admin-Only System Management (Units, Ingredients)

**Purpose**  
Create functional CRUD for Units and Ingredients, enforce business rules, and allow administrators to configure the system baseline.

### Main tasks

#### 1. Units CRUD (admin only)
**Subtasks**
- List, Create, Edit, Toggle Active
- Use only active units in ingredient forms

#### 2. Ingredient CRUD
**Subtasks**
- Create/Edit Ingredient
- Ensure form filters active units only

#### 3. Inventory Adjustment (staff + admin)
**Subtasks**
- Add adjustment field (+X / –X)
- Recalculate MenuItem/Menu availability after adjustment

---

## Phase 3 — Menu Items and Recipe Requirements

**Purpose**  
Implement CRUD for MenuItems and the two-step recipe creation flow. Add cost calculation and ingredient-dependency logic.

### Main tasks

#### 1. MenuItem CRUD
**Subtasks**
- Create, List, Detail, Edit
- Admin controls price

#### 2. Recipe Requirements
**Subtasks**
- Add/remove ingredients
- Validate `quantity_required`
- Recalculate MenuItem cost and availability automatically

#### 3. MenuItem availability logic
**Subtasks**
- Auto-update based on ingredient quantities
- Display availability in templates

---

## Phase 4 — Menus (Composite Items)

**Purpose**  
Implement menu composition, pricing, and availability logic. Build editing workflows for admin and staff.

### Main tasks

#### 1. Menu CRUD
**Subtasks**
- Create, List, Detail, Edit
- Admin controls price

#### 2. Menu composition management
**Subtasks**
- Add/remove MenuItems
- Recalculate cost and availability

#### 3. Templates & UX
**Subtasks**
- Show all composition data clearly
- Visual indicators for availability

---

## Phase 5 — Purchase Workflow (3-Step Atomic Flow)

**Purpose**  
Build the complete purchasing system with validation, price freezing, inventory deduction, and concurrency safety.

### Main tasks

#### 1. Step 1: Purchase creation
**Subtasks**
- Staff selects available MenuItems only
- Validate requested quantities

#### 2. Step 2: Confirmation page
**Subtasks**
- Display summary
- Do not modify inventory yet

#### 3. Step 3: Atomic finalization
**Subtasks**
- Use `transaction.atomic()`
- Lock ingredient rows (`select_for_update`)
- Deduct inventory
- Freeze `price_at_purchase`
- Redirect to Purchase Detail

---

## Phase 6 — Users, Authentication, Dashboard, Testing

**Purpose**  
Finish the application with full user management, permissions, admin dashboards, and a complete test suite.

### Main tasks

#### 1. User Management (admin only)
**Subtasks**
- List users
- Create users
- Edit `is_staff`, `is_active`
- Toggle active/inactive
- Reset passwords

#### 2. Authentication & redirection
**Subtasks**
- Login/Logout
- Admin → dashboard
- Staff → purchase list

#### 3. Dashboard (admin only)
**Subtasks**
- Revenue, cost, profit metrics
- Low-stock ingredients
- Top-selling MenuItems

#### 4. Test suite
**Subtasks**
- Model tests
- Availability logic tests
- Purchase flow integration tests
- Permission tests
