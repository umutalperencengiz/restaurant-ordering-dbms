# Restaurant Ordering DBMS

A Flask + MySQL restaurant ordering system with separate portals for customers and sales clerks.

## Features

- **Customer portal**: register/login, browse menu items, place orders (with ingredient stock checks)
- **Sales clerk portal**: login, dashboard, view orders with daily/total P&L, generate bills, manage ingredient restocking
- **Database**: MySQL schema included (`schema.sql`) with seed data
- **Security**: bcrypt password hashing, per-request DB connections, session-based auth, flash messages
- **Deploy-ready**: `requirements.txt`, `Procfile`, `runtime.txt`, env-based configuration

## Local setup

### 1. Clone and enter the folder
```bash
cd SelectedTopicsDBMS
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up the database
Make sure MySQL is running, then initialize the database:
```bash
mysql -u root -p < schema.sql
```

The seed data creates:
- Menu items (Lahmacun, Pide, Kebab, Durum, Beverage)
- Ingredient stock totals (500 each of spice / vegetable / meat)
- Sales clerk: `ahmet@restaurant.local` / password `clerk123`

### 5. Configure environment (optional)
Create a `.env` file if you want to override defaults:
```env
SECRET_KEY=replace-with-a-random-secret
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=assignment3database
FLASK_DEBUG=true
```

### 6. Run locally
```bash
python backEnd.py
```
Visit http://127.0.0.1:5000

## Deployment (Render.com)

This app is ready to deploy on [Render](https://render.com) (free tier) connected to GitHub.

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/umutalperencengiz/<repo-name>.git
git push -u origin main
```

### 2. Create a MySQL database on Render
- In Render dashboard: **New** → **Managed Database** → **MySQL**
- Note the internal database name, user, and password Render gives you

### 3. Create the web service
- **New** → **Web Service** → connect your GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn backEnd:app`
- Add environment variables:
  - `SECRET_KEY` — a long random string
  - `DB_HOST` — Render MySQL host
  - `DB_USER` — Render MySQL user
  - `DB_PASSWORD` — Render MySQL password
  - `DB_NAME` — `assignment3database`
  - `FLASK_DEBUG` — `false`

### 4. Seed the database
Once deployed, connect to your Render MySQL instance and run:
```bash
mysql -h <render-host> -u <render-user> -p assignment3database < schema.sql
```

## Project structure

```
SelectedTopicsDBMS/
├── backEnd.py          # Flask application (routes + DB logic)
├── schema.sql          # MySQL schema + seed data
├── requirements.txt    # Python dependencies
├── Procfile            # Render/Railway process definition
├── runtime.txt         # Python version pin
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

## Bugs fixed vs. original

- `customer_dashboard` was missing its `@app.route` decorator — the page never loaded
- `order_screen` rendered `order.html` without passing `items` — template crashed
- Hardcoded DB credentials → now read from environment variables
- Weak `SECRET_KEY` → now env-configurable
- Plaintext password storage → bcrypt hashing
- Global `mysql.connector` connection (not thread-safe) → per-request connection via Flask `g`
- `debug=True` hardcoded → controlled by `FLASK_DEBUG` env var
- Raw string error responses → `flash()` messages with proper HTTP status codes
