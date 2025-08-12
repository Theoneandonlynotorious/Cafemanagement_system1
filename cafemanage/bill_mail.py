import io
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------
# Gmail credentials
# ---------------------------------------------------------
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USERNAME = "mycafe480@gmail.com"
SMTP_PASSWORD = "vufa rafh vzlz bgqv"
FROM_EMAIL    = SMTP_USERNAME

# ---------------------------------------------------------
# Font registration (₹ support if possible)
# ---------------------------------------------------------
FONT_PATH = os.path.join(os.path.dirname(__file__), "dejavu-fonts-ttf-2.37", "ttf", "DejaVuSans.ttf")
HAS_DEJAVU = False

if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("DejaVu", FONT_PATH))
    HAS_DEJAVU = True
else:
    print(f"[bill_mail.py] Warning: DejaVuSans.ttf not found at {FONT_PATH}. Using Helvetica instead.")

def build_pdf(order_dict: dict) -> bytes:
    """Generate a clean PDF bill, with ₹ support if available."""
    LEFT, RIGHT = 2 * cm, 17.5 * cm
    LINE_H = 0.55 * cm

    rows = len(order_dict["items"]) + 6
    page_height = 4 * cm + rows * LINE_H + 1 * cm
    page_size = (RIGHT + 1 * cm, page_height)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_size[0] / 2, page_height - 1.2 * cm, f"Bill – {order_dict['id']}")

    # Meta info
    c.setFont("Helvetica", 10)
    y = page_height - 2.2 * cm
    meta = [
        f"Customer : {order_dict['customer_name']}",
        f"Table    : {order_dict.get('table_number') or 'Take-away'}",
        f"Date     : {order_dict['date']}  {order_dict['time']}"
    ]
    for line in meta:
        c.drawString(LEFT, y, line)
        y -= LINE_H

    # Headers
    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(LEFT, y, "Item")
    c.drawRightString(10 * cm, y, "Qty")
    c.setFont("DejaVu" if HAS_DEJAVU else "Helvetica", 9)
    c.drawRightString(12.5 * cm, y, "Price (₹)" if HAS_DEJAVU else "Price")
    c.drawRightString(17 * cm, y, "Subtotal (₹)" if HAS_DEJAVU else "Subtotal")
    c.setFont("Helvetica", 9)  # Reset for item rows
    y -= LINE_H

    # Items
    for it in order_dict["items"]:
        c.drawString(LEFT, y, it["name"])
        c.drawRightString(10 * cm, y, str(it["quantity"]))
        c.setFont("DejaVu" if HAS_DEJAVU else "Helvetica", 9)
        price_str = f"₹{it['price']:.2f}" if HAS_DEJAVU else f"{it['price']:.2f}"
        subtotal_str = f"₹{it['subtotal']:.2f}" if HAS_DEJAVU else f"{it['subtotal']:.2f}"
        c.drawRightString(12.5 * cm, y, price_str)
        c.drawRightString(17 * cm, y, subtotal_str)
        c.setFont("Helvetica", 9)
        y -= LINE_H

    # Totals
    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 10)
    totals = [
        ("Subtotal",  order_dict["subtotal"]),
        ("Discount", -order_dict["discount"]),
        ("Tax",       order_dict["tax"]),
        ("Service",   order_dict["service_charge"]),
        ("Total",     order_dict["total"])
    ]
    for label, value in totals:
        c.drawRightString(15 * cm, y, f"{label}:")
        c.setFont("DejaVu" if HAS_DEJAVU else "Helvetica", 10)
        value_str = f"₹{value:.2f}" if HAS_DEJAVU else f"{value:.2f}"
        c.drawRightString(17 * cm, y, value_str)
        c.setFont("Helvetica-Bold", 10)
        y -= LINE_H

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(page_size[0] / 2, 0.8 * cm, "Thank you for visiting My Café!")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def send_email(to_email: str, order_dict: dict, pdf_bytes: bytes):
    """Send the PDF bill via email."""
    if not to_email.strip():
        return
    subject = f"Your bill – {order_dict['id']}"
    body = (
        f"Hi {order_dict['customer_name']},\n\n"
        f"Please find your bill attached.\n"
        f"Thank you for visiting us!\n\n"
        f"Regards,\nMy Café"
    )

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email.strip()
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    att = MIMEApplication(pdf_bytes, _subtype="pdf")
    att.add_header("Content-Disposition", "attachment", filename=f"{order_dict['id']}.pdf")
    msg.attach(att)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as srv:
        srv.starttls()
        srv.login(SMTP_USERNAME, SMTP_PASSWORD)
        srv.sendmail(FROM_EMAIL, to_email.strip(), msg.as_string())
