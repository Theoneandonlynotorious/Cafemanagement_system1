import streamlit as st
import json
import os
from datetime import datetime, date
import qrcode
import io

# ✅ Import PDF and Email helpers
from bill_mail import build_pdf, send_email

# --- File paths ---
MENU_FILE = "menu_data.json"
ORDERS_FILE = "orders_data.json"
SETTINGS_FILE = "settings.json"
TABLES_FILE = "tables_data.json"  # New file for tables
USERS_FILE = "users_data.json"    # New file for users (auth)

# --- Initialize data files with defaults if missing ---
def initialize_data_files():
    if not os.path.exists(MENU_FILE):
        default_menu = {
            "beverages": [
                {"id": "BEV001", "name": "Espresso", "price": 2.50, "category": "Coffee",
                 "available": True, "description": "Strong black coffee", "inventory": 50},
                {"id": "BEV002", "name": "Cappuccino", "price": 3.50, "category": "Coffee",
                 "available": True, "description": "Coffee with steamed milk foam", "inventory": 40},
                {"id": "BEV003", "name": "Latte", "price": 4.00, "category": "Coffee",
                 "available": True, "description": "Coffee with steamed milk", "inventory": 40},
                {"id": "BEV004", "name": "Green Tea", "price": 2.00, "category": "Tea",
                 "available": True, "description": "Fresh green tea", "inventory": 30},
                {"id": "BEV005", "name": "Fresh Orange Juice", "price": 3.00, "category": "Juice",
                 "available": True, "description": "Freshly squeezed orange juice", "inventory": 25}
            ],
            "food": [
                {"id": "FOOD001", "name": "Croissant", "price": 2.50, "category": "Pastry",
                 "available": True, "description": "Buttery French pastry", "inventory": 40},
                {"id": "FOOD002", "name": "Chocolate Muffin", "price": 3.00, "category": "Pastry",
                 "available": True, "description": "Rich chocolate muffin", "inventory": 35},
                {"id": "FOOD003", "name": "Caesar Salad", "price": 8.50, "category": "Salad",
                 "available": True, "description": "Fresh romaine with caesar dressing", "inventory": 20},
                {"id": "FOOD004", "name": "Club Sandwich", "price": 9.00, "category": "Sandwich",
                 "available": True, "description": "Triple layer sandwich with turkey and bacon", "inventory": 30},
                {"id": "FOOD005", "name": "Margherita Pizza", "price": 12.00, "category": "Pizza",
                 "available": True, "description": "Classic pizza with tomato and mozzarella", "inventory": 15}
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

# --- Load/save helpers ---
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# --- Authentication functions ---
def authenticate(username, password):
    users = load_json(USERS_FILE) or []
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

# --- QR Code generation ---
def generate_menu_qr(cafe_url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(cafe_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

initialize_data_files()

# --- Session State Init ---
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

# --- Dashboard Page ---
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

# --- Table Management ---
def table_management_page():
    tables = load_json(TABLES_FILE) or []
    orders = load_json(ORDERS_FILE) or []
    def is_table_busy(tn: str) -> bool:
        return any(o.get("table_number") == tn and o.get("status") in {"Pending", "Preparing", "Ready"} for o in orders)
    changed = False
    for t in tables:
        should_be = "Occupied" if is_table_busy(t["table_number"]) else "Available"
        if t["status"] != should_be:
            t["status"] = should_be
            changed = True
    if changed:
        save_json(TABLES_FILE, tables)
    status_options = ["Available", "Occupied", "Reserved"]
    manual_change = False
    for idx, table in enumerate(tables):
        col1, col2, col3 = st.columns([1, 2, 1])
        col1.write(table["table_number"])
        col2.write(table["status"])
        new_status = col3.selectbox(
            "Change",
            status_options,
            index=status_options.index(table["status"]),
            key=f"tbl_{table['table_number']}"
        )
        if new_status != table["status"]:
            tables[idx]["status"] = new_status
            manual_change = True
    if manual_change:
        save_json(TABLES_FILE, tables)
        st.success("Table statuses updated")

# --- Order Management ---
def order_management_page():
    st.header("🛒 Order Management")
    menu_data = load_json(MENU_FILE) or {"beverages": [], "food": []}
    orders_data = load_json(ORDERS_FILE) or []
    settings = load_json(SETTINGS_FILE) or {}
    tab1, tab2 = st.tabs(["New Order", "Order History"])

    with tab1:
        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            customer_name = st.text_input("Customer Name")
        with col_mid:
            table_number = st.text_input("Table Number (Optional)")
        with col_right:
            customer_email = st.text_input("Customer e-mail (for bill)")

        st.write("### Menu Items")
        all_items = [it for cat in menu_data.values() for it in cat if it.get("available", True)]
        for cat in sorted({it["category"] for it in all_items}):
            st.write(f"**{cat}**")
            for item in [i for i in all_items if i["category"] == cat]:
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
            st.write(f"Tax ({tax_rate*100:.0f}%): +₹{tax_amt:.2f}")
            st.write(f"Service Charge ({service_charge*100:.0f}%): +₹{svc_amt:.2f}")
            st.write(f"**Total: ₹{final_total:.2f}**")
            payment_status = st.selectbox("Payment Status", ["Unpaid", "Paid", "Partial"])

            if st.button("Place Order"):
                if not customer_name:
                    st.error("Enter customer name")
                elif not st.session_state.cart:
                    st.error("Cart is empty")
                else:
                    for ci in st.session_state.cart:
                        for cat in menu_data:
                            for it in menu_data[cat]:
                                if it["id"] == ci["id"]:
                                    if ci["quantity"] > it.get("inventory", 0):
                                        st.error(f"Not enough inventory for {it['name']}")
                                        return
                                    it["inventory"] -= ci["quantity"]
                    save_json(MENU_FILE, menu_data)

                    new_order = {
                        "id": f"ORD{len(orders_data)+1:05d}",
                        "customer_name": customer_name,
                        "table_number": table_number,
                        "items": st.session_state.cart.copy(),
                        "subtotal": total,
                        "discount": 0.0,  # ensure exists
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

                    # ✅ Generate PDF
                    try:
                        pdf_bytes = build_pdf(new_order)
                    except Exception as e:
                        st.error(f"Error generating PDF: {e}")
                        pdf_bytes = None

                    # ✅ Send Email
                    if customer_email and pdf_bytes:
                        try:
                            send_email(customer_email, new_order, pdf_bytes)
                            st.success(f"Bill sent to {customer_email}")
                        except Exception as e:
                            st.error(f"Email failed: {e}")

                    # ✅ Download Button
                    if pdf_bytes:
                        st.download_button(
                            "📄 Download Bill PDF",
                            pdf_bytes,
                            file_name=f"{new_order['id']}.pdf",
                            mime="application/pdf"
                        )

                    st.balloons()
                    st.success(f"Order placed! ID: {new_order['id']}")
                    st.session_state.cart = []
        else:
            st.info("Add items to the cart from above menu.")

    with tab2:
        st.subheader("Order History")
        orders = load_json(ORDERS_FILE) or []
        if not orders:
            st.info("No orders found")
            return
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Preparing", "Ready", "Completed", "Cancelled"])
        date_filter = st.date_input("Filter by Date", None)
        filt = orders
        if status_filter != "All":
            filt = [o for o in filt if o.get("status") == status_filter]
        if date_filter:
            filt = [o for o in filt if o.get("date") == str(date_filter)]
        filt = sorted(filt, key=lambda x: x["timestamp"], reverse=True)
        for order in filt:
            with st.expander(f"{order['id']} by {order['customer_name']} — ₹{order['total']:.2f} ({order.get('status')})"):
                st.write(f"Date: {order['date']} {order['time']} | Table: {order.get('table_number', '-')}")
                for it in order["items"]:
                    st.write(f"- {it['name']} x{it['quantity']} = ₹{it['subtotal']:.2f}")
                st.write(f"Subtotal: ₹{order['subtotal']:.2f}")
                st.write(f"Tax: ₹{order.get('tax', 0):.2f}")
                st.write(f"Service Charge: ₹{order.get('service_charge', 0):.2f}")
                st.write(f"**Total: ₹{order['total']:.2f}**")
                st.write(f"Payment: {order.get('payment_status', 'Unpaid')}")
                new_status = st.selectbox("Update Status", ["Pending", "Preparing", "Ready", "Completed", "Cancelled"],
                                          index=["Pending", "Preparing", "Ready", "Completed", "Cancelled"].index(order.get("status", "Pending")),
                                          key=f"status_{order['id']}")
                if st.button("Update", key=f"upd_{order['id']}"):
                    for o in orders:
                        if o["id"] == order["id"]:
                            o["status"] = new_status
                            save_json(ORDERS_FILE, orders)
                            st.success("Status updated")
                            st.rerun()

# --- Other functions unchanged: sales_analytics_page(), settings_page() ---

def main():
    st.set_page_config(page_title="Cafe Management System", page_icon="☕", layout="wide")
    if not st.session_state.get('logged_in'):
        login_page()
        return
    user = st.session_state['user']
    st.sidebar.title(f"Logged in as: {user['username']} ({user['role']})")
    admin_options = ["Dashboard", "Menu Management", "Order Management", "Sales Analytics", "Table Management", "Settings", "Logout"]
    staff_options = ["Dashboard", "Order Management", "Table Management", "Logout"]
    menu_options = admin_options if user["role"] == "admin" else staff_options
    choice = st.sidebar.selectbox("Navigation", menu_options)
    if choice == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['user'] = None
        st.session_state['cart'] = []
        st.experimental_rerun()
    elif choice == "Dashboard":
        dashboard_page()
    elif choice == "Menu Management":
        if user['role'] == 'admin':
            menu_management_page()
        else:
            st.warning("Only admin can access menu management.")
    elif choice == "Order Management":
        order_management_page()
    elif choice == "Sales Analytics":
        if user['role'] == 'admin':
            sales_analytics_page()
        else:
            st.warning("Only admin can access sales analytics.")
    elif choice == "Table Management":
        table_management_page()
    elif choice == "Settings":
        if user['role'] == 'admin':
            settings_page()
        else:
            st.warning("Only admin can access settings.")

if __name__ == "__main__":
    if 'cart' not in st.session_state:
        st.session_state['cart'] = []
    main()
