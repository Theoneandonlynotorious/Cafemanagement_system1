import streamlit as st
import json
import os
from datetime import datetime, date
import qrcode
import io

# Import bill and mail functions
from bill_mail import build_pdf, send_email

# --- File paths ---
MENU_FILE = "menu_data.json"
ORDERS_FILE = "orders_data.json"
SETTINGS_FILE = "settings.json"
TABLES_FILE = "tables_data.json"
USERS_FILE = "users_data.json"

# --- Initialize data files ---
def initialize_data_files():
    if not os.path.exists(MENU_FILE):
        default_menu = {
            "beverages": [
                {"id": "BEV001", "name": "Espresso", "price": 2.50, "category": "Coffee",
                 "available": True, "description": "Strong black coffee", "inventory": 50},
                {"id": "BEV002", "name": "Cappuccino", "price": 3.50, "category": "Coffee",
                 "available": True, "description": "Coffee with steamed milk foam", "inventory": 40},
            ],
            "food": [
                {"id": "FOOD001", "name": "Croissant", "price": 2.50, "category": "Pastry",
                 "available": True, "description": "Buttery French pastry", "inventory": 40},
                {"id": "FOOD002", "name": "Chocolate Muffin", "price": 3.00, "category": "Pastry",
                 "available": True, "description": "Rich chocolate muffin", "inventory": 35},
            ]
        }
        with open(MENU_FILE, 'w') as f:
            json.dump(default_menu, f, indent=2)
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(SETTINGS_FILE):
        default_settings = {
            "cafe_name": "My Cafe",
            "barcode_url": "https://mycafe.com/menu",
            "tax_rate": 0.10,
            "service_charge": 0.05
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=2)
    if not os.path.exists(TABLES_FILE):
        tables = [{"table_number": str(i), "status": "Available"} for i in range(1, 11)]
        with open(TABLES_FILE, 'w') as f:
            json.dump(tables, f, indent=2)
    if not os.path.exists(USERS_FILE):
        default_users = [
            {"username": "admin", "password": "admin123", "role": "admin"},
            {"username": "staff", "password": "staff123", "role": "staff"}
        ]
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)

# --- Helper functions ---
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def authenticate(username, password):
    users = load_json(USERS_FILE) or []
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

def generate_menu_qr(cafe_url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(cafe_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

# Initialize files
initialize_data_files()

# Session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'cart' not in st.session_state:
    st.session_state['cart'] = []

# --- Login Page ---
def login_page():
    st.title("☕ Cafe Management System - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate(username, password)
        if user:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.success(f"Welcome, {user['username']}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# --- Dashboard ---
def dashboard_page():
    st.header("🏠 Dashboard")
    menu_data = load_json(MENU_FILE) or {"beverages": [], "food": []}
    orders_data = load_json(ORDERS_FILE) or []
    today_str = str(date.today())
    today_orders = [o for o in orders_data if o.get('date') == today_str]
    today_revenue = sum(o.get('total', 0) for o in today_orders)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Menu Items", sum(len(menu_data[key]) for key in menu_data))
    col2.metric("Total Orders", len(orders_data))
    col3.metric("Today's Orders", len(today_orders))
    col4.metric("Today's Revenue", f"₹{today_revenue:.2f}")

# --- Order Management (Updated with Bill + Email) ---
def order_management_page():
    st.header("🛒 Order Management")
    menu_data = load_json(MENU_FILE) or {"beverages": [], "food": []}
    orders_data = load_json(ORDERS_FILE) or []
    settings = load_json(SETTINGS_FILE) or {}
    tab1, tab2 = st.tabs(["New Order", "Order History"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        customer_name = col1.text_input("Customer Name")
        table_number = col2.text_input("Table Number (Optional)")
        customer_email = col3.text_input("Customer Email (for bill)")

        st.write("### Menu Items")
        available_items = [it for cat in menu_data.values() for it in cat if it.get("available", True)]
        for cat in sorted({it["category"] for it in available_items}):
            st.write(f"**{cat}**")
            for item in [i for i in available_items if i["category"] == cat]:
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.write(f"{item['name']} — {item.get('description', '')}")
                c2.write(f"₹{item['price']:.2f}")
                qty = c3.number_input(f"Qty {item['id']}", 0, 100, key=f"qty_{item['id']}")
                if c4.button("Add", key=f"add_{item['id']}") and qty > 0:
                    if qty > item.get("inventory", 0):
                        st.error(f"Only {item['inventory']} left of {item['name']}")
                    else:
                        st.session_state.cart.append({
                            "id": item["id"], "name": item["name"],
                            "price": item["price"], "quantity": qty,
                            "subtotal": round(item["price"] * qty, 2)
                        })
                        st.success(f"Added {qty}x {item['name']} to cart!")
                        st.rerun()

        st.subheader("Shopping Cart")
        if st.session_state.cart:
            total = sum(i["subtotal"] for i in st.session_state.cart)
            tax_rate = settings.get("tax_rate", 0.10)
            service_charge = settings.get("service_charge", 0.05)
            tax_amt = total * tax_rate
            svc_amt = total * service_charge
            final_total = total + tax_amt + svc_amt
            st.write(f"Subtotal: ₹{total:.2f}")
            st.write(f"Tax: ₹{tax_amt:.2f}")
            st.write(f"Service Charge: ₹{svc_amt:.2f}")
            st.write(f"**Total: ₹{final_total:.2f}**")
            payment_status = st.selectbox("Payment Status", ["Unpaid", "Paid", "Partial"])
            if st.button("Place Order"):
                if not customer_name:
                    st.error("Enter customer name first")
                else:
                    for ci in st.session_state.cart:
                        for cat in menu_data:
                            for it in menu_data[cat]:
                                if it["id"] == ci["id"]:
                                    it["inventory"] -= ci["quantity"]
                    save_json(MENU_FILE, menu_data)
                    new_order = {
                        "id": f"ORD{len(orders_data)+1:05d}",
                        "customer_name": customer_name,
                        "table_number": table_number,
                        "items": st.session_state.cart.copy(),
                        "subtotal": total,
                        "discount": 0.0,
                        "tax": tax_amt,
                        "service_charge": svc_amt,
                        "total": final_total,
                        "date": str(date.today()),
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": datetime.now().isoformat(),
                        "status": "Pending",
                        "payment_status": payment_status
                    }
                    orders_data.append(new_order)
                    save_json(ORDERS_FILE, orders_data)

                    # Bill PDF
                    try:
                        pdf_bytes = build_pdf(new_order)
                    except Exception as e:
                        st.error(f"Bill generation failed: {e}")
                        pdf_bytes = None

                    # Send Email if available
                    if customer_email and pdf_bytes:
                        try:
                            send_email(customer_email, new_order, pdf_bytes)
                            st.success(f"Bill emailed to {customer_email}")
                        except Exception as e:
                            st.error(f"Email failed: {e}")

                    # Download link
                    if pdf_bytes:
                        st.download_button(
                            "📄 Download Bill PDF",
                            pdf_bytes,
                            file_name=f"{new_order['id']}.pdf",
                            mime="application/pdf"
                        )

                    st.balloons()
                    st.session_state.cart = []
        else:
            st.info("No items in cart yet.")

    with tab2:
        orders = load_json(ORDERS_FILE) or []
        if not orders:
            st.info("No orders found")
            return
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Preparing", "Ready", "Completed", "Cancelled"])
        if status_filter != "All":
            orders = [o for o in orders if o["status"] == status_filter]
        for order in orders:
            with st.expander(f"{order['id']} - {order['customer_name']}"):
                st.write(order)

# Table management, sales analytics, settings pages would be same as your version unchanged
# For brevity, not pasting unchanged functions

# --- Main ---
def main():
    st.set_page_config(page_title="Cafe Management System", page_icon="☕", layout="wide")
    if not st.session_state.get('logged_in'):
        login_page()
        return
    user = st.session_state['user']
    st.sidebar.title(f"Logged in as: {user['username']} ({user['role']})")
    menu_options = ["Dashboard", "Order Management", "Logout"] if user["role"] == "staff" else \
                   ["Dashboard", "Order Management", "Logout"]
    choice = st.sidebar.selectbox("Navigation", menu_options)
    if choice == "Dashboard":
        dashboard_page()
    elif choice == "Order Management":
        order_management_page()
    elif choice == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.session_state['cart'] = []
        st.rerun()

if __name__ == "__main__":
    main()
