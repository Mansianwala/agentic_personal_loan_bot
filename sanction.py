from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_sanction_letter(name, amount, tenure):
    file_name = "sanction_letter.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)

    c.setFont("Helvetica", 12)
    c.drawString(100, 800, "PERSONAL LOAN SANCTION LETTER")
    c.drawString(100, 760, f"Customer Name: {name}")
    c.drawString(100, 730, f"Loan Amount: ₹{amount}")
    c.drawString(100, 700, f"Tenure: {tenure} months")
    c.drawString(100, 670, "Status: APPROVED")

    c.save()
    return file_name
