from rules import evaluate_loan


def assess(credit_score, loan_amount, preapproved_limit, salary):
    """Run underwriting rules and return (decision, reason, details)."""
    return evaluate_loan(credit_score, loan_amount, preapproved_limit, salary)
