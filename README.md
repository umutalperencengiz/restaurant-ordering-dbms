# Restaurant Ordering DBMS

A full-stack Flask + MySQL restaurant ordering system with separate portals for customers and sales clerks. Built as a database systems course project — production-ready with environment-based configuration, bcrypt password hashing, and per-request database connections.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)](https://mysql.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 About

Restaurant Ordering DBMS is a web application that manages a restaurant's daily operations:

- **Customers** can register/log in, browse the menu, and place orders. Orders are checked against live ingredient stock (spice, vegetables, meat) so the restaurant never sells what it can't make.
- **Sales clerks** can log in to a dashboard, view all orders with daily and per-customer P&L reports, generate printable bills, and record daily ingredient restocking.
- All data lives in MySQL; every query uses parameterized statements (no SQL injection).

---

## 🚀 Live Demo

Deploy your own copy in under 5 minutes on Render (free tier):

1. **Fork this repo** to your GitHub account.
2. **Create a MySQL database** on Render: *New → Managed Database → MySQL*. Note the host, user, and password.
3. **Create a Web Service** → connect your fork:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn backEnd:app`
   - Environment variables (see `.env.example`):
     - `SECRET_KEY` — any long random string
     - `DB_HOST`, `DB_USER`, `DB_PASSWORD` — from your Render MySQL instance
     - `DB_NAME=assignment3database`
     - `FLASK_DEBUG=false`
4. **Seed the database** by running `schema.sql` against your MySQL instance.
5. Visit your Render URL. Default clerk login: `ahmet@restaurant.local` / `clerk123`.

---

## 🛠 Local Setup

### 1. Clone
```bash
git clone https://github.com/umutalperencengiz/restaurant-ordering-dbms.git
cd restaurant-ordering-dbms
```

### 2. Virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Database
Make sure MySQL is running, then initialize:
```bash
mysql -u root -p < schema.sql
```

Seed data includes menu items (Lahmacun, Pide, Kebab, Durum, Beverage), ingredient stock, and a sales clerk account:
- Email: `ahmet@restaurant.local`
- Password: `clerk123`

### 5. Configure
Copy `.env.example` to `.env` and fill in your MySQL password:
```bash
cp .env.example .env
# edit .env with your values
```

### 6. Run
```bash
python backEnd.py
```
Visit **http://127.0.0.1:5000**

---

## 🗄 Database Schema

```
Customer          customer_id, name, telephone, email
SalesClerk        clerk_id, name, email, password (bcrypt)
Item              item_id, name, price
ingredients       item_id, spice, vegetable, meat  (item_id=7 = running stock)
orders            order_id, customer_id, item, quantity, date, totalPrice
order_ingredients order_date, prices, totals per ingredient
```

See `schema.sql` for the full DDL and seed data.

---

## 🐛 Bugs Fixed (vs. original submission)

| Area | Issue | Fix |
|------|-------|-----|
| Routing | `customer_dashboard` had no `@app.route` — page was unreachable | Added decorator |
| Templating | `order_screen` passed no `items` — template crashed | Query `Item` and pass `items` |
| Security | Passwords stored in plaintext | `bcrypt` hashing |
| Security | Hardcoded DB credentials & `SECRET_KEY` | Environment variables |
| Reliability | Global MySQL connection (not thread-safe) | Per-request connection via Flask `g` |
| Reliability | `debug=True` hardcoded | Controlled by `FLASK_DEBUG` env var |
| Data integrity | `<input type="month">` sends `YYYY-MM` but DB needs `DATE` | `normalize_date()` helper |
| UX | Raw string error responses | `flash()` messages |
| Deployment | No `requirements.txt`, `Procfile`, or `runtime.txt` | Added all three |

---

## 📁 Project Structure

```
restaurant-ordering-dbms/
├── backEnd.py          # Flask app — routes + database logic
├── schema.sql          # MySQL schema + seed data
├── requirements.txt    # Python dependencies
├── Procfile            # Render/Railway process definition
├── runtime.txt         # Python version pin
├── .env.example        # Environment variable template
├── .gitignore
├── README.md
└── templates/          # Jinja2 HTML templates
    ├── login.html
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

## 🔐 Security Notes

- Passwords are hashed with bcrypt — never stored plaintext.
- All SQL queries use parameterized placeholders (`%s`) — immune to SQL injection.
- Session-based authentication with role checks (`customer` vs `clerk`).
- `.env` and `__pycache__` are gitignored — secrets never committed.

---

## 📄 License

MIT — feel free to use this as a template for your own projects.

---

*Built by Umut Alperen Cengiz — Database Systems course project.*