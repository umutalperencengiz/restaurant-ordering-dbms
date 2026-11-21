# Restaurant Ordering DBMS

A full-stack Flask + SQLite restaurant ordering system with separate portals for customers and sales clerks. Built as a database systems course project — zero external dependencies, deploys instantly on Render (free tier).

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)](https://www.sqlite.org)

---

## 🌐 Live Website

**Render URL:** `https://restaurant-ordering-dbms.onrender.com`

### Demo Accounts
| Role | Email | Password |
|------|-------|----------|
| Sales Clerk | `ahmet@restaurant.local` | `clerk123` |
| Customer | Register at `/register` | — |

---

## 📖 About

Restaurant Ordering DBMS manages a restaurant's daily operations:

- **Customers** can register, log in, browse the menu, and place orders. Orders are checked against live ingredient stock (spice, vegetables, meat) so the restaurant never sells what it can't make.
- **Sales clerks** can log in to a dashboard, view all orders with daily and per-customer P&L reports, generate printable bills, and record daily ingredient restocking.
- All data lives in a local SQLite file (`restaurant.db`) — no external database server needed.
- Every query uses parameterized statements (no SQL injection).

---

## 🚀 Deploy on Render (free tier) — no database setup needed

Since the app uses SQLite, you don't need MySQL or any external database:

1. **Fork** this repo to your GitHub account.
2. **Create a Web Service** on [Render](https://render.com):
   - Connect your GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn backEnd:app`
   - Environment variables (optional — only `SECRET_KEY` is recommended):
     - `SECRET_KEY` — any long random string
     - `FLASK_DEBUG` = `false`
3. Click **Create Web Service**. Render will handle the rest.
4. Visit your Render URL.

---

## 🛠 Local Setup

```bash
git clone https://github.com/umutalperencengiz/restaurant-ordering-dbms.git
cd restaurant-ordering-dbms
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python backEnd.py
```
Visit **http://127.0.0.1:5000** locally.

The SQLite database (`restaurant.db`) is created automatically on first run with sample menu items and a sales clerk account.

---

## 🗄 Database (SQLite)

No MySQL, no external host, no environment variables for DB credentials. The schema is in `schema.sql` and is applied automatically when the app starts:

```
Customer          customer_id, name, telephone, email
SalesClerk        clerk_id, name, email, password (bcrypt)
Item              item_id, name, price
ingredients       item_id, spice, vegetable, meat  (item_id=7 = running stock)
orders            order_id, customer_id, item, quantity, date, totalPrice
order_ingredients order_date, prices, totals per ingredient
```

---

## 📁 Project Structure

```
restaurant-ordering-dbms/
├── backEnd.py          # Flask app — routes + SQLite logic
├── schema.sql          # SQLite schema + seed data (auto-applied)
├── requirements.txt    # Python dependencies (Flask, gunicorn)
├── Procfile            # Render process definition
├── runtime.txt         # Python version pin
├── .env.example        # Environment variable template
├── README.md
└── templates/          # Jinja2 HTML templates
    ├── login.html
    ├── register.html
    ├── order.html
    ├── sales_clerk_dashboard.html
    ├── view_orders.html
    ├── generate_bills.html
    ├── bill_template.html
    ├── order_ingredients.html
    ├── monthly_report.html
    └── monthly_report_form.html
```

---

## ⚠️ Important Note (Render Free Tier)

Render's free tier uses an **ephemeral filesystem**, which means the SQLite database (`restaurant.db`) resets to the seed data every time the service redeploys or sleeps. This is fine for a portfolio demo. For persistent production data, upgrade to a Render persistent disk or use an external database.

---

## 🔐 Security Notes

- Passwords are hashed with bcrypt — never stored plaintext.
- All SQL queries use parameterized placeholders — immune to SQL injection.
- Session-based authentication with role checks (`customer` vs `clerk`).
- `.env` and `__pycache__` are gitignored — secrets never committed.

---

## 📄 License

MIT — feel free to use this as a template for your own projects.

---

*Built by Umut Alperen Cengiz — Database Systems course project.*