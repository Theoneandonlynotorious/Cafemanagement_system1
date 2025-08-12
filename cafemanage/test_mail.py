from bill_mail import send_email
fake_order = {"id":"TEST123","customer_name":"Test","date":"2025-08-03","time":"12:00",
              "items":[{"name":"Coffee","quantity":1,"price":2.5,"subtotal":2.5}],
              "subtotal":2.5,"discount":0,"tax":0.25,"service_charge":0.12,"total":2.87}
pdf = b"fake pdf bytes"
send_email("your_own_email@gmail.com", fake_order, pdf)
print("mail sent")