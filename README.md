# Restaurant Ordering DBMS

A full-stack Flask + MySQL restaurant ordering system with separate portals for customers and sales clerks. Built as a database systems course project — production-ready with environment-based configuration, bcrypt password hashing, and per-request database connections.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)](https://mysql.com)

---

## 🌐 Live Website

**Render URL:** `https://your-app-name.onrender.com`

*(Replace this with your actual Render URL after deployment)*

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
- All data lives in MySQL; every query uses parameterized statements (no SQL injection).

---

## 🚀 Deploy on Render (free tier)

1. **Fork** this repo to your GitHub account.
2. **Create a MySQL database** (e.g. [db4free.net](https://db4free.net) or any free MySQL host). Note the host, user, and password.
3. **Create a Web Service** on [Render](https://render.com):
   - Connect your GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn backEnd:app`
   - Environment variables:
     - `SECRET_KEY` — any long random string
     - `DB_HOST` — your MySQL host
     - `DB_USER` — your MySQL username
     - `DB_PASSWORD` — your MySQL password
     - `DB_NAME` = `assignment3database`
     - `FLASK_DEBUG` = `false`
4. **Seed the database** by running `schema.sql` against your MySQL instance.
5. Visit your Render URL.

---

## 🛠 Local Setup

```bash
git clone https://github.com/umutalperencengiz/restaurant-ordering-dbms.git
cd restaurant-ordering-dbms
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
mysql -u root -p < schema.sql
cp .env.example .env       # fill in your DB credentials
python backEnd.py
```
Visit **http://127.0.0.1:5000** locally.

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

## 📁 Project Structure

```
restaurant-ordering-dbms/
├── backEnd.py          # Flask app — routes + database logic
├── schema.sql          # MySQL schema + seed data
├── requirements.txt    # Python dependencies
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