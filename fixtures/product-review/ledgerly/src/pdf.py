from io import BytesIO
from reportlab.pdfgen import canvas


def render_invoice_pdf(inv):
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 760, f"Invoice #{inv['id']}")
    c.drawString(72, 740, f"Bill to: {inv['client']['name']} <{inv['client']['email']}>")
    c.drawString(72, 720, f"Issued: {inv['issued']}")
    c.drawString(72, 700, f"Total: {inv['total']:.2f}")
    c.drawString(72, 680, f"Status: {inv['status']}")
    c.showPage()
    c.save()
    return buf.getvalue()
