"""Simple JSON-backed storage for persisted customers."""
import json
import os


def _customers_path():
    return os.path.join(os.path.dirname(__file__), "customers.json")


def load_customers():
    path = _customers_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_customers(customers: dict):
    path = _customers_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(customers, f, indent=2, ensure_ascii=False)


def add_customer(phone: str, record: dict):
    customers = load_customers()
    customers[phone] = record
    save_customers(customers)
    return True


def get_customer(phone: str):
    customers = load_customers()
    return customers.get(phone)
