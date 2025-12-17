from data import CUSTOMERS
from storage import get_customer, add_customer

def verify_phone(phone):
    """Return customer dict if phone exists, else None."""
    # check built-in customers first
    c = CUSTOMERS.get(phone)
    if c:
        return c
    # then check persisted customers
    pc = get_customer(phone)
    if pc:
        return pc
    return None


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

    # create an id and set defaults
    guest_id = f"guest-{int(datetime.utcnow().timestamp())}"
    guest_record = {
        "name": guest.get("name"),
        "salary": guest.get("salary"),
        "credit_score": guest.get("credit_score"),
        "preapproved_limit": guest.get("preapproved_limit", 0),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "approved": False,
        "associated_phone": None,
    }
    guests[guest_id] = guest_record

    # write back
    try:
        with open(guests_file, "w", encoding="utf-8") as f:
            json.dump(guests, f, indent=2, ensure_ascii=False)
    except Exception:
        # best-effort persistence, ignore on failure
        pass

    return guest_id


def _guests_file_path():
    import os

    return os.path.join(os.path.dirname(__file__), "guests.json")


def load_guests():
    import json, os

    guests_file = _guests_file_path()
    try:
        if os.path.exists(guests_file):
            with open(guests_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_guests(guests: dict):
    import json
    with open(_guests_file_path(), "w", encoding="utf-8") as f:
        json.dump(guests, f, indent=2, ensure_ascii=False)


def get_guest(guest_id: str):
    guests = load_guests()
    return guests.get(guest_id)


def find_guest_by_phone(phone: str):
    guests = load_guests()
    for gid, record in guests.items():
        if record.get("associated_phone") == phone:
            return gid, record
    return None, None


def associate_guest_phone(guest_id: str, phone: str):
    guests = load_guests()
    rec = guests.get(guest_id)
    if not rec:
        return False
    # ensure no other guest has this phone
    other_id, _ = find_guest_by_phone(phone)
    if other_id and other_id != guest_id:
        return False
    rec["associated_phone"] = phone
    guests[guest_id] = rec
    try:
        save_guests(guests)
    except Exception:
        pass
    return True


def mark_guest_approved(guest_id: str, phone: str = None):
    guests = load_guests()
    rec = guests.get(guest_id)
    if not rec:
        return False
    rec["approved"] = True
    if phone:
        rec["associated_phone"] = phone
    guests[guest_id] = rec
    try:
        save_guests(guests)
    except Exception:
        pass
    return True
