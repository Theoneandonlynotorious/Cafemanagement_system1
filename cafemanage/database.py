import sqlite3
from datetime import datetime

DB_FILE = "cafe.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,       -- store hashed passwords in real app!
        role TEXT NOT NULL            -- e.g., 'admin', 'staff'
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        available INTEGER NOT NULL,
        description TEXT,
        inventory INTEGER DEFAULT 0
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Available'  -- Available, Occupied, Reserved
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        table_number TEXT,
        subtotal REAL,
        tax REAL,
        service_charge REAL,
        discount REAL DEFAULT 0,
        total REAL,
        date TEXT,
        time TEXT,
        status TEXT,
        payment_status TEXT DEFAULT 'Unpaid' -- Paid, Unpaid, Partial
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id),
        FOREIGN KEY(item_id) REFERENCES menu_items(item_id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    # Insert default settings if empty
    cur.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        default_settings = {
            "cafe_name": "My Cafe",
            "barcode_url": "https://mycafe.com/menu",
            "tax_rate": "0.1",
            "service_charge": "0.05"
        }
        for k, v in default_settings.items():
            cur.execute("INSERT INTO settings (key, value) VALUES (?,?)", (k, v))

    # Insert default tables if empty (example tables 1-10)
    cur.execute("SELECT COUNT(*) FROM tables")
    if cur.fetchone()[0] == 0:
        for tn in range(1, 11):
            cur.execute("INSERT INTO tables (table_number) VALUES (?)", (str(tn),))

    conn.commit()
    conn.close()
