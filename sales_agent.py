def greet_start():
    return "Welcome to Tata Capital! I'm your AI loan assistant. Please enter your phone number to get started." 


def ask_loan_amount(name=None):
    if name:
        return f"Hello {name}, how much loan do you need? (enter amount in numbers, e.g. 300000)"
    return "How much loan do you need? (enter amount in numbers, e.g. 300000)"


def ask_tenure():
    return "Please enter desired loan tenure in months (e.g. 12, 24, 36)."


def confirmation_message(customer_name, amount, tenure):
    return f"Thank you {customer_name}. You requested ₹{amount} for {tenure} months. Proceeding to underwriting and verification..."


def ask_guest_name():
    return "Welcome, guest! Please tell me your full name."


def ask_guest_salary():
    return "Please enter your monthly salary in numbers (e.g. 40000)."


def ask_guest_credit_score():
    return "Please enter your approximate credit score (e.g. 650)."
