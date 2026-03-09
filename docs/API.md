# REST API Guide

The Django Delights REST API provides programmatic access to all resources in the system. It is built with Django REST Framework and uses JWT authentication.

> **AI Disclosure:** This documentation was generated with the assistance of AI tools and reviewed by the project author.

---

## Table of Contents

- [Authentication](#authentication)
- [Available Endpoints](#available-endpoints)
- [Health Check](#health-check)
- [Units](#units)
- [Ingredients](#ingredients)
- [Dishes](#dishes)
- [Menus](#menus)
- [Purchases](#purchases)
- [Dashboard](#dashboard)
- [Pagination](#pagination)
- [Rate Limiting](#rate-limiting)
- [Error Codes](#error-codes)
- [Interactive Documentation](#interactive-documentation)

---

## Authentication

The API uses **JWT (JSON Web Tokens)** via SimpleJWT. Authentication is required for all endpoints except the health check.

### Obtain Tokens

```bash
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Use the Access Token

Include the `Authorization` header in every request:

```bash
curl http://localhost:8000/api/v1/dishes/ \
  -H "Authorization: Bearer <access_token>"
```

### Refresh the Token

When the access token expires (default: 60 minutes), use the refresh token:

```bash
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

**Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Verify a Token

```bash
POST /api/v1/auth/token/verify/
Content-Type: application/json

{
  "token": "<access_token>"
}
```

### Token Configuration

| Parameter | Environment Variable | Default |
|---|---|---|
| Access token lifetime | `JWT_ACCESS_TOKEN_LIFETIME` | 60 minutes |
| Refresh token lifetime | `JWT_REFRESH_TOKEN_LIFETIME` | 7 days |
| Refresh token rotation | — | Enabled |
| Blacklist after rotation | — | Enabled |

---

## Available Endpoints

All endpoints are prefixed with `/api/v1/`.

| Endpoint | Methods | Permissions | Description |
|---|---|---|---|
| `/api/v1/auth/token/` | POST | Public | Obtain JWT tokens |
| `/api/v1/auth/token/refresh/` | POST | Public | Refresh access token |
| `/api/v1/auth/token/verify/` | POST | Public | Verify a token |
| `/api/v1/health/` | GET | Public | Health check |
| `/api/v1/units/` | GET, POST | Auth (admin for writes) | Unit CRUD |
| `/api/v1/units/{id}/` | GET, PUT, PATCH | Auth (admin for writes) | Unit detail/edit |
| `/api/v1/units/{id}/toggle_active/` | POST | Admin | Toggle unit active status |
| `/api/v1/ingredients/` | GET, POST | Staff or Admin | Ingredient CRUD |
| `/api/v1/ingredients/{id}/` | GET, PUT, PATCH, DELETE | Staff or Admin | Ingredient detail/edit |
| `/api/v1/ingredients/{id}/adjust/` | POST | Staff or Admin | Adjust inventory |
| `/api/v1/dishes/` | GET, POST | Auth (admin for prices) | Dish CRUD |
| `/api/v1/dishes/{id}/` | GET, PUT, PATCH, DELETE | Auth (admin for prices) | Dish detail/edit |
| `/api/v1/dishes/{id}/add_requirement/` | POST | Auth | Add recipe requirement |
| `/api/v1/dishes/{id}/remove_requirement/{req_id}/` | DELETE | Auth | Remove recipe requirement |
| `/api/v1/dishes/available/` | GET | Auth | Available dishes only |
| `/api/v1/menus/` | GET, POST | Auth (admin for prices) | Menu CRUD |
| `/api/v1/menus/{id}/` | GET, PUT, PATCH, DELETE | Auth (admin for prices) | Menu detail/edit |
| `/api/v1/menus/{id}/add_dish/{dish_id}/` | POST | Auth | Add dish to menu |
| `/api/v1/menus/{id}/remove_dish/{dish_id}/` | DELETE | Auth | Remove dish from menu |
| `/api/v1/purchases/` | GET, POST | Auth (filtered by user) | List/create purchases |
| `/api/v1/purchases/{id}/` | GET | Auth (owner or admin) | Purchase detail |
| `/api/v1/dashboard/` | GET | Admin only | Metrics and analytics |

---

## Health Check

```bash
GET /api/v1/health/
```

No authentication required. Returns:

```json
{
  "status": "healthy"
}
```

---

## Units

### List Units

```bash
GET /api/v1/units/
Authorization: Bearer <token>
```

### Create Unit (Admin only)

```bash
POST /api/v1/units/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "kg",
  "description": "kilogram",
  "is_active": true
}
```

### Toggle Unit Active Status (Admin only)

```bash
POST /api/v1/units/{id}/toggle_active/
Authorization: Bearer <token>
```

---

## Ingredients

### List Ingredients

```bash
GET /api/v1/ingredients/
Authorization: Bearer <token>
```

### Create Ingredient

```bash
POST /api/v1/ingredients/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Flour",
  "unit": 1,
  "price_per_unit": "1.50",
  "quantity_available": "100.00"
}
```

### Adjust Inventory

Add or subtract from an ingredient's stock:

```bash
POST /api/v1/ingredients/{id}/adjust/
Authorization: Bearer <token>
Content-Type: application/json

{
  "adjustment": "50.00",
  "action": "add"
}
```

The `action` field can be `"add"` or `"subtract"`. When inventory is adjusted, availability of affected dishes is automatically recalculated.

---

## Dishes

### List Dishes

```bash
GET /api/v1/dishes/
Authorization: Bearer <token>
```

### Create Dish

```bash
POST /api/v1/dishes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Margherita Pizza",
  "description": "Classic pizza with tomato and mozzarella",
  "price": "12.00"
}
```

Cost is auto-calculated when recipe requirements are added. Availability is set to `false` until ingredients are added and sufficient stock exists.

### Add Recipe Requirement

```bash
POST /api/v1/dishes/{id}/add_requirement/
Authorization: Bearer <token>
Content-Type: application/json

{
  "ingredient": 1,
  "quantity_required": "0.25"
}
```

If the ingredient already exists in the recipe, the quantity is updated. After adding/updating, dish cost and availability are recalculated automatically.

### Remove Recipe Requirement

```bash
DELETE /api/v1/dishes/{id}/remove_requirement/{requirement_id}/
Authorization: Bearer <token>
```

### List Available Dishes Only

```bash
GET /api/v1/dishes/available/
Authorization: Bearer <token>
```

---

## Menus

### List Menus

```bash
GET /api/v1/menus/
Authorization: Bearer <token>
```

### Create Menu

```bash
POST /api/v1/menus/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Family Dinner",
  "description": "For 4 people",
  "price": "35.00",
  "dishes": [1, 2, 3]
}
```

### Add Dish to Menu

```bash
POST /api/v1/menus/{id}/add_dish/{dish_id}/
Authorization: Bearer <token>
```

### Remove Dish from Menu

```bash
DELETE /api/v1/menus/{id}/remove_dish/{dish_id}/
Authorization: Bearer <token>
```

---

## Purchases

Purchases only allow read (GET) and create (POST) operations. They cannot be modified or deleted.

### List Purchases

```bash
GET /api/v1/purchases/
Authorization: Bearer <token>
```

- **Admin**: sees all purchases
- **Staff**: sees only their own purchases

### Create Purchase

Creating a purchase is an atomic operation that:
1. Validates all dishes are available
2. Verifies sufficient ingredient stock
3. Creates the purchase record with frozen prices
4. Deducts inventory
5. Recalculates availability

```bash
POST /api/v1/purchases/
Authorization: Bearer <token>
Content-Type: application/json

{
  "items": [
    {"dish_id": 1, "quantity": 2},
    {"dish_id": 3, "quantity": 1}
  ],
  "notes": "Table 5"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "user": "admin",
  "timestamp": "2025-03-09T15:30:00Z",
  "total_price_at_purchase": "36.00",
  "status": "completed",
  "notes": "Table 5",
  "items": [
    {
      "dish": "Margherita Pizza",
      "quantity": 2,
      "price_at_purchase": "12.00",
      "subtotal": "24.00"
    },
    {
      "dish": "Caesar Salad",
      "quantity": 1,
      "price_at_purchase": "12.00",
      "subtotal": "12.00"
    }
  ]
}
```

**Possible errors:**
- `400 Bad Request` — Dish not available or insufficient stock

---

## Dashboard

Admin-only endpoint.

```bash
GET /api/v1/dashboard/
Authorization: Bearer <token>
```

**Response:**

```json
{
  "total_revenue": "1250.00",
  "total_cost": "875.00",
  "total_profit": "375.00",
  "total_purchases": 42,
  "top_dishes": [
    {"dish__name": "Margherita Pizza", "total_sold": 28},
    {"dish__name": "Caesar Salad", "total_sold": 15}
  ],
  "low_stock_ingredients": [
    {"name": "Mozzarella", "quantity_available": "3.00", "unit__name": "kg"},
    {"name": "Tomatoes", "quantity_available": "5.00", "unit__name": "kg"}
  ]
}
```

The low-stock threshold is configurable via the `LOW_STOCK_THRESHOLD` environment variable (default: 10).

---

## Pagination

The API uses page-number pagination. By default, **20 results per page** are returned.

```bash
GET /api/v1/dishes/?page=2
```

**Paginated response format:**

```json
{
  "count": 45,
  "next": "http://localhost:8000/api/v1/dishes/?page=3",
  "previous": "http://localhost:8000/api/v1/dishes/?page=1",
  "results": [...]
}
```

---

## Rate Limiting

The API applies throttling to protect against abuse:

| Environment | Anonymous | Authenticated |
|---|---|---|
| Development | 1000/hour | 10000/hour |
| Production | 100/hour | 1000/hour |

---

## Error Codes

| Code | Meaning |
|---|---|
| `200 OK` | Successful operation |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Invalid data or business rule violation |
| `401 Unauthorized` | Token missing or expired |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Resource not found |
| `429 Too Many Requests` | Rate limit exceeded |

---

## Interactive Documentation

With the server running, you can access automatically generated interactive documentation:

- **Swagger UI**: http://localhost:8000/api/docs/ — Test endpoints directly from the browser
- **ReDoc**: http://localhost:8000/api/redoc/ — Readable documentation format
- **OpenAPI Schema (JSON)**: http://localhost:8000/api/schema/ — Downloadable raw schema
