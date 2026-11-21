from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = '123456'

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="assignment3database"
)
cursor = db.cursor()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/sales_clerk_login', methods=['POST'])
def sales_clerk_login():
    email = request.form['email']
    password = request.form['password']
    # Check if credentials exist in the database
    query = "SELECT * FROM SalesClerk WHERE email=%s AND password=%s"
    cursor.execute(query, (email, password))
    sales_clerk = cursor.fetchone()
    if sales_clerk:
        # Store logged-in user in session
        session['user'] = email
        return redirect('/sales_clerk_dashboard')
    else:
        return "Invalid credentials. Please try again."

@app.route('/customer_login', methods=['POST'])
def customer_login():
    name = request.form['name']
    telephone = request.form['telephone']
    email = request.form['email']
    
    # Check if customer exists in the database
    query = "SELECT * FROM Customer WHERE customerName=%s AND telephoneNum=%s AND email=%s"
    cursor.execute(query, (name, telephone, email))
    customer = cursor.fetchone()
    
    if customer:
        # Customer already exists, store logged-in user in session
        session['user'] = name
        session['customer_id'] = customer[2]
        return redirect('/customer_dashboard')
    else:
        # Insert new customer into the database
        insert_query = "INSERT INTO Customer (customerName, telephoneNum, email) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (name, telephone, email))
        db.commit()  # Commit the transaction
        
        # Retrieve the auto-generated customer_id
        customer_id = cursor.lastrowid
        
        # Store logged-in user, customer_id, and email in session
        session['user'] = name
        session['customer_id'] = customer_id
        session['email'] = email
        
        return redirect('/customer_dashboard')


@app.route('/sales_clerk_dashboard')
def sales_clerk_dashboard():
    # Check if user is logged in
    if 'user' in session:
        user = session['user']
        return render_template('sales_clerk_dashboard.html')
    else:
        return redirect('/')
@app.route('/customer_dashboard')
def customer_dashboard():
    # Check if user is logged in
    if 'user' in session:
        # Fetch item names from the database
        cursor.execute("SELECT name FROM Item")
        items = [item[0] for item in cursor.fetchall()]
        user = session['user']
        return render_template('order.html', user=user, items=items)  # Pass 'items' to the template
    else:
        return redirect('/')
@app.route('/view_orders')
def view_orders():
    if 'user' in session:
        try:
            # Part 1: Retrieve Customer Name, Contact No, and Order Date
            cursor.execute("SELECT customerName, contactNo, orderDate FROM orders GROUP BY customerName, contactNo, orderDate")
            customer_details = cursor.fetchall()

            # Part 2: Fetch Order IDs where Customer Name, Contact No, and Order Date are equal
            orders_with_ids = []
            for customer in customer_details:
                customer_name, contact_no, order_date = customer
                cursor.execute("SELECT GROUP_CONCAT(orderID) FROM orders WHERE customerName=%s AND contactNo=%s AND orderDate=%s", (customer_name, contact_no, order_date))
                order_ids = cursor.fetchone()[0]
                orders_with_ids.append((customer_name, contact_no, order_date, order_ids))

            # Part 3: Calculate the total PLN
            total_pln = 0
            for customer in customer_details:
                customer_name, contact_no, order_date = customer
                cursor.execute("SELECT SUM(totalPrice) FROM orders WHERE customerName=%s AND contactNo=%s AND orderDate=%s", (customer_name, contact_no, order_date))
                total_price = cursor.fetchone()[0]
                total_pln += total_price

            return render_template('view_orders.html', orders_with_ids=orders_with_ids, total_pln=total_pln)
        except Exception as e:
            # Handle any exceptions
            return f"Error: {str(e)}"
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    # Remove user from session
    session.pop('user', None)
    return redirect('/')

@app.route('/order_screen')
def order_screen():
    if 'user' in session:
        return render_template('order.html')
    else:
        return redirect('/')


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user' in session:
        user = session['user']
        customer_id = session['customer_id']
        
        # Begin a database transaction
        try:
            db.start_transaction()
            
            # Initialize lists to store items and quantities
            items = []
            quantities = []
            
            # Retrieve all item names and quantities from the form
            for i in range(1, 6):  # Assuming a maximum of 5 items can be ordered in one transaction
                item_key = f"item{i}"
                quantity_key = f"quantity{i}"
                
                if item_key in request.form and quantity_key in request.form:
                    item = request.form[item_key]
                    quantity = int(request.form[quantity_key])
                    
                    # Retrieve item details (such as price) from the database
                    query_item_price = "SELECT price FROM item WHERE name = %s"
                    cursor.execute(query_item_price, (item,))
                    item_price = cursor.fetchone()[0]  # Assuming it returns a single row
                    
                    # Calculate the total price
                    total_price = item_price * quantity
                    
                    # Retrieve the quantities of spices, vegetables, and meat used from the ingredients table
                    query_ingredient_quantities = "SELECT spice, vegetable, meat FROM ingredients WHERE item_id = (SELECT item_id FROM item WHERE name = %s)"
                    cursor.execute(query_ingredient_quantities, (item,))
                    used_spice, used_vegetable, used_meat = cursor.fetchone()
                    
                    # Get the total spice, vegetable, and meat quantities from the ingredients table
                    query_total_ingredients = "SELECT spice, vegetable, meat FROM ingredients WHERE item_id = 7"
                    cursor.execute(query_total_ingredients)
                    total_spice, total_vegetable, total_meat = cursor.fetchone()  # Assuming it returns a single row
                    
                    # Calculate the new quantities after deducting the used quantities for the order
                    new_spice = total_spice - used_spice * quantity
                    new_vegetable = total_vegetable - used_vegetable * quantity
                    new_meat = total_meat - used_meat * quantity
                    
                    # Check if any of the new quantities are negative, indicating insufficient ingredients
                    if new_spice < 0 or new_vegetable < 0 or new_meat < 0:
                        # Rollback the transaction and return an error message
                        db.rollback()
                        return "Error: Not enough ingredients to place the order."
                    
                    # Insert the order into the database with a unique order ID
                    insert_query = "INSERT INTO orders (customer_id, name, quantity, date, totalPrice) VALUES (%s, %s, %s, %s, %s)"
                    date = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute(insert_query, (customer_id, item, quantity, date, total_price))
                
            # Commit the transaction
            db.commit()
            
            return "Order placed successfully!"
        except Exception as e:
            # Rollback the transaction in case of an error
            db.rollback()
            return f"Error: {str(e)}"
    else:
        return redirect('/')


    



if __name__ == '__main__':
    app.run(debug=True)
