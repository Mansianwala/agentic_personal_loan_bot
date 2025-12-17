from data import CUSTOMERS

def verify_phone(phone):
    """Return customer dict if phone exists, else None."""
    return CUSTOMERS.get(phone)


def mask_customer(customer: dict):
    """Return a masked copy of customer details for display/logging."""
    if not customer:
        return None
    masked = customer.copy()
    # No PI in the stored customer except name; if phone were passed store separately
    return masked


def persist_guest(guest: dict):
    """Append a guest profile to `guests.json` and return an assigned guest_id.

    Guest dict should include at least `name`, `salary`, `credit_score`.
    """
    import json
    import os
    from datetime import datetime

    guests_file = os.path.join(os.path.dirname(__file__), "guests.json")

    # Load existing guests
    try:
        if os.path.exists(guests_file):
            with open(guests_file, "r", encoding="utf-8") as f:
                guests = json.load(f)
        else:
            guests = {}
    except Exception:
        guests = {}

    # create an id
    guest_id = f"guest-{int(datetime.utcnow().timestamp())}"
    guests[guest_id] = guest

    # write back
    try:
        with open(guests_file, "w", encoding="utf-8") as f:
            json.dump(guests, f, indent=2, ensure_ascii=False)
    except Exception:
        # best-effort persistence, ignore on failure
        pass

    return guest_id
