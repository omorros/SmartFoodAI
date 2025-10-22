from db_manager import init_db, add_item, list_items, DB_PATH
import datetime as dt
from utils import shelf_life_days, estimated_expiry, days_left


def menu():
    print("\nSmartFood AI (console)")
    print("[1] Add item manually")
    print("[2] List items")
    print("[3] List items by urgency") 
    print("[0] Exit")


def cmd_add_item():
    name = input("Name: ").strip()
    qty = float(input("Qty (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip()
    category = input("Category (e.g., Fruit, Dairy): ").strip()
    location = (input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip() or "Fridge").title()
    purchased = input("Purchased on (YYYY-MM-DD) [today]: ").strip() or dt.date.today().isoformat()
    expiry = input("Expiry on (YYYY-MM-DD) [blank to auto]: ").strip() or None

    if not expiry:
        days = shelf_life_days(name, location)
        if days is not None:
            guess = estimated_expiry(purchased, days)
            yn = input(f"Auto-fill expiry using shelf life ({days} days) → {guess}? [Y/n] ").strip().lower()
            if yn in ("", "y", "yes"):
                expiry = guess
        else:
            print("No shelf-life rule found for this item. Saving without expiry.")

    try:
        iid = add_item(name, category, qty, unit, location, purchased, expiry, source="manual", notes=None)
        print(f"✔ Saved (id {iid}).")
    except Exception as e:
        print("Error saving item:", e)




def cmd_list_items():
    rows = list_items()
    print("\nID | Item           | Qty | Unit | Category | Loc    | Purchased   | Expiry")
    print("-"*90)
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        print(f"{iid:<3}| {name[:14]:<14}| {qty:<4}| {unit:<4}| {cat or '-':<9}| {loc[:6]:<6}| {pur or '-':<11}| {exp or '-'}")

def cmd_list_by_urgency():
    rows = list_items()
    annotated = []
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        annotated.append((dleft, iid, name, qty, unit, cat, loc, pur, exp))
    # Sort: items with a known date first (lowest days_left), then those without a date
    annotated.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 99999))

    print("\nID | Days | Item           | Qty | Unit | Category | Loc    | Expiry")
    print("-"*90)
    for (dleft, iid, name, qty, unit, cat, loc, pur, exp) in annotated:
        dtxt = "-" if dleft is None else str(dleft)
        print(f"{iid:<3}| {dtxt:>4} | {name[:14]:<14}| {qty:<4}| {unit:<4}| {cat or '-':<9}| {loc[:6]:<6}| {exp or '-'}")

def main():
    init_db()
    print(f"Using database: {DB_PATH}")
    while True:
        menu()
        choice = input("Choose: ").strip()
        if choice == "1": cmd_add_item()
        elif choice == "2": cmd_list_items()
        elif choice == "3": cmd_list_by_urgency()
        elif choice == "0": break
        else: print("Invalid option.")


if __name__ == "__main__":
    main()
