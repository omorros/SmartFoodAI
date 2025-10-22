from db_manager import init_db, add_item, list_items, DB_PATH, get_item, update_item, delete_item
import datetime as dt
from utils import shelf_life_days, estimated_expiry, days_left

# ANSI color helpers (works in most terminals; colorama is optional on Windows)
try:
    import colorama
    colorama.init()
except Exception:
    colorama = None

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"

def _color_days(d):
    """Return a colored string for days-left (d can be int or None)."""
    if d is None:
        return f"{DIM}- {RESET}"
    if d < 0:
        return f"{RED}EXPIRED{RESET}"
    if d == 0:
        return f"{RED}0{RESET}"
    if d <= 3:
        return f"{YELLOW}{d}{RESET}"
    return f"{GREEN}{d}{RESET}"


def menu():
    print("\nSmartFood AI (console)")
    print("[1] Add item")
    print("[2] View all items")
    print("[3] View items by urgency")
    print("[4] Edit item")
    print("[5] Delete item")
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
    print("\nID | Days      | Item           | Qty | Unit | Category | Loc    | Purchased   | Expiry")
    print("-"*100)
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        dtxt = _color_days(dleft)
        # colored dtxt may affect alignment in some terminals
        print(f"{iid:<3}| {dtxt:>9} | {name[:14]:<14}| {qty:<4}| {unit:<4}| {cat or '-':<9}| {loc[:6]:<6}| {pur or '-':<11}| {exp or '-'}")

def cmd_list_by_urgency():
    rows = list_items()
    annotated = []
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        annotated.append((dleft, iid, name, qty, unit, cat, loc, pur, exp))
    # Sort: items with a known date first (lowest days_left), then those without a date
    annotated.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 99999))

    print("\nID | Days      | Item           | Qty | Unit | Category | Loc    | Expiry")
    print("-"*100)
    for (dleft, iid, name, qty, unit, cat, loc, pur, exp) in annotated:
        dtxt = _color_days(dleft)
        # note: colored strings include ANSI codes which don't count toward visible width,
        # alignment may be approximate in some terminals.
        print(f"{iid:<3}| {dtxt:>9} | {name[:14]:<14}| {qty:<4}| {unit:<4}| {cat or '-':<9}| {loc[:6]:<6}| {exp or '-'}")

def _show_items_brief():
    """Show a compact list to help the user pick an ID."""
    rows = list_items()
    if not rows:
        print("\nNo items in database.\n")
        return
    print("\nID | Days      | Item                 | Expiry")
    print("-"*70)
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        dtxt = _color_days(dleft)
        print(f"{iid:<3}| {dtxt:>9} | {name[:20]:<20}| {exp or '-'}")
    print()

def cmd_edit_item():
    _show_items_brief()
    s = input("Enter item ID to edit (or Enter to cancel): ").strip()
    if s == "" or s.lower() == "q":
        print("Cancelled.")
        return
    try:
        iid = int(s)
    except ValueError:
        print("Invalid id.")
        return
    row = get_item(iid)
    if not row:
        print("Item not found.")
        return
    # row: id,name,category,qty,unit,location,purchased_on,expiry_on,source,notes
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print("Leave blank to keep current value.")
    n_name = input(f"Name [{name}]: ").strip() or name
    n_qty = input(f"Qty [{qty}]: ").strip()
    try:
        n_qty = float(n_qty) if n_qty else qty
    except ValueError:
        print("Invalid quantity, keeping existing.")
        n_qty = qty
    n_unit = input(f"Unit [{unit}]: ").strip() or unit
    n_cat = input(f"Category [{category or ''}]: ").strip() or category
    n_loc = (input(f"Location [{location}]: ").strip() or location).title()
    n_purchased = input(f"Purchased on [{purchased or dt.date.today().isoformat()}]: ").strip() or purchased
    n_expiry = input(f"Expiry on [{expiry or ''}] (blank to auto/use existing): ").strip()
    if n_expiry == "":
        # decide: keep existing expiry (if any) or try auto-fill if none
        if not expiry:
            days = shelf_life_days(n_name, n_loc)
            if days is not None:
                guess = estimated_expiry(n_purchased or dt.date.today().isoformat(), days)
                yn = input(f"Auto-fill expiry using shelf life ({days} days) → {guess}? [Y/n] ").strip().lower()
                if yn in ("", "y", "yes"):
                    n_expiry = guess
                else:
                    n_expiry = None
            else:
                n_expiry = None
        else:
            n_expiry = expiry
    # source/notes - keep existing unless provided
    n_source = input(f"Source [{source or ''}]: ").strip() or source
    n_notes = input(f"Notes [{notes or ''}]: ").strip() or notes

    try:
        update_item(iid, n_name, n_cat, n_qty, n_unit, n_loc, n_purchased, n_expiry, n_source, n_notes)
        print("✔ Item updated.")
    except Exception as e:
        print("Error updating item:", e)

def cmd_delete_item():
    _show_items_brief()
    s = input("Enter item ID to delete (or Enter to cancel): ").strip()
    if s == "" or s.lower() == "q":
        print("Cancelled.")
        return
    try:
        iid = int(s)
    except ValueError:
        print("Invalid id.")
        return
    row = get_item(iid)
    if not row:
        print("Item not found.")
        return
    # show details before confirming
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print(f"\nSelected: {iid} - {name} | {qty} {unit} | {category or '-'} | {location} | purchased: {purchased or '-'} | expiry: {expiry or '-'}")
    yn = input("Delete this item? [y/N] ").strip().lower()
    if yn not in ("y", "yes"):
        print("Cancelled.")
        return
    try:
        ok = delete_item(iid)
        if ok:
            print("✔ Item deleted.")
        else:
            print("Item not deleted (maybe already gone).")
    except Exception as e:
        print("Error deleting item:", e)

def main():
    init_db()
    print(f"Using database: {DB_PATH}")
    while True:
        menu()
        choice = input("Choose: ").strip()
        if choice == "1": cmd_add_item()
        elif choice == "2": cmd_list_items()
        elif choice == "3": cmd_list_by_urgency()
        elif choice == "4": cmd_edit_item()
        elif choice == "5": cmd_delete_item()
        elif choice == "0": break
        else: print("Invalid option.")


if __name__ == "__main__":
    main()
a