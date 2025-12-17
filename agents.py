from data import CUSTOMERS
from sanction import create_sanction_letter
from verification_agent import (
    verify_phone,
    mask_customer,
    persist_guest,
    get_guest,
    find_guest_by_phone,
    associate_guest_phone,
    mark_guest_approved,
)
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
from storage import add_customer
from llm import is_configured, generate_chat_reply


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

    # PHONE: verify customer exists, accept guest-id, or start guest flow
    if step == "PHONE":
        entry = message.strip()
        if entry.lower() == "guest":
            # start guest onboarding
            session["step"] = "GUEST_NAME"
            return ask_guest_name()

        # if user provided a guest id, load guest and ask to associate a phone
        if entry.startswith("guest-"):
            guest = get_guest(entry)
            if not guest:
                return "Guest id not found. Please re-enter a registered phone number or type 'guest' to create a new guest."
            session["guest_id"] = entry
            session["customer"] = guest
            session["step"] = "ASSOC_PHONE"
            return "Please enter your phone number to associate with this guest id."

        # treat entry as phone number
        phone = entry

        # check if phone is already associated with an approved guest
        other_id, other = find_guest_by_phone(phone)
        if other and other.get("approved"):
            return "This phone number has already been used for an approved loan. Please contact support if this is your number."

        # check registered customers
        customer = verify_phone(phone)
        if customer:
            session["phone"] = phone
            session["customer"] = customer
            session["step"] = "LOAN_AMOUNT"
            return ask_loan_amount(customer.get("name"))

        # if phone belongs to an unapproved guest, load that guest
        if other:
            session["phone"] = phone
            session["customer"] = other
            session["guest_id"] = other_id
            session["step"] = "LOAN_AMOUNT"
            return ask_loan_amount(other.get("name"))

        # unknown phone
        return "Customer not found. Please re-enter a registered phone number or type 'guest' to continue as guest."

    # ASSOC_PHONE: associate provided phone to an existing guest id
    if step == "ASSOC_PHONE":
        phone = message.strip()
        # ensure phone not already associated with an approved guest
        other_id, other = find_guest_by_phone(phone)
        if other and other.get("approved"):
            return "This phone number has already been used for an approved loan. Please provide a different phone number."

        gid = session.get("guest_id")
        if not gid:
            session["step"] = "PHONE"
            return "Guest id missing. Please enter your phone number or guest id."

        ok = associate_guest_phone(gid, phone)
        if not ok:
            return "Unable to associate phone with guest id (it may be used). Please enter a different phone."

        session["phone"] = phone
        # update in-memory customer too
        customer = session.get("customer", {})
        customer["associated_phone"] = phone
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
        # set defaults for guest preapproved limit based on salary so guests can get offers
        session.setdefault("customer", {})["credit_score"] = credit
        salary = session.setdefault("customer", {}).get("salary")
        if salary:
            # assign a demo pre-approved limit proportional to salary (e.g., 6x monthly salary)
            preapproved = int(salary * 6)
        else:
            preapproved = 0
        session.setdefault("customer", {})["preapproved_limit"] = preapproved

        # persist guest to guests.json and store guest id in session
        guest_profile = session.get("customer", {}).copy()
        guest_id = persist_guest(guest_profile)
        session["guest_id"] = guest_id

        session["step"] = "LOAN_AMOUNT"
        return (
            ask_loan_amount(session["customer"].get("name"))
            + f"\n\nNote: your details were saved as guest id {guest_id}. Your demo pre-approved limit is ₹{preapproved:,}."
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
            file_name = create_sanction_letter(
                customer.get("name"),
                session["loan_amount"],
                tenure,
                salary=customer.get("salary"),
                preapproved_limit=customer.get("preapproved_limit"),
                credit_score=customer.get("credit_score"),
                guest_id=session.get("guest_id"),
            )
            session["last_file"] = file_name
            # if guest, mark guest as approved and associate phone
            if session.get("guest_id"):
                try:
                    mark_guest_approved(session.get("guest_id"), session.get("phone"))
                except Exception:
                    pass
            # persist approved customer so phone cannot be reused and for future lookups
            try:
                if session.get("phone"):
                    add_customer(session.get("phone"), {
                        "name": customer.get("name"),
                        "salary": customer.get("salary"),
                        "preapproved_limit": customer.get("preapproved_limit"),
                        "credit_score": customer.get("credit_score"),
                    })
            except Exception:
                pass

            session["step"] = "POST"
            return (
                confirmation_message(customer.get("name"), session["loan_amount"], tenure)
                + "\n\nCongratulations! Your loan is approved and a sanction letter has been generated.\n\nIs there anything else I can help you with? (type 'restart' to apply again)"
            )

        session["step"] = "POST"
        # include brief reason in rejection message and keep reason in session for follow-up
        return f"Sorry, based on underwriting rules your loan cannot be approved at this time.\n\n{reason}\n\nIs there anything else I can help you with? (type 'restart' to apply again)"

    # POST: after a flow completes, a lightweight chat mode
    if step == "POST":
        text = (message or "").strip()
        if not text:
            return "Is there anything else I can help you with? Type 'restart' to start a new loan application."
        if text.lower() in ("restart", "new", "apply"):
            session.clear()
            session["step"] = "PHONE"
            return "Sure — let's start again. Please enter your phone number or type 'guest' to continue as guest."
        # If OpenAI is configured, prefer using it for a richer reply.
        if is_configured():
            try:
                reply = generate_chat_reply(text, {"last_reason": session.get("last_reason"), "last_details": session.get("last_details")})
                if reply:
                    return reply
            except Exception:
                pass

        # Basic helpful responses (demo fallback)
        low = text.lower()
        if "interest" in low or "emi" in low:
            details = session.get("last_details") or {}
            emi = details.get("emi")
            if emi:
                return f"Your estimated EMI was ₹{int(emi):,} per month. I can show a payment schedule if you want."
            return "EMI depends on principal, tenure and interest rate. Provide those and I can estimate."
        if "help" in low or "support" in low:
            return "I can help with loan applications, explain decisions, or generate sanction letters. Type 'restart' to start a new loan application."
        # fallback echo-like response
        return f"You asked: '{message}'. I can help with loan applications — type 'restart' to begin a new one."

    return "Thank you."
