# Restaurant Ordering DBMS

A full-stack **Flask + SQLite** restaurant ordering system with separate portals for customers and sales clerks. Built as a database systems course project — zero external services, one command to run.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)](https://www.sqlite.org)
[![Deploy](https://img.shields.io/badge/Live-Render-46E3B7)](https://restaurant-ordering-dbms.onrender.com/)

---

## 🌐 Live Website

**https://restaurant-ordering-dbms.onrender.com**

### Demo accounts

| Role | Login | Credentials |
|------|-------|-------------|
| **Sales Clerk** | Email + password | `ahmet@restaurant.local` / `clerk123` |
| **Customer** | Email + telephone | `demo@customer.local` / `5550000001` |
| **Customer** | — | Register a new account at `/register` |

> Free Render instances sleep after inactivity, so the first visit can take ~30 seconds to wake up.

---

## 📖 What it does

**Customers**
- Register with name, telephone and email — no password needed, the account is identified by email + telephone.
- Log in, see the live menu with prices and the remaining ingredient stock.
- Order up to five different dishes in one go. Every order is validated against stock, so the restaurant never accepts an order it cannot cook.

**Sales clerks**
- Log in to a dashboard with four tools:
  - **View all orders** — per-order values, daily revenue, revenue per customer and a grand total.
  - **Generate bills** — pick a date and a customer, get a printable bill with quantity and line totals.
  - **Reorder ingredients** — record a monthly restock (prices + quantities); the running stock is updated by the difference.
  - **Monthly report** — summarized spice / vegetable / meat purchases for a month.

**Under the hood**
- Every SQL statement uses parameterized placeholders — no string concatenation, so no SQL injection.
- Passwords are stored as PBKDF2-SHA256 hashes (Werkzeug), never plaintext.
- One SQLite connection per request, closed automatically at teardown.
- Session-based auth with explicit `customer` / `clerk` role checks on every protected route.
- The database is created and seeded automatically on first start; re-running is idempotent and never destroys existing rows.

---

## 🚀 Run it locally

```bash
git clone https://github.com/umutalperencengiz/restaurant-ordering-dbms.git
cd restaurant-ordering-dbms
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python backEnd.py
```

Open **http://127.0.0.1:5000**. `restaurant.db` is created next to `backEnd.py` with the menu, stock, a demo customer and a sales clerk.

### Deploy on Render

1. Create a **Web Service** pointing at this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn backEnd:app`
4. Add environment variable `SECRET_KEY` (any long random string). Optionally `FLASK_DEBUG=false`.

No database host, no MySQL, no credentials. SQLite ships with Python.

> **Note:** Render's free tier has an ephemeral disk, so `restaurant.db` resets to the seed data on each deploy. The seeded demo accounts above always work.

---

## 🗄 Database schema

```
SalesClerk         clerk_id, clerkName, email, password (PBKDF2 hash)
Customer           customer_id, customerName, telephoneNum, email
Item               item_id, name, price
ingredients        item_id, spice, vegetable, meat        -- grams per portion
orders             order_id, customer_id, name, quantity, date, totalPrice
order_ingredients  order_date, price_spice, price_vegetables, price_meat,
                   total_spice, total_vegetables, total_meat
```

`ingredients.item_id = 7` is a sentinel row that holds the **running stock**, separate from the per-dish usage rows. Placing an order subtracts `usage × quantity` from that row; a restock adds the quantities entered by the clerk.

Full DDL and seed menu: [`schema.sql`](schema.sql)

---

## 📁 Project structure

```
restaurant-ordering-dbms/
├── backEnd.py                        # Flask app: routes, auth, stock logic
├── schema.sql                        # SQLite DDL + seed menu/stock (idempotent)
├── requirements.txt                  # Flask, Werkzeug, gunicorn
├── Procfile                          # Render start command
├── runtime.txt                       # Python version pin
├── .env.example                      # Environment variable template
└── templates/
    ├── login.html                    # Clerk / customer login
    ├── register.html                 # Customer registration
    ├── order.html                    # Menu + multi-dish order form
    ├── sales_clerk_dashboard.html
    ├── view_orders.html              # Revenue reports
    ├── generate_bills.html
    ├── bill_template.html            # Printable bill
    ├── order_ingredients.html        # Monthly restock
    ├── monthly_report_form.html
    └── monthly_report.html
```

---

## 📄 License

MIT — free to use as a template.

---

*Built by Umut Alperen Cengiz — Database Systems course project.*
