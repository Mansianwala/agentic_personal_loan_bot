from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from datetime import datetime
import math


def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _calc_emi(principal, months, annual_rate):
    # EMI formula: E = P * r * (1+r)^n / ((1+r)^n - 1)
    if months <= 0:
        return 0
    r = annual_rate / 12.0 / 100.0
    if r == 0:
        return principal / months
    numerator = principal * r * (1 + r) ** months
    denominator = (1 + r) ** months - 1
    emi = numerator / denominator
    return emi


def create_sanction_letter(name, amount, tenure, salary=None, preapproved_limit=None, credit_score=None, guest_id=None, annual_rate=12.0):
    """Generate a detailed sanction letter PDF in `generated/` and return its relative path.

    The function is backward-compatible when only (name, amount, tenure) are provided.
    """
    gen_dir = os.path.join(os.path.dirname(__file__), "generated")
    _ensure_dir(gen_dir)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    file_name = f"sanction_{ts}.pdf"
    file_path = os.path.join(gen_dir, file_name)

    emi = _calc_emi(amount, tenure, annual_rate)
    total_payable = emi * tenure
    sanction_no = f"SAN-{int(datetime.utcnow().timestamp())}-{abs(hash(name))%1000}"

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, height - 60, "PERSONAL LOAN SANCTION LETTER")

    c.setFont("Helvetica", 11)
    y = height - 100
    lines = [
        f"Sanction No: {sanction_no}",
        f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}",
        "",
        f"Customer Name: {name}",
        f"Guest ID: {guest_id or 'N/A'}",
        f"Credit Score: {credit_score or 'N/A'}",
        f"Monthly Salary: ₹{salary:,}" if salary else "Monthly Salary: N/A",
        f"Pre-approved Limit: ₹{preapproved_limit:,}" if preapproved_limit else "Pre-approved Limit: N/A",
        "",
        f"Requested Loan Amount: ₹{amount:,}",
        f"Tenure: {tenure} months",
        f"Annual Interest Rate (assumed): {annual_rate}%",
        f"Estimated EMI (monthly): ₹{emi:,.2f}",
        f"Total Payable (approx.): ₹{total_payable:,.2f}",
        "",
        "Status: APPROVED",
        "",
        "Notes:",
        "This sanction letter is a system-generated document for demonstration purposes.",
    ]

    for line in lines:
        c.drawString(60, y, line)
        y -= 18
        if y < 60:
            c.showPage()
            y = height - 60

    c.save()
    # return path relative to app root so frontend can request '/generated/<file>'
    rel_path = os.path.join('generated', file_name).replace('\\', '/')
    return rel_path
