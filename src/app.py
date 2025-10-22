from db_manager import init_db, add_item, list_items, DB_PATH, get_item, update_item, delete_item, consume_item
import datetime as dt
from utils import shelf_life_days, estimated_expiry, days_left, parse_date_input

# ANSI color helpers (works in most terminals; colorama is optional on Windows)
try:
    import colorama
    colorama.init()
except Exception:
    colorama = None

import re

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    """Return string without ANSI sequences."""
    return ANSI_RE.sub("", s)

def pad_visible(s: str, width: int, align: str = "left") -> str:
    """
    Pad a string to 'width' based on its visible length (ignores ANSI codes).
    If the visible content is longer than width, it's truncated (ANSI removed).
    """
    visible = strip_ansi(s)
    if len(visible) > width:
        # When too long, return truncated visible text (drop colors to avoid broken escapes)
        return visible[:width]
    pad = width - len(visible)
    if align == "right":
        return (" " * pad) + s
    return s + (" " * pad)

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
    print("[6] Consume item")  # New option
    print("[0] Exit")


def cmd_add_item():
    name = input("Name: ").strip()
    qty = float(input("Qty (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip()
    category = input("Category (e.g., Fruit, Dairy): ").strip()
    location = (input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip() or "Fridge").title()
    purchased_raw = input("Purchased on (YYYY-MM-DD or '3' = 3 days ago) [today]: ").strip()
    purchased = parse_date_input(purchased_raw) or dt.date.today().isoformat()
    expiry = input("Expiry on (YYYY-MM-DD) [blank to auto]: ").strip() or None

    if not expiry:
        days = shelf_life_days(name, location)
        if days is not None:
            guess = estimated_expiry(purchased, days)
            # Auto-fill expiry without asking confirmation when left blank
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
    # Column widths
    W_ID = 2
    W_DAYS = 9
    W_NAME = 15
    W_QTY = 6
    W_UNIT = 4
    W_CAT = 12
    W_LOC = 7
    W_PUR = 10
    W_EXP = 10

    # Header
    print("\n" + f"{'ID':>{W_ID}} | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Category':<{W_CAT}} | {'Loc':<{W_LOC}} | {'Purchased':<{W_PUR}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_CAT + W_LOC + W_PUR + W_EXP + 24))
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        dtxt = _color_days(dleft)
        dtxt_f = pad_visible(dtxt, W_DAYS, align="left")
        print(f"{iid:>{W_ID}d} | {dtxt_f} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {(cat or '-').title():<{W_CAT}} | {loc:<{W_LOC}} | {pur or '-':<{W_PUR}} | {exp or '-':<{W_EXP}}")

def cmd_list_by_urgency():
    rows = list_items()
    annotated = []
    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        annotated.append((dleft, iid, name, qty, unit, cat, loc, pur, exp))
    annotated.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 99999))

    # Column widths (match list view)
    W_ID = 2
    W_DAYS = 9
    W_NAME = 15
    W_QTY = 6
    W_UNIT = 4
    W_CAT = 12
    W_LOC = 7
    W_EXP = 10

    print("\n" + f"{'ID':>{W_ID}} | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Category':<{W_CAT}} | {'Loc':<{W_LOC}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_CAT + W_LOC + W_EXP + 20))
    for (dleft, iid, name, qty, unit, cat, loc, pur, exp) in annotated:
        dtxt = _color_days(dleft)
        dtxt_f = pad_visible(dtxt, W_DAYS, align="left")
        print(f"{iid:>{W_ID}d} | {dtxt_f} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {(cat or '-').title():<{W_CAT}} | {loc:<{W_LOC}} | {exp or '-':<{W_EXP}}")

def _show_items_brief():
    """Show a compact list to help the user pick an ID."""
    rows = list_items()
    if not rows:
        print("\nNo items in database.\n")
        return

    # Calculate max widths but cap them for a neat display
    max_name = max((len(name) for _,name,*_ in rows), default=4)
    max_name = max(10, min(max_name, 20))  # between 10 and 20 chars

    # Column widths
    W_ID = 2
    W_DAYS = 9
    W_NAME = max_name
    W_QTY = 6
    W_UNIT = 4
    W_EXP = 10

    # Header
    print("\n" + f"{'ID':>{W_ID}}  | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_EXP + 18))

    for (iid,name,qty,unit,cat,loc,pur,exp) in rows:
        dleft = days_left(exp)
        dtxt = _color_days(dleft)
        dtxt_f = pad_visible(dtxt, W_DAYS, align="left")
        print(f"{iid:>{W_ID}}  | {dtxt_f} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {exp or '-':<{W_EXP}}")
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
    n_purchased_raw = input(f"Purchased on [{purchased or dt.date.today().isoformat()}]: ").strip()
    if n_purchased_raw == "":
        n_purchased = purchased
    else:
        parsed = parse_date_input(n_purchased_raw)
        if parsed is None:
            print("Couldn't parse date, keeping existing.")
            n_purchased = purchased
        else:
            n_purchased = parsed
    n_expiry = input(f"Expiry on [{expiry or ''}] (blank to auto/use existing): ").strip()
    if n_expiry == "":
        # decide: keep existing expiry (if any) or auto-fill if none — no confirmation
        if not expiry:
            days = shelf_life_days(n_name, n_loc)
            if days is not None:
                guess = estimated_expiry(n_purchased or dt.date.today().isoformat(), days)
                # Auto-fill expiry without asking confirmation when left blank
                n_expiry = guess
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

def cmd_consume_item():
    _show_items_brief()
    s = input("Enter item ID to consume (or Enter to cancel): ").strip()
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
    
    # Show current details
    _, name, _, qty, unit, _, _, _, _, _ = row
    print(f"\nCurrent: {name} - {qty} {unit}")
    
    # Get amount to consume
    try:
        amount = float(input(f"Amount to consume [all={qty}]: ").strip() or qty)
    except ValueError:
        print("Invalid amount.")
        return
    
    # Consume
    ok, new_qty = consume_item(iid, amount)
    if not ok:
        print("Error updating item.")
        return
    
    print(f"✔ Updated: {new_qty} {unit} remaining")
    
    # If empty, offer to delete
    if new_qty <= 0:
        yn = input("Item is empty. Delete it? [y/N] ").strip().lower()
        if yn in ("y", "yes"):
            if delete_item(iid):
                print("✔ Item deleted.")
            else:
                print("Error deleting item.")

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
        elif choice == "6": cmd_consume_item()  # New handler
        elif choice == "0": break
        else: print("Invalid option.")


if __name__ == "__main__":
    main()
