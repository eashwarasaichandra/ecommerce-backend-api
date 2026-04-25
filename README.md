# NexShop E-Commerce Backend API 🚀

A production-grade RESTful E-Commerce backend built with **Python Flask**, **SQLAlchemy ORM**, and **JWT Authentication**. Designed to demonstrate real-world backend engineering skills including SQL JOINs, dynamic filtering, pagination, business-logic state machines, and global error handling.

---

## 🌟 Features

| Feature | Details |
|---|---|
| 🔐 JWT Authentication | Stateless auth with expiry, protected routes, role-based access |
| 🔍 Product Search & Filtering | Search by name, filter by category, min/max price, paginated |
| 📄 Pagination | All list endpoints support `?page=&limit=` params |
| 📦 Order Status System | State machine: `pending → shipped → delivered / cancelled` |
| 🧾 Order History (SQL JOIN) | Explicit JOIN across Users, Orders, OrderItems, Products |
| 🛒 Persistent Cart | DB-backed cart with add, update quantity, remove, clear |
| ⭐ Product Reviews | 1–5 star ratings with comments, average shown on product |
| 📊 Admin Dashboard Stats | SQL aggregation: revenue, top products, low-stock alerts |
| ⚠️ Global Error Handling | JSON responses for all errors (400/401/403/404/405/500) |
| 🧪 Input Validation | Email format, password strength, price/stock type checks |

---

## 🏗️ Architecture

```
E-Commerce Backend - Major Project/
├── app/
│   ├── __init__.py          # App factory, error handlers, blueprint registration
│   ├── config.py            # Environment-based config (SQLite → PostgreSQL)
│   ├── models.py            # SQLAlchemy models: User, Product, Order, Cart, Review
│   ├── utils.py             # JWT middleware, input validators, status transition logic
│   └── routes/
│       ├── auth_routes.py   # Register, Login, Profile
│       ├── product_routes.py# CRUD + Search + Filter + Reviews
│       ├── cart_routes.py   # Cart CRUD + quantity update
│       ├── order_routes.py  # Orders + status update + JOIN history
│       ├── admin_routes.py  # Admin stats dashboard
│       └── ui_routes.py     # Frontend serving
├── seed_db.py               # Pre-populates DB with sample products
├── run.py                   # Entry point
└── requirements.txt
```

```mermaid
graph TD
    Client[Frontend Client] --> Auth[/api/auth]
    Client --> Products[/api/products]
    Client --> Cart[/api/cart]
    Client --> Orders[/api/orders]
    Admin[Admin Client] --> AdminAPI[/api/admin]
    Auth --> UserDB[(Users Table)]
    Products --> ProdDB[(Products Table)]
    Cart --> CartDB[(Cart Table)]
    Orders --> OrderDB[(Orders + OrderItems)]
    AdminAPI --> AllTables[(SQL Aggregation)]
```

---

## 🛠️ Stack

- **Runtime**: Python 3.9+
- **Framework**: Flask 3.x + Flask-SQLAlchemy + Flask-Bcrypt
- **Auth**: PyJWT (HS256, 24h expiry)
- **Database**: SQLite (local) → PostgreSQL (production)
- **Deployment**: Gunicorn + Render

---

## 📥 Quick Start (Local)

```bash
# 1. Clone and create virtual environment
git clone <repo-url>
cd "E-Commerce Backend - Major Project"
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env         # then edit .env if needed

# 4. Seed the database
python fix.py
python seed_db.py

# 5. Run the server
python run.py
```

Open **http://127.0.0.1:5000** in your browser for the full frontend.

---

## 🔌 API Endpoints

### 🔐 Auth (`/api/auth`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register. Validates email format & password length |
| POST | `/api/auth/login` | Public | Returns JWT token (24h expiry) |
| GET | `/api/auth/profile` | Token | Get current user profile |

### 📦 Products (`/api/products`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/products/` | Public | List products. Supports `?search=`, `?category=`, `?min_price=`, `?max_price=`, `?page=`, `?limit=` |
| GET | `/api/products/<id>` | Public | Product detail with reviews & avg rating |
| POST | `/api/products/` | Admin | Add product |
| PUT | `/api/products/<id>` | Admin | Update product |
| DELETE | `/api/products/<id>` | Admin | Delete product |
| POST | `/api/products/<id>/reviews` | Token | Submit 1–5 star review |

**Example:**
```
GET /api/products?search=phone&category=Electronics&min_price=10000&max_price=50000&page=1&limit=10
```

### 🛒 Cart (`/api/cart`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/cart/` | Token | View cart with totals |
| POST | `/api/cart/add` | Token | Add item (increments if exists) |
| PUT | `/api/cart/update/<item_id>` | Token | Update item quantity |
| DELETE | `/api/cart/remove/<item_id>` | Token | Remove specific item |
| DELETE | `/api/cart/clear` | Token | Empty entire cart |

### 🧾 Orders (`/api/orders`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/orders/` | Token | Own order history |
| POST | `/api/orders/` | Token | Checkout (simulates payment gateway) |
| PUT | `/api/orders/<id>/status` | Admin | Update status: `pending→shipped→delivered/cancelled` |
| GET | `/api/orders/user/<user_id>` | Admin | Full order history for a user (SQL JOIN) |
| GET | `/api/orders/all` | Admin | All orders, paginated, filterable by status |

**Order Status Flow:**
```
pending → shipped → delivered
   └──────────────→ cancelled
```

**Example status update:**
```json
PUT /api/orders/5/status
{ "status": "shipped" }
```

### 📊 Admin (`/api/admin`)
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/admin/stats` | Admin | Revenue, user count, top products, low-stock alerts |

---

## 🔑 Authentication

All protected endpoints require a Bearer token in the header:
```
Authorization: Bearer <your-jwt-token>
```

Get a token by POSTing to `/api/auth/login`.

---

## ⚠️ Error Responses

All errors return consistent JSON:
```json
{
  "error": "Not Found",
  "message": "The requested resource was not found."
}
```

| Code | Meaning |
|---|---|
| 400 | Bad Request — missing/invalid fields |
| 401 | Unauthorized — missing or expired token |
| 403 | Forbidden — insufficient role (admin required) |
| 404 | Not Found |
| 409 | Conflict — e.g., invalid status transition |
| 500 | Internal Server Error |

---

## 👤 Author

**Eashwar Kancharla**
