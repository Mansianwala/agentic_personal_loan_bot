def evaluate_loan(credit_score, loan_amount, preapproved_limit, salary):
    """Evaluate loan eligibility and return (decision, reason, details).

    - decision: 'APPROVED' or 'REJECTED'
    - reason: short human-readable explanation.
    - details: dict with numeric breakdown for explanations (EMI, salary, limits).
    """
    details = {
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "preapproved_limit": preapproved_limit,
        "salary": salary,
        "max_allowed": 2 * preapproved_limit if preapproved_limit else 0,
    }

    # Check credit score
    if credit_score < 700:
        reason = f"Credit score {credit_score} is below the required minimum of 700."
        return "REJECTED", reason, details

    # Within preapproved limit
    if loan_amount <= preapproved_limit:
        reason = f"Requested amount ₹{loan_amount:,} is within pre-approved limit of ₹{preapproved_limit:,}."
        details.update({"emi": loan_amount / 12})
        return "APPROVED", reason, details

    # Up to 2x preapproved limit, check EMI affordability
    if loan_amount <= 2 * preapproved_limit:
        emi = loan_amount / 12  # simple monthly EMI estimate without interest for demo
        details["emi"] = emi
        if salary:
            affordable = emi <= 0.5 * salary
        else:
            affordable = False

        if affordable:
            reason = f"Estimated monthly EMI ₹{emi:,.0f} is <= 50% of monthly salary ₹{salary:,}; affordable."
            return "APPROVED", reason, details
        else:
            reason = f"Estimated monthly EMI ₹{emi:,.0f} exceeds 50% of monthly salary ₹{salary:,}; unaffordable."
            return "REJECTED", reason, details

    # Anything beyond 2x preapproved limit is rejected
    reason = (
        f"Requested amount ₹{loan_amount:,} exceeds the allowable maximum (2x pre-approved limit ₹{2*preapproved_limit:,})."
    )
    details["emi"] = loan_amount / 12
    return "REJECTED", reason, details
