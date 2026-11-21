import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

DATABASE = os.environ.get("DATABASE_URL", "restaurant.db")


# ---------------------------------------------------------------- database
def get_db():
    """Open a new SQLite connection per request (thread-safe for production)."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.cursor = g.db.cursor()
    return g.db, g.cursor


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    cursor = g.pop("cursor", None)
    if cursor is not None:
        cursor.close()
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed data on first run."""
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            db.executescript(f.read())

    # Seed a default sales clerk if none exists
    cursor.execute("SELECT COUNT(*) FROM SalesClerk")
    if cursor.fetchone()[0] == 0:
        pw_hash = generate_password_hash("clerk123")
        cursor.execute(
            "INSERT INTO SalesClerk (clerkName, email, password) VALUES (?, ?, ?)",
            ("Ahmet Demir", "ahmet@restaurant.local", pw_hash),
        )
        db.commit()

    db.close()


def db_query(query, args=(), fetchone=False, commit=False):
    """Helper: run a query using the request-scoped connection."""
    db, cursor = get_db()
    cursor.execute(query, args)
    if commit:
        db.commit()
        return cursor.lastrowid
    if fetchone:
        return cursor.fetchone()
    return cursor.fetchall()


def normalize_date(value: str) -> str:
    """Convert a YYYY-MM (from <input type='month'>) to YYYY-MM-DD for SQLite DATE."""
    value = value.strip()
    if not value:
        return value
    if len(value) == 7 and value[4] == "-":  # YYYY-MM
        return value + "-01"
    return value


# Initialize database on import (works with gunicorn too)
init_db()


# ---------------------------------------------------------------- routes
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Customer registration page."""
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not telephone or not email:
        flash("Please fill in all fields.", "error")
        return render_template("register.html")

    existing = db_query(
        "SELECT customer_id FROM Customer WHERE email=? OR telephoneNum=?",
        (email, telephone), fetchone=True,
    )
    if existing:
        flash("A customer with this email or telephone already exists.", "error")
        return render_template("register.html")

    try:
        new_id = db_query(
            "INSERT INTO Customer (customerName, telephoneNum, email) VALUES (?, ?, ?)",
            (name, telephone, email), commit=True,
        )
        session["user"] = name
        session["customer_id"] = new_id
        session["role"] = "customer"
        session["email"] = email
        flash("Account created successfully! You are now logged in.", "success")
        return redirect("/customer_dashboard")
    except sqlite3.Error as e:
        flash(f"Registration failed: {e}", "error")
        return render_template("register.html")


@app.route("/sales_clerk_login", methods=["POST"])
def sales_clerk_login():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect("/")

    row = db_query(
        "SELECT clerkName, email, password FROM SalesClerk WHERE email=?",
        (email,), fetchone=True,
    )
    if row and check_password_hash(row[2], password):
        session["user"] = row[0]      # clerkName
        session["user_email"] = row[1]
        session["role"] = "clerk"
        flash("Welcome back, Sales Clerk!", "success")
        return redirect("/sales_clerk_dashboard")
    flash("Invalid email or password.", "error")
    return redirect("/")


@app.route("/customer_login", methods=["POST"])
def customer_login():
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()
    if not name or not telephone or not email:
        flash("Please fill in all customer fields.", "error")
        return redirect("/")

    row = db_query(
        "SELECT customer_id, customerName, telephoneNum, email FROM Customer "
        "WHERE customerName=? AND telephoneNum=? AND email=?",
        (name, telephone, email), fetchone=True,
    )
    if row:
        session["user"] = row[1]
        session["customer_id"] = row[0]
        session["role"] = "customer"
        flash(f"Welcome back, {row[1]}!", "success")
        return redirect("/customer_dashboard")

    flash("No account found with these details. Please register first.", "error")
    return redirect("/register")


@app.route("/customer_dashboard")
def customer_dashboard():
    if "user" not in session or session.get("role") != "customer":
        return redirect("/")
    rows = db_query("SELECT name FROM Item ORDER BY name")
    items = [r[0] for r in rows] if rows else []
    return render_template("order.html", user=session["user"], items=items)


@app.route("/sales_clerk_dashboard")
def sales_clerk_dashboard():
    if "user" not in session or session.get("role") != "clerk":
        return redirect("/")
    row = db_query(
        "SELECT clerkName FROM SalesClerk WHERE email=?",
        (session.get("user_email"),), fetchone=True,
    )
    clerk_name = row[0] if row else session["user"]
    return render_template("sales_clerk_dashboard.html", sales_clerk_name=clerk_name)


@app.route("/view_orders")
def view_orders():
    if "user" not in session:
        return redirect("/")
    try:
        customer_details = db_query(
            "SELECT o.customerName, o.telephoneNum, o.date "
            "FROM orders o JOIN customer c ON o.customer_id = c.customer_id "
            "GROUP BY o.customer_id, o.date ORDER BY o.date DESC"
        ) or []

        orders_with_ids = []
        daily_pln = {}
        total_pln_per_customer = {}
        total_pln_per_customer_per_day = {}
        order_values = {}

        for customer_name, contact_no, order_date in customer_details:
            id_row = db_query(
                "SELECT GROUP_CONCAT(o.order_id) FROM orders o JOIN customer c "
                "ON o.customer_id = c.customer_id "
                "WHERE c.customerName=? AND c.telephoneNum=? AND o.date=?",
                (customer_name, contact_no, order_date), fetchone=True,
            )
            order_ids = id_row[0] if id_row and id_row[0] else ""
            if order_ids:
                orders_with_ids.append((customer_name, contact_no, order_date, order_ids))

            day_total = db_query(
                "SELECT SUM(o.totalPrice) FROM orders o JOIN customer c "
                "ON o.customer_id = c.customer_id "
                "WHERE c.customerName=? AND c.telephoneNum=? AND o.date=?",
                (customer_name, contact_no, order_date), fetchone=True,
            )
            daily_pln[order_date] = day_total[0] if day_total and day_total[0] else 0

            cust_total = db_query(
                "SELECT SUM(o.totalPrice) FROM orders o JOIN customer c "
                "ON o.customer_id = c.customer_id "
                "WHERE c.customerName=? AND c.telephoneNum=?",
                (customer_name, contact_no), fetchone=True,
            )
            if cust_total and cust_total[0]:
                total_pln_per_customer[customer_name] = cust_total[0]

            day_cust_total = db_query(
                "SELECT SUM(o.totalPrice) FROM orders o JOIN customer c "
                "ON o.customer_id = c.customer_id "
                "WHERE c.customerName=? AND c.telephoneNum=? AND o.date=?",
                (customer_name, contact_no, order_date), fetchone=True,
            )
            if day_cust_total and day_cust_total[0]:
                total_pln_per_customer_per_day.setdefault(customer_name, {})[order_date] = day_cust_total[0]

        for order in orders_with_ids:
            ids = order[3].split(",")
            order_values[order[3]] = []
            for oid in ids:
                val = db_query("SELECT totalPrice FROM orders WHERE order_id=?", (oid,), fetchone=True)
                order_values[order[3]].append(val[0] if val and val[0] else 0)

        total_pln = sum(daily_pln.values())

        return render_template(
            "view_orders.html",
            orders_with_ids=orders_with_ids,
            order_values=order_values,
            total_pln=total_pln,
            daily_pln=daily_pln,
            total_pln_per_customer=total_pln_per_customer,
            total_pln_per_customer_per_day=total_pln_per_customer_per_day,
        )
    except sqlite3.Error as e:
        return f"Database error: {e}", 500


@app.route("/generate_bills", methods=["GET", "POST"])
def generate_bills():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":
        bill_date = request.form.get("bill_date", "")
        customer_id = request.form.get("customer_id", "")
        if not bill_date or not customer_id:
            flash("Please select both date and customer.", "error")
            return redirect("/generate_bills")

        try:
            orders = db_query(
                "SELECT i.name, o.totalPrice FROM orders o JOIN item i ON o.name = i.name "
                "WHERE o.date = ? AND o.customer_id = ?",
                (bill_date, customer_id),
            ) or []
            cust = db_query(
                "SELECT customerName FROM Customer WHERE customer_id=?",
                (customer_id,), fetchone=True,
            )
            customer_name = cust[0] if cust else "Customer"
            total_price = sum(o[1] for o in orders if o[1] is not None)
            bill_no = f"B-{bill_date.replace('-', '')}-{customer_name.replace(' ', '')}"
            return render_template(
                "bill_template.html",
                bill_no=bill_no, bill_date=bill_date, customer_name=customer_name,
                orders=orders, total_price=total_price,
            )
        except sqlite3.Error as e:
            return f"Database error: {e}", 500

    unique_dates = [r[0] for r in (db_query("SELECT DISTINCT date FROM orders ORDER BY date DESC") or [])]
    unique_customer_ids = [r[0] for r in (db_query("SELECT DISTINCT customer_id FROM orders ORDER BY customer_id") or [])]
    return render_template("generate_bills.html", unique_dates=unique_dates, unique_customer_ids=unique_customer_ids)


@app.route("/update_order_ingredients", methods=["POST"])
def update_order_ingredients():
    if "user" not in session or session.get("role") != "clerk":
        return redirect("/")
    order_date = normalize_date(request.form.get("order_date", ""))
    price_spice = request.form.get("price_spice", "0")
    price_vegetables = request.form.get("price_vegetables", "0")
    price_meat = request.form.get("price_meat", "0")
    total_spice = request.form.get("total_spice", "0")
    total_vegetables = request.form.get("total_vegetables", "0")
    total_meat = request.form.get("total_meat", "0")

    try:
        total_spice = int(total_spice)
        total_vegetables = int(total_vegetables)
        total_meat = int(total_meat)
    except ValueError:
        flash("Ingredient quantities must be numbers.", "error")
        return redirect("/order_ingredients")

    try:
        count_row = db_query(
            "SELECT COUNT(*) FROM order_ingredients WHERE order_date=?",
            (order_date,), fetchone=True,
        )
        count = count_row[0] if count_row else 0

        if count > 0:
            prev = db_query(
                "SELECT total_spice, total_vegetables, total_meat FROM order_ingredients WHERE order_date=?",
                (order_date,), fetchone=True,
            )
            if prev:
                diff_spice = total_spice - int(prev[0])
                diff_vegetables = total_vegetables - int(prev[1])
                diff_meat = total_meat - int(prev[2])
            else:
                diff_spice = diff_vegetables = diff_meat = 0

            db_query(
                "UPDATE order_ingredients SET price_spice=?, price_vegetables=?, price_meat=?, "
                "total_spice=?, total_vegetables=?, total_meat=? WHERE order_date=?",
                (price_spice, price_vegetables, price_meat, total_spice, total_vegetables, total_meat, order_date),
                commit=True,
            )
            message = "Values updated successfully!"
        else:
            db_query(
                "INSERT INTO order_ingredients "
                "(order_date, price_spice, price_vegetables, price_meat, total_spice, total_vegetables, total_meat) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_date, price_spice, price_vegetables, price_meat, total_spice, total_vegetables, total_meat),
                commit=True,
            )
            diff_spice, diff_vegetables, diff_meat = total_spice, total_vegetables, total_meat
            message = "Values inserted successfully!"

        now = datetime.now()
        year, month = map(int, order_date.split("-")[:2])
        if now.year <= year and now.month <= month:
            db_query(
                "UPDATE ingredients SET Spice = Spice + ?, Vegetable = Vegetable + ?, Meat = Meat + ? WHERE item_id = ?",
                (diff_spice, diff_vegetables, diff_meat, 7), commit=True,
            )

        flash(message, "success")
        return render_template("order_ingredients.html", message=message)
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "error")
        return redirect("/order_ingredients")


@app.route("/show_ingredients", methods=["GET", "POST"])
def show_ingredients():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":
        order_date = normalize_date(request.form.get("order_date", ""))
        try:
            ingredient_orders = db_query(
                "SELECT price_spice, price_vegetables, price_meat, total_spice, total_vegetables, total_meat "
                "FROM order_ingredients WHERE order_date=?",
                (order_date,),
            ) or []
            return render_template("monthly_report.html", order_date=order_date, ingredient_orders=ingredient_orders)
        except sqlite3.Error as e:
            return f"Database error: {e}", 500
    return render_template("monthly_report_form.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect("/")


@app.route("/order_screen")
def order_screen():
    if "user" not in session or session.get("role") != "customer":
        return redirect("/")
    rows = db_query("SELECT name FROM Item ORDER BY name")
    items = [r[0] for r in rows] if rows else []
    return render_template("order.html", user=session["user"], items=items)


@app.route("/place_order", methods=["POST"])
def place_order():
    if "user" not in session or session.get("role") != "customer":
        return redirect("/")
    customer_id = session.get("customer_id")
    date = datetime.now().strftime("%Y-%m-%d")

    try:
        for i in range(1, 6):
            item = request.form.get(f"item{i}", "").strip()
            quantity = request.form.get(f"quantity{i}", "").strip()
            if not item or not quantity:
                continue
            quantity = int(quantity)
            if quantity < 1:
                continue

            price_row = db_query("SELECT price FROM item WHERE name=?", (item,), fetchone=True)
            if not price_row:
                continue
            item_price = price_row[0]
            total_price = item_price * quantity

            ing_row = db_query(
                "SELECT spice, vegetable, meat FROM ingredients WHERE item_id = (SELECT item_id FROM item WHERE name=?)",
                (item,), fetchone=True,
            )
            if not ing_row:
                continue
            used_spice, used_veg, used_meat = ing_row

            total_row = db_query("SELECT Spice, Vegetable, Meat FROM ingredients WHERE item_id = 7", fetchone=True)
            if not total_row:
                continue
            total_spice, total_veg, total_meat = total_row

            new_spice = total_spice - used_spice * quantity
            new_veg = total_veg - used_veg * quantity
            new_meat = total_meat - used_meat * quantity

            if new_spice < 0 or new_veg < 0 or new_meat < 0:
                flash("Not enough ingredients to complete the order.", "error")
                return redirect("/order_screen")

            db_query(
                "INSERT INTO orders (customer_id, name, quantity, date, totalPrice) VALUES (?, ?, ?, ?, ?)",
                (customer_id, item, quantity, date, total_price), commit=True,
            )

        flash("Order placed successfully!", "success")
        return redirect("/order_screen")
    except sqlite3.Error as e:
        return f"Database error: {e}", 500


# ---------------------------------------------------------------- entrypoint
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )
