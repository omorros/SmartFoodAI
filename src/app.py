from db_manager import init_db, add_item, list_items
import datetime as dt

def menu():
    print("\nSmartFood AI (console)")
    print("[1] Add item manually")
    print("[2] List items")
    print("[0] Exit")

def cmd_add_item():
    name = input("Name: ").strip()
    qty = float(input("Qty (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip()
    category = input("Category (e.g., Fruit, Dairy): ").strip()
    location = (input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip() or "Fridge").title()
    purchased = input("Purchased on (YYYY-MM-DD) [today]: ").strip() or dt.date.today().isoformat()
    expiry = input("Expiry on (YYYY-MM-DD) [blank if unknown]: ").strip() or None
    add_item(name, category, qty, unit, location, purchased, expiry, source="manual", notes=None)
    print("Saved.")

def cmd_list_items():
    rows = list_items()
    print("\nID | Item           | Qty | Unit | Category | Loc    | Purchased   | Expiry")
    print("-"*90)
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        print(f"{iid:<3}| {name[:14]:<14}| {qty:<4}| {unit:<4}| {cat or '-':<9}| {loc[:6]:<6}| {pur or '-':<11}| {exp or '-'}")

def main():
    init_db()
    while True:
        menu()
        choice = input("Choose: ").strip()
        if choice == "1": cmd_add_item()
        elif choice == "2": cmd_list_items()
        elif choice == "0": break
        else: print("Invalid option.")

if __name__ == "__main__":
    main()
