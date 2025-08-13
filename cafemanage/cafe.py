# app.py
import streamlit as st
import json
import os
from datetime import datetime, date
import qrcode
import io
from streamlit_autorefresh import st_autorefresh   # NEW for live refresh

# ✅ Import PDF and Email helpers (keep your existing files)
from bill_mail import build_pdf, send_email

# --- File paths ---
MENU_FILE = "menu_data.json"
ORDERS_FILE = "orders_data.json"
SETTINGS_FILE = "settings.json"
TABLES_FILE = "tables_data.json"
USERS_FILE = "users_data.json"

# --- Initialize data files with defaults if missing ---
def initialize_data_files():
    for f, default in [
        (MENU_FILE,
         {"beverages": [
             {"id": "BEV001", "name": "Espresso", "price": 2.50,
              "category": "Coffee", "available": True,
              "description": "Strong black coffee", "inventory": 50},
             {"id": "BEV002", "name": "Cappuccino", "price": 3.50,
              "category": "Coffee", "available": True,
              "description": "Coffee with steamed milk foam", "inventory": 40},
             {"id": "BEV003", "name": "Latte", "price": 4.00,
              "category": "Coffee", "available": True,
              "description": "Coffee with steamed milk", "inventory": 40},
             {"id": "BEV004", "name": "Green Tea", "price": 2.00,
              "category": "Tea", "available": True,
              "description": "Fresh green tea", "inventory": 30},
             {"id": "BEV005", "name": "Fresh Orange Juice", "price": 3.00,
              "category": "Juice", "available": True,
              "description": "Freshly squeezed orange juice", "inventory": 25}],
          "food": [
             {"id": "FOOD001", "name": "Croissant", "price": 2.50,
              "category": "Pastry", "available": True,
              "description": "Buttery French pastry", "inventory": 40},
             {"id": "FOOD002", "name": "Chocolate Muffin", "price": 3.00,
              "category": "Pastry", "available": True,
              "description": "Rich chocolate muffin", "inventory": 35},
             {"id": "FOOD003", "name": "Caesar Salad", "price": 8.50,
              "category": "Salad", "available": True,
              "description": "Fresh romaine with caesar dressing", "inventory": 20},
             {"id": "FOOD004", "name": "Club Sandwich", "price": 9.00,
              "category": "Sandwich", "available": True,
              "description": "Triple layer sandwich with turkey and bacon", "inventory": 30},
             {"id": "FOOD005", "name": "Margherita Pizza", "price": 12.00,
              "category": "Pizza", "available": True,
              "description": "Classic pizza with tomato and mozzarella", "inventory": 15}]}),
        (ORDERS_FILE, []),
        (SETTINGS_FILE,
         {"cafe_name": "My Cafe",
          "barcode_url": "https://mycafe.com/menu",
          "tax_rate": 0.10, "service_charge": 0.05}),
        (TABLES_FILE,
         [{"table_number": str(i), "status": "Available"} for i in range(1, 11)]),
        (USERS_FILE,
         [{"username": "admin", "password": "admin123", "role": "admin"},
          {"username": "staff", "password": "staff123", "role": "staff"}])
    ]:
        if not os.path.exists(f):
            with open(f, 'w') as fp:
                json.dump(default, fp, indent=2)

# --- Load / save helpers ---
def load_json(fp):   # safe loader
    try:
        with open(fp) as f:
            return json.load(f)
    except Exception:
        return None

def save_json(fp, data):
    with open(fp, 'w') as f:
        json.dump(data, f, indent=2)

# --- Auth ---
def authenticate(username, password):
    users = load_json(USERS_FILE) or []
    return next((u for u in users if u['username'] == username and u['password'] == password), None)

# --- QR helper ---
def generate_menu_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

initialize_data_files()

# --- Session defaults ---
for k in ('logged_in', 'user', 'cart'):
    if k not in st.session_state:
        st.session_state[k] = [] if k == 'cart' else (None if k == 'user' else False)

# ----------------------------------------------------------
# PAGES
# ----------------------------------------------------------
def login_page():
    st.title("☕ Cafe Management System – Login")
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
            st.error("Invalid credentials")

def dashboard_page():
    st.header("🏠 Dashboard")
    menu = load_json(MENU_FILE) or {"beverages": [], "food": []}
    orders = load_json(ORDERS_FILE) or []
    today_str = str(date.today())
    today_orders = [o for o in orders if o.get('date') == today_str]
    revenue = sum(o['total'] for o in today_orders)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Menu Items", sum(len(menu[k]) for k in menu))
    c2.metric("Total Orders", len(orders))
    c3.metric("Today's Orders", len(today_orders))
    c4.metric("Today's Revenue", f"₹{revenue:.2f}")

# --------------- LIVE TABLE MANAGEMENT ---------------------------------
def table_management_page():
    st.header("🪑 Table Management – Auto Mode")
    tables = load_json(TABLES_FILE) or []
    orders = load_json(ORDERS_FILE) or []

    # 1. Real busy tables
    busy = {
        o.get("table_number")
        for o in orders
        if o.get("table_number") and o.get("status") not in {"Completed", "Cancelled"}
    }

    # 2. Auto-sync
    changed = False
    for t in tables:
        should = "Occupied" if t["table_number"] in busy else "Available"
        if t["status"] != should:
            t["status"] = should
            changed = True
    if changed:
        save_json(TABLES_FILE, tables)

    # 3. Display / manual override
    st.info("💡 Automation keeps tables in sync.  Toggle below only for special cases.")
    for idx, tbl in enumerate(tables):
        c1, c2, c3 = st.columns([1, 2, 2])
        c1.write(f"**Table {tbl['table_number']}**")
        c2.write(tbl["status"])
        override = c3.toggle("Reserve", key=f"man_{tbl['table_number']}")
        if tbl["table_number"] not in busy:   # automation not in charge
            new = "Reserved" if override else "Available"
            if tbl["status"] != new:
                tbl["status"] = new
                save_json(TABLES_FILE, tables)
                st.rerun()

# --------------- ORDER MANAGEMENT + LIVE TABLE PICKER ------------------
def order_management_page():
    st.header("🛒 Order Management")
    menu = load_json(MENU_FILE) or {"beverages": [], "food": []}
    orders = load_json(ORDERS_FILE) or []
    settings = load_json(SETTINGS_FILE) or {}

    # Live refresh every 3 seconds for the table grid
    st_autorefresh(interval=3000, limit=None, key="order_refresh")

    tab1, tab2 = st.tabs(["New Order", "Order History"])

    with tab1:
        col_left, col_mid, col_right = st.columns(3)
        with col_left:
            customer_name = st.text_input("Customer Name")
        with col_mid:
            customer_email = st.text_input("Customer e-mail (for bill)")
        with col_right:
            pass

        # ---- LIVE TABLE PICKER --------------------------------------
        tables = load_json(TABLES_FILE) or []
        available = [t for t in tables if t["status"] == "Available"]
        st.write("#### Pick your table")
        tbl_cols = st.columns(5)
        table_number = None
        for idx, tbl in enumerate(tables):
            col = tbl_cols[idx % 5]
            color = "green" if tbl["status"] == "Available" else "red"
            disabled = tbl["status"] != "Available"
            if col.button(
                f"**{tbl['table_number']}**",
                disabled=disabled,
                key=f"pick_{tbl['table_number']}",
                help=f"Status: {tbl['status']}"
            ):
                table_number = tbl["table_number"]
        if table_number:
            st.info(f"Selected table: {table_number}")

        # ---- MENU ----------------------------------------------------
        st.write("### Menu Items")
        all_items = [it for cat in menu.values() for it in cat if it.get("available", True)]
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

        # ---- CART ----------------------------------------------------
        st.subheader("Shopping Cart")
        if st.session_state.cart:
            sub = sum(i["subtotal"] for i in st.session_state.cart)
            tax = sub * settings.get("tax_rate", 0.1)
            svc = sub * settings.get("service_charge", 0.05)
            total = sub + tax + svc
            st.write(f"Subtotal: ₹{sub:.2f}")
            st.write(f"Tax: ₹{tax:.2f}")
            st.write(f"Service Charge: ₹{svc:.2f}")
            st.write(f"**Total: ₹{total:.2f}**")
            payment = st.selectbox("Payment Status", ["Unpaid", "Paid", "Partial"])

            if st.button("Place Order"):
                if not customer_name:
                    st.error("Enter customer name")
                else:
                    # reduce inventory
                    for ci in st.session_state.cart:
                        for cat in menu:
                            for it in menu[cat]:
                                if it["id"] == ci["id"]:
                                    it["inventory"] -= ci["quantity"]
                    save_json(MENU_FILE, menu)

                    new_order = {
                        "id": f"ORD{len(orders)+1:05d}",
                        "customer_name": customer_name,
                        "table_number": table_number,
                        "items": st.session_state.cart.copy(),
                        "subtotal": sub,
                        "discount": 0.0,
                        "tax": tax,
                        "service_charge": svc,
                        "total": total,
                        "date": str(date.today()),
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "timestamp": datetime.now().isoformat(),
                        "status": "Pending",
                        "payment_status": payment
                    }
                    orders.append(new_order)
                    save_json(ORDERS_FILE, orders)

                    # PDF + email
                    try:
                        pdf_bytes = build_pdf(new_order)
                    except Exception as e:
                        st.error(f"PDF error: {e}")
                        pdf_bytes = None
                    if customer_email and pdf_bytes:
                        try:
                            send_email(customer_email, new_order, pdf_bytes)
                            st.success("Bill emailed!")
                        except Exception as e:
                            st.error(f"Email error: {e}")
                    if pdf_bytes:
                        st.download_button("📄 Download Bill", pdf_bytes,
                                           file_name=f"{new_order['id']}.pdf",
                                           mime="application/pdf")
                    st.balloons()
                    st.success(f"Order placed – {new_order['id']}")
                    st.session_state.cart.clear()
                    st.rerun()
        else:
            st.info("Add items to the cart from above menu.")

    # ---- ORDER HISTORY --------------------------------------------
    with tab2:
        st.subheader("Order History")
        if not orders:
            st.info("No orders yet")
            return
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Preparing", "Ready", "Completed", "Cancelled"])
        date_filter = st.date_input("Filter by Date", None)
        filt = orders
        if status_filter != "All":
            filt = [o for o in filt if o.get("status") == status_filter]
        if date_filter:
            filt = [o for o in filt if o.get("date") == str(date_filter)]
        filt = sorted(filt, key=lambda x: x["timestamp"], reverse=True)
        for o in filt:
            with st.expander(f"{o['id']} – {o['customer_name']} | ₹{o['total']:.2f} ({o['status']})"):
                st.write(f"Date: {o['date']} {o['time']} | Table: {o.get('table_number', '-')}")
                for it in o["items"]:
                    st.write(f"- {it['name']} x{it['quantity']} = ₹{it['subtotal']:.2f}")
                st.write(f"Total: ₹{o['total']:.2f} | Payment: {o.get('payment_status')}")
                new_status = st.selectbox("Update Status", ["Pending", "Preparing", "Ready", "Completed", "Cancelled"],
                                          index=["Pending", "Preparing", "Ready", "Completed", "Cancelled"].index(o["status"]),
                                          key=f"upd_{o['id']}")
                if st.button("Update", key=f"btn_{o['id']}"):
                    o["status"] = new_status
                    save_json(ORDERS_FILE, orders)
                    st.success("Updated")
                    st.rerun()

# ----------------------------------------------------------
#  Dummy stubs so the file still runs
# ----------------------------------------------------------
def menu_management_page():
    st.write("Menu management not implemented in this snippet")

def sales_analytics_page():
    st.write("Sales analytics not implemented in this snippet")

def settings_page():
    st.write("Settings not implemented in this snippet")

# ----------------------------------------------------------
#  MAIN NAVIGATION
# ----------------------------------------------------------
def main():
    st.set_page_config(page_title="Cafe Management", page_icon="☕", layout="wide")
    if not st.session_state['logged_in']:
        login_page()
        return
    user = st.session_state['user']
    st.sidebar.title(f"Logged in as: {user['username']} ({user['role']})")
    opts = (["Dashboard", "Menu Management", "Order Management",
             "Sales Analytics", "Table Management", "Settings", "Logout"]
            if user["role"] == "admin"
            else ["Dashboard", "Order Management", "Table Management", "Logout"])
    choice = st.sidebar.selectbox("Navigation", opts)
    if choice == "Logout":
        st.session_state.clear()
        st.rerun()
    elif choice == "Dashboard":
        dashboard_page()
    elif choice == "Menu Management" and user["role"] == "admin":
        menu_management_page()
    elif choice == "Order Management":
        order_management_page()
    elif choice == "Sales Analytics" and user["role"] == "admin":
        sales_analytics_page()
    elif choice == "Table Management":
        table_management_page()
    elif choice == "Settings" and user["role"] == "admin":
        settings_page()
    else:
        st.warning("Access denied")

if __name__ == "__main__":
    if 'cart' not in st.session_state:
        st.session_state['cart'] = []
    main()

