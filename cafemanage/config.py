# Configuration file for Cafe Management System

# Default settings
DEFAULT_SETTINGS = {
    "cafe_name": "My Cafe",
    "barcode_url": "https://mycafe.com/menu",
    "tax_rate": 0.10,  # 10%
    "service_charge": 0.05,  # 5%
    "currency": "USD",
    "currency_symbol": "₹"
}

# File paths
DATA_FILES = {
    "menu": "menu_data.json",
    "orders": "orders_data.json",
    "settings": "settings.json"
}

# Default menu categories
MENU_CATEGORIES = {
    "beverages": ["Coffee", "Tea", "Juice", "Smoothie", "Soft Drink"],
    "food": ["Pastry", "Sandwich", "Salad", "Pizza", "Pasta", "Burger"]
}

# Order statuses
ORDER_STATUSES = ["Pending", "Preparing", "Ready", "Completed", "Cancelled"]

# Supported barcode formats
SUPPORTED_BARCODE_FORMATS = [
    "QR_CODE", 
    "CODE128", 
    "CODE39", 
    "EAN13", 
    "EAN8", 
    "UPCA", 
    "UPCE"
]

# Image settings for barcode scanning
IMAGE_SETTINGS = {
    "max_size": (800, 600),  # Max image size for processing
    "supported_formats": ["PNG", "JPG", "JPEG", "BMP"],
    "quality": 85
}