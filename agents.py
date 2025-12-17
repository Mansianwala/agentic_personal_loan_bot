from data import CUSTOMERS
from sanction import create_sanction_letter
from verification_agent import verify_phone, mask_customer
from verification_agent import persist_guest
from sales_agent import (
    greet_start,
    ask_loan_amount,
    ask_tenure,
    confirmation_message,
    ask_guest_name,
    ask_guest_salary,
    ask_guest_credit_score,
)
from underwriting_agent import assess


def master_agent(message, session):
    """Master orchestrator that delegates to worker agents.

    session is a dict holding conversation state. Steps:
      START -> PHONE -> LOAN_AMOUNT -> TENURE -> UNDERWRITE -> END
    """
    step = session.get("step", "START")

    # If user asks for an explanation (why), return last stored reason when available
    if message and message.strip().lower() in ("why", "why?", "explain", "reason", "what happened"):
        if session.get("last_reason"):
            return f"Reason: {session.get('last_reason')}"
        return "Could you clarify which part you'd like explained?"

    # START: greet and ask for phone
    if step == "START":
        session["step"] = "PHONE"
        return greet_start()

    # PHONE: verify customer exists or start guest flow
    if step == "PHONE":
        phone = message.strip()
        if phone.lower() == "guest":
            # start guest onboarding
            session["step"] = "GUEST_NAME"
            return ask_guest_name()

        customer = verify_phone(phone)
        if not customer:
            # keep the conversation alive and ask to re-enter
            return "Customer not found. Please re-enter a registered phone number or type 'guest' to continue as guest."

        session["phone"] = phone
        session["customer"] = customer
        session["step"] = "LOAN_AMOUNT"
        return ask_loan_amount(customer.get("name"))

    # GUEST_NAME: collect name
    if step == "GUEST_NAME":
        name = message.strip()
        if not name:
            return ask_guest_name()
        session.setdefault("customer", {})["name"] = name
        session["step"] = "GUEST_SALARY"
        return ask_guest_salary()

    # GUEST_SALARY: collect salary
    if step == "GUEST_SALARY":
        try:
            salary = int(message.replace(",", ""))
        except Exception:
            return "Please enter your monthly salary as a number, e.g. 40000"
        session.setdefault("customer", {})["salary"] = salary
        session["step"] = "GUEST_CREDIT_SCORE"
        return ask_guest_credit_score()

    # GUEST_CREDIT_SCORE: collect credit score and continue
    if step == "GUEST_CREDIT_SCORE":
        try:
            credit = int(message)
        except Exception:
            return "Please enter an approximate numeric credit score, e.g. 650"
        # set defaults for guest preapproved limit
        session.setdefault("customer", {})["credit_score"] = credit
        session.setdefault("customer", {})["preapproved_limit"] = 0

        # persist guest to guests.json and store guest id in session
        guest_profile = session.get("customer", {}).copy()
        guest_id = persist_guest(guest_profile)
        session["guest_id"] = guest_id

        session["step"] = "LOAN_AMOUNT"
        return (
            ask_loan_amount(session["customer"].get("name"))
            + f"\n\nNote: your details were saved as guest id {guest_id}."
        )

    # LOAN_AMOUNT: capture loan amount
    if step == "LOAN_AMOUNT":
        try:
            amount = int(message.replace(",", ""))
        except Exception:
            return "Please enter the loan amount as a number, e.g. 300000"

        session["loan_amount"] = amount
        session["step"] = "TENURE"
        return ask_tenure()

    # TENURE: capture tenure and run underwriting
    if step == "TENURE":
        try:
            tenure = int(message)
        except Exception:
            return "Please enter loan tenure in months as a number, e.g. 24"

        session["tenure"] = tenure

        # Prepare underwriting inputs
        customer = session.get("customer")
        if not customer:
            session["step"] = "END"
            return "Customer data missing. Cannot proceed."

        # assess returns (decision, reason, details)
        decision, reason, details = assess(
            customer.get("credit_score", 0),
            session.get("loan_amount", 0),
            customer.get("preapproved_limit", 0),
            customer.get("salary", 0),
        )

        # store last decision, reason and details for later explanation
        session["last_decision"] = decision
        session["last_reason"] = reason
        session["last_details"] = details

        if decision == "APPROVED":
            # generate sanction letter and store filename in session
            file_name = create_sanction_letter(customer.get("name"), session["loan_amount"], tenure)
            session["last_file"] = file_name
            session["step"] = "END"
            return (
                confirmation_message(customer.get("name"), session["loan_amount"], tenure)
                + "\n\nCongratulations! Your loan is approved and a sanction letter has been generated."
            )

        session["step"] = "END"
        # include brief reason in rejection message and keep reason in session for follow-up
        return f"Sorry, based on underwriting rules your loan cannot be approved at this time.\n\n{reason}"

    return "Thank you."
