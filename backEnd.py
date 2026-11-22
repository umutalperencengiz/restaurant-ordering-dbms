import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

DATABASE = os.environ.get("DATABASE_URL", os.path.join(BASE_DIR, "restaurant.db"))
if DATABASE.startswith("sqlite:///"):
    DATABASE = DATABASE[len("sqlite:///"):]
if not os.path.isabs(DATABASE):
    DATABASE = os.path.join(BASE_DIR, DATABASE)


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
    cursor = g.pop("cursor", None)
    db = g.pop("db", None)
    if cursor is not None:
        cursor.close()
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed data. Safe to run on every start (idempotent)."""
    db = sqlite3.connect(DATABASE)
    try:
        db.row_factory = sqlite3.Row
        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                db.executescript(f.read())

        cur = db.cursor()

        # Default sales clerk: ahmet@restaurant.local / clerk123
        if cur.execute("SELECT COUNT(*) FROM SalesClerk").fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO SalesClerk (clerkName, email, password) VALUES (?, ?, ?)",
                ("Ahmet Demir", "ahmet@restaurant.local", generate_password_hash("clerk123")),
            )

        # Demo customer + sample orders so reports/bills are never empty
        if cur.execute("SELECT COUNT(*) FROM Customer").fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO Customer (customerName, telephoneNum, email) VALUES (?, ?, ?)",
                ("Demo Customer", "5550000001", "demo@customer.local"),
            )
            customer_id = cur.lastrowid
            cur.execute(
                "INSERT INTO orders (customer_id, name, quantity, date, totalPrice) "
                "VALUES (?, 'Lahmacun', 2, DATE('now', '-1 day'), 90.00)",
                (customer_id,),
            )
            cur.execute(
                "INSERT INTO orders (customer_id, name, quantity, date, totalPrice) "
                "VALUES (?, 'Kebab', 1, DATE('now'), 85.00)",
                (customer_id,),
            )

        db.commit()
    finally:
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
    value = (value or "").strip()
    if not value:
        return value
    if len(value) == 7 and value[4] == "-":  # YYYY-MM
        return value + "-01"
    return value


def normalize_phone(value: str) -> str:
    """Keep digits only so '+90 555 000 00 00' matches '905550000000'."""
    return re.sub(r"\D", "", value or "")


def is_customer():
    return "user" in session and session.get("role") == "customer"


def is_clerk():
    return "user" in session and session.get("role") == "clerk"


def menu_items():
    rows = db_query("SELECT name, price FROM Item ORDER BY name") or []
    return [{"name": r[0], "price": r[1]} for r in rows]


def stock_levels():
    row = db_query(
        "SELECT spice, vegetable, meat FROM ingredients WHERE item_id = 7", fetchone=True
    )
    if row is None:
        return {"spice": 0, "vegetable": 0, "meat": 0}
    return {"spice": row[0], "vegetable": row[1], "meat": row[2]}


# Initialize database on import (works with gunicorn too)
init_db()


# ---------------------------------------------------------------- routes
@app.route("/")
def login():
    return render_template("login.html")


@app.route("/health")
def health():
    return {"status": "ok"}


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
        "SELECT customer_id FROM Customer "
        "WHERE lower(email) = lower(?) OR replace(replace(replace(telephoneNum, ' ', ''), '-', ''), '+', '') = ?",
        (email, normalize_phone(telephone)),
        fetchone=True,
    )
    if existing:
        flash("A customer with this email or telephone already exists.", "error")
        return render_template("register.html")

    try:
        new_id = db_query(
            "INSERT INTO Customer (customerName, telephoneNum, email) VALUES (?, ?, ?)",
            (name, telephone, email),
            commit=True,
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
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect("/")

    row = db_query(
        "SELECT clerkName, email, password FROM SalesClerk WHERE lower(email) = lower(?)",
        (email,),
        fetchone=True,
    )
    if row and check_password_hash(row[2], password):
        session["user"] = row[0]  # clerkName
        session["user_email"] = row[1]
        session["role"] = "clerk"
        flash(f"Welcome back, {row[0]}!", "success")
        return redirect("/sales_clerk_dashboard")

    flash("Invalid email or password.", "error")
    return redirect("/")


@app.route("/customer_login", methods=["POST"])
def customer_login():
    name = request.form.get("name", "").strip()
    telephone = request.form.get("telephone", "").strip()
    email = request.form.get("email", "").strip()

    if not email or not telephone:
        flash("Please enter your email and telephone number.", "error")
        return redirect("/")

    # Look the account up by email, then verify the telephone number.
    # The name is only used for the greeting, so a small typo cannot lock
    # a customer out of their own account.
    row = db_query(
        "SELECT customer_id, customerName, telephoneNum FROM Customer WHERE lower(email) = lower(?)",
        (email,),
        fetchone=True,
    )

    if row and normalize_phone(row[2]) == normalize_phone(telephone):
        session["user"] = name or row[1]
        session["customer_id"] = row[0]
        session["role"] = "customer"
        session["email"] = email
        flash(f"Welcome back, {row[1]}!", "success")
        return redirect("/customer_dashboard")

    if row:
        flash(
            "That email exists, but the telephone number doesn't match. "
            "Check the number you registered with.",
            "error",
        )
        return redirect("/")

    flash("No account found with this email. Please register first.", "error")
    return redirect("/register")


@app.route("/customer_dashboard")
@app.route("/order_screen")
def customer_dashboard():
    if not is_customer():
        return redirect("/")
    return render_template(
        "order.html",
        user=session["user"],
        items=menu_items(),
        menu=menu_items(),
        stock=stock_levels(),
    )


@app.route("/sales_clerk_dashboard")
def sales_clerk_dashboard():
    if not is_clerk():
        return redirect("/")
    row = db_query(
        "SELECT clerkName FROM SalesClerk WHERE email=?",
        (session.get("user_email"),),
        fetchone=True,
    )
    clerk_name = row[0] if row else session["user"]
    return render_template("sales_clerk_dashboard.html", sales_clerk_name=clerk_name)


@app.route("/view_orders")
def view_orders():
    if not is_clerk():
        return redirect("/")
    try:
        rows = db_query(
            "SELECT c.customerName, c.telephoneNum, o.date, "
            "       GROUP_CONCAT(o.order_id), GROUP_CONCAT(o.totalPrice), SUM(o.totalPrice) "
            "FROM orders o JOIN Customer c ON c.customer_id = o.customer_id "
            "GROUP BY o.customer_id, o.date "
            "ORDER BY o.date DESC, c.customerName"
        ) or []

        orders_with_ids = []
        order_values = {}
        daily_pln = {}
        total_pln_per_customer = {}
        total_pln_per_customer_per_day = {}

        for customer_name, contact_no, order_date, order_ids, prices_csv, day_total in rows:
            day_total = float(day_total or 0)
            orders_with_ids.append((customer_name, contact_no, order_date, order_ids))
            order_values[order_ids] = [float(p) for p in (prices_csv or "").split(",") if p]

            daily_pln[order_date] = daily_pln.get(order_date, 0) + day_total
            total_pln_per_customer[customer_name] = (
                total_pln_per_customer.get(customer_name, 0) + day_total
            )
            total_pln_per_customer_per_day.setdefault(customer_name, {})[order_date] = day_total

        return render_template(
            "view_orders.html",
            orders_with_ids=orders_with_ids,
            order_values=order_values,
            total_pln=sum(daily_pln.values()),
            daily_pln=daily_pln,
            total_pln_per_customer=total_pln_per_customer,
            total_pln_per_customer_per_day=total_pln_per_customer_per_day,
        )
    except sqlite3.Error as e:
        return f"Database error: {e}", 500


@app.route("/generate_bills", methods=["GET", "POST"])
def generate_bills():
    if not is_clerk():
        return redirect("/")

    if request.method == "POST":
        bill_date = normalize_date(request.form.get("bill_date", ""))
        customer_id = request.form.get("customer_id", "").strip()
        if not bill_date or not customer_id:
            flash("Please select both a date and a customer.", "error")
            return redirect("/generate_bills")

        cust = db_query(
            "SELECT customerName, telephoneNum FROM Customer WHERE customer_id=?",
            (customer_id,),
            fetchone=True,
        )
        if cust is None:
            flash("Customer not found.", "error")
            return redirect("/generate_bills")

        orders = db_query(
            "SELECT name, quantity, totalPrice FROM orders "
            "WHERE date=? AND customer_id=? ORDER BY order_id",
            (bill_date, customer_id),
        ) or []

        if not orders:
            flash("No orders found for that customer on that date.", "error")
            return redirect("/generate_bills")

        total_price = sum(float(o[2] or 0) for o in orders)
        bill_no = f"B-{bill_date.replace('-', '')}-{customer_id}"
        return render_template(
            "bill_template.html",
            bill_no=bill_no,
            bill_date=bill_date,
            customer_name=cust[0],
            contact_no=cust[1],
            orders=orders,
            total_price=f"{total_price:.2f}",
        )

    unique_dates = [
        r[0] for r in (db_query("SELECT DISTINCT date FROM orders ORDER BY date DESC") or [])
    ]
    unique_customers = db_query(
        "SELECT DISTINCT c.customer_id, c.customerName "
        "FROM orders o JOIN Customer c ON c.customer_id = o.customer_id "
        "ORDER BY c.customerName"
    ) or []
    return render_template(
        "generate_bills.html",
        unique_dates=unique_dates,
        unique_customers=unique_customers,
    )


@app.route("/order_ingredients")
def order_ingredients():
    if not is_clerk():
        return redirect("/")
    return render_template("order_ingredients.html", stock=stock_levels())


@app.route("/update_order_ingredients", methods=["POST"])
def update_order_ingredients():
    if not is_clerk():
        return redirect("/")

    order_date = normalize_date(request.form.get("order_date", ""))
    if not order_date:
        flash("Please choose the month you are restocking.", "error")
        return redirect("/order_ingredients")

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
        flash("Ingredient quantities must be whole numbers.", "error")
        return redirect("/order_ingredients")

    try:
        db, cur = get_db()
        prev = cur.execute(
            "SELECT total_spice, total_vegetables, total_meat FROM order_ingredients WHERE order_date=?",
            (order_date,),
        ).fetchone()

        if prev:
            diff_spice = total_spice - int(prev["total_spice"])
            diff_vegetables = total_vegetables - int(prev["total_vegetables"])
            diff_meat = total_meat - int(prev["total_meat"])
            cur.execute(
                "UPDATE order_ingredients SET price_spice=?, price_vegetables=?, price_meat=?, "
                "total_spice=?, total_vegetables=?, total_meat=? WHERE order_date=?",
                (
                    price_spice,
                    price_vegetables,
                    price_meat,
                    total_spice,
                    total_vegetables,
                    total_meat,
                    order_date,
                ),
            )
            message = "Restock values updated."
        else:
            cur.execute(
                "INSERT INTO order_ingredients "
                "(order_date, price_spice, price_vegetables, price_meat, "
                " total_spice, total_vegetables, total_meat) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    order_date,
                    price_spice,
                    price_vegetables,
                    price_meat,
                    total_spice,
                    total_vegetables,
                    total_meat,
                ),
            )
            diff_spice, diff_vegetables, diff_meat = total_spice, total_vegetables, total_meat
            message = "Restock recorded."

        cur.execute(
            "UPDATE ingredients SET spice = spice + ?, vegetable = vegetable + ?, "
            "meat = meat + ? WHERE item_id = 7",
            (diff_spice, diff_vegetables, diff_meat),
        )
        db.commit()

        flash(message, "success")
        return redirect("/order_ingredients")
    except sqlite3.Error as e:
        flash(f"Database error: {e}", "error")
        return redirect("/order_ingredients")


@app.route("/show_ingredients", methods=["GET", "POST"])
def show_ingredients():
    if not is_clerk():
        return redirect("/")
    if request.method == "POST":
        order_date = normalize_date(request.form.get("order_date", ""))
        try:
            ingredient_orders = db_query(
                "SELECT price_spice, price_vegetables, price_meat, "
                "       total_spice, total_vegetables, total_meat "
                "FROM order_ingredients WHERE order_date=?",
                (order_date,),
            ) or []
            return render_template(
                "monthly_report.html",
                order_date=order_date,
                ingredient_orders=ingredient_orders,
            )
        except sqlite3.Error as e:
            return f"Database error: {e}", 500
    return render_template("monthly_report_form.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect("/")


@app.route("/place_order", methods=["POST"])
def place_order():
    if not is_customer():
        return redirect("/")

    requested = []
    for i in range(1, 6):
        item = request.form.get(f"item{i}", "").strip()
        quantity = request.form.get(f"quantity{i}", "").strip()
        if not item or not quantity:
            continue
        try:
            quantity = int(quantity)
        except ValueError:
            flash(f"Quantity for {item} must be a whole number.", "error")
            return redirect("/order_screen")
        if quantity < 1:
            continue
        requested.append((item, quantity))

    if not requested:
        flash("Please choose at least one dish and a quantity.", "error")
        return redirect("/order_screen")

    try:
        db, cur = get_db()

        stock = cur.execute(
            "SELECT spice, vegetable, meat FROM ingredients WHERE item_id = 7"
        ).fetchone()
        if stock is None:
            flash("Ingredient stock is not initialised.", "error")
            return redirect("/order_screen")

        need = {"spice": 0, "vegetable": 0, "meat": 0}
        priced = []

        for item, quantity in requested:
            price_row = cur.execute(
                "SELECT price FROM Item WHERE name = ?", (item,)
            ).fetchone()
            ing_row = cur.execute(
                "SELECT i.spice, i.vegetable, i.meat FROM ingredients i "
                "JOIN Item it ON it.item_id = i.item_id WHERE it.name = ?",
                (item,),
            ).fetchone()
            if price_row is None or ing_row is None:
                flash(f"'{item}' is not available right now.", "error")
                return redirect("/order_screen")

            priced.append((item, quantity, float(price_row["price"]) * quantity))
            need["spice"] += ing_row["spice"] * quantity
            need["vegetable"] += ing_row["vegetable"] * quantity
            need["meat"] += ing_row["meat"] * quantity

        if (
            need["spice"] > stock["spice"]
            or need["vegetable"] > stock["vegetable"]
            or need["meat"] > stock["meat"]
        ):
            flash(
                "Not enough ingredients in stock for this order. "
                f"Available — spice {stock['spice']} g, vegetables {stock['vegetable']} g, "
                f"meat {stock['meat']} g.",
                "error",
            )
            return redirect("/order_screen")

        today = datetime.now().strftime("%Y-%m-%d")
        customer_id = session.get("customer_id")

        for item, quantity, total in priced:
            cur.execute(
                "INSERT INTO orders (customer_id, name, quantity, date, totalPrice) "
                "VALUES (?, ?, ?, ?, ?)",
                (customer_id, item, quantity, today, total),
            )

        cur.execute(
            "UPDATE ingredients SET spice = spice - ?, vegetable = vegetable - ?, "
            "meat = meat - ? WHERE item_id = 7",
            (need["spice"], need["vegetable"], need["meat"]),
        )
        db.commit()

        total = sum(p[2] for p in priced)
        flash(f"Order placed successfully — {len(priced)} dish(es), {total:.2f} PLN.", "success")
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
