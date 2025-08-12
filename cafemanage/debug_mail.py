from bill_mail import send_email
import datetime
order = {
    "id": "DEBUG001",
    "customer_name": "Debug",
    "date": str(datetime.date.today()),
    "time": "now",
    "items": [{"name":"Test","quantity":1,"price":1,"subtotal":1}],
    "subtotal":1, "discount":0, "tax":0.1, "service_charge":0.05, "total":1.15
}
pdf = b"%PDF-1.4 fake pdf bytes"
send_email("your_own_real_address@gmail.com", order, pdf)
print("debug_mail.py finished")