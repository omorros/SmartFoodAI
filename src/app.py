from db_manager import (
    init_db, add_item, list_items, DB_PATH,
    get_item, update_item, delete_item, consume_item
)
import datetime as dt
from utils import shelf_life_days, estimated_expiry, days_left, parse_date_input
import re
import os
import requests
import pyzxing

# ---------- Helper Functions ----------

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def pad_visible(s: str, width: int, align: str = "left") -> str:
    visible = strip_ansi(s)
    if len(visible) > width:
        return visible[:width]
    pad = width - len(visible)
    if align == "right":
        return (" " * pad) + s
    return s + (" " * pad)

def _color_days(d):
    if d is None:
        return "-"
    if d < 0:
        return "EXPIRED"
    if d == 0:
        return "0"
    if d <= 3:
        return str(d)
    return str(d)

# ---------- Barcode + API Integration ----------

def scan_barcode_local(image_path: str):
    reader = pyzxing.BarCodeReader()
    results = reader.decode(image_path)

    if not results:
        print("No barcode detected.")
        return None

    data = results[0].get("raw", None)
    print(f"Detected barcode: {data}")
    return data

def lookup_product_by_barcode(barcode: str):
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        jd = r.json()
    except Exception as e:
        print("API request failed:", e)
        return None

    if jd.get("status") != 1:
        return None

    p = jd.get("product", {})
    return {
        "barcode": barcode,
        "product_name": p.get("product_name", "").strip(),
        "brands": p.get("brands", "").strip(),
        "categories": p.get("categories", "").strip()
    }

def scan_and_add_product(image_path: str):
    barcode = scan_barcode_local(image_path)
    if not barcode:
        return

    product_info = lookup_product_by_barcode(barcode)

    if product_info:
        print(f"Product found: {product_info['product_name']} | Brand: {product_info['brands']} | Category: {product_info['categories']}")
        name = product_info["product_name"] or input("Enter product name: ").strip()
        category = product_info["categories"].split(",")[0] if product_info["categories"] else input("Enter category: ").strip()
    else:
        print("Product not found in OpenFoodFacts.")
        name = input("Enter product name manually: ").strip()
        category = input("Enter category: ").strip()

    qty = float(input("Quantity (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip() or "pcs"
    location = input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip().title() or "Fridge"
    purchased = dt.date.today().isoformat()
    expiry = input("Expiry date (YYYY-MM-DD) [optional]: ").strip() or None

    try:
        iid = add_item(name, category, qty, unit, location, purchased, expiry, source="barcode", notes=f"barcode:{barcode}")
        print(f"Saved item ID {iid}: {name} ({barcode})")
    except Exception as e:
        print("Error saving item:", e)

# ---------- Existing Commands ----------

def menu():
    print("\nSmartFood AI (console)")
    print("[1] Add item manually")
    print("[2] View all items")
    print("[3] View items by urgency")
    print("[4] Edit item")
    print("[5] Delete item")
    print("[6] Consume item")
    print("[7] Recognize item from image")
    print("[8] Add item via barcode scan")
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
            expiry = guess
        else:
            print("No shelf-life rule found for this item. Saving without expiry.")

    try:
        iid = add_item(name, category, qty, unit, location, purchased, expiry, source="manual", notes=None)
        print(f"Saved (id {iid}).")
    except Exception as e:
        print("Error saving item:", e)

def cmd_list_items():
    rows = list_items()
    W_ID, W_DAYS, W_NAME, W_QTY, W_UNIT, W_CAT, W_LOC, W_PUR, W_EXP = 2, 9, 15, 6, 4, 12, 7, 10, 10
    print("\n" + f"{'ID':>{W_ID}} | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Category':<{W_CAT}} | {'Loc':<{W_LOC}} | {'Purchased':<{W_PUR}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_CAT + W_LOC + W_PUR + W_EXP + 24))
    for (iid, name, qty, unit, cat, loc, pur, exp) in rows:
        dleft = days_left(exp)
        dtxt_f = pad_visible(_color_days(dleft), W_DAYS, align="left")
        print(f"{iid:>{W_ID}d} | {dtxt_f} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {(cat or '-').title():<{W_CAT}} | {loc:<{W_LOC}} | {pur or '-':<{W_PUR}} | {exp or '-':<{W_EXP}}")

def cmd_list_by_urgency():
    rows = list_items()
    annotated = []
    for (iid, name, qty, unit, cat, loc, pur, exp) in rows:
        dleft = days_left(exp)
        annotated.append((dleft, iid, name, qty, unit, cat, loc, pur, exp))
    annotated.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 99999))

    W_ID, W_DAYS, W_NAME, W_QTY, W_UNIT, W_CAT, W_LOC, W_EXP = 2, 9, 15, 6, 4, 12, 7, 10
    print("\n" + f"{'ID':>{W_ID}} | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Category':<{W_CAT}} | {'Loc':<{W_LOC}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_CAT + W_LOC + W_EXP + 20))
    for (dleft, iid, name, qty, unit, cat, loc, pur, exp) in annotated:
        dtxt_f = pad_visible(_color_days(dleft), W_DAYS, align="left")
        print(f"{iid:>{W_ID}d} | {dtxt_f} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {(cat or '-').title():<{W_CAT}} | {loc:<{W_LOC}} | {exp or '-':<{W_EXP}}")

def _show_items_brief():
    rows = list_items()
    if not rows:
        print("\nNo items in database.\n")
        return
    max_name = max((len(name) for _, name, *_ in rows), default=4)
    max_name = max(10, min(max_name, 20))
    W_ID, W_DAYS, W_NAME, W_QTY, W_UNIT, W_EXP = 2, 9, max_name, 6, 4, 10
    print("\n" + f"{'ID':>{W_ID}}  | {'Days':<{W_DAYS}} | {'Item':<{W_NAME}} | {'Qty':>{W_QTY}} | {'Unit':<{W_UNIT}} | {'Expiry':<{W_EXP}}")
    print("-" * (W_ID + W_DAYS + W_NAME + W_QTY + W_UNIT + W_EXP + 18))
    for (iid, name, qty, unit, cat, loc, pur, exp) in rows:
        dleft = days_left(exp)
        dtxt_f = pad_visible(_color_days(dleft), W_DAYS, align="left")
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
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print("Leave blank to keep current value.")
    n_name = input(f"Name [{name}]: ").strip() or name
    n_qty = input(f"Qty [{qty}]: ").strip()
    try:
        n_qty = float(n_qty) if n_qty else qty
    except ValueError:
        n_qty = qty
    n_unit = input(f"Unit [{unit}]: ").strip() or unit
    n_cat = input(f"Category [{category or ''}]: ").strip() or category
    n_loc = (input(f"Location [{location}]: ").strip() or location).title()
    n_purchased_raw = input(f"Purchased on [{purchased or dt.date.today().isoformat()}]: ").strip()
    if n_purchased_raw == "":
        n_purchased = purchased
    else:
        parsed = parse_date_input(n_purchased_raw)
        n_purchased = parsed if parsed else purchased
    n_expiry = input(f"Expiry on [{expiry or ''}] (blank to auto/use existing): ").strip()
    if n_expiry == "":
        if not expiry:
            days = shelf_life_days(n_name, n_loc)
            n_expiry = estimated_expiry(n_purchased or dt.date.today().isoformat(), days) if days else None
        else:
            n_expiry = expiry
    n_source = input(f"Source [{source or ''}]: ").strip() or source
    n_notes = input(f"Notes [{notes or ''}]: ").strip() or notes

    try:
        update_item(iid, n_name, n_cat, n_qty, n_unit, n_loc, n_purchased, n_expiry, n_source, n_notes)
        print("Item updated.")
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
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print(f"\nSelected: {iid} - {name} | {qty} {unit} | {category or '-'} | {location} | purchased: {purchased or '-'} | expiry: {expiry or '-'}")
    yn = input("Delete this item? [y/N] ").strip().lower()
    if yn not in ("y", "yes"):
        print("Cancelled.")
        return
    try:
        ok = delete_item(iid)
        print("Item deleted." if ok else "Item not deleted.")
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
    _, name, _, qty, unit, _, _, _, _, _ = row
    print(f"\nCurrent: {name} - {qty} {unit}")
    try:
        amount = float(input(f"Amount to consume [all={qty}]: ").strip() or qty)
    except ValueError:
        print("Invalid amount.")
        return
    ok, new_qty = consume_item(iid, amount)
    if not ok:
        print("Error updating item.")
        return
    print(f"Updated: {new_qty} {unit} remaining")
    if new_qty <= 0:
        yn = input("Item is empty. Delete it? [y/N] ").strip().lower()
        if yn in ("y", "yes"):
            if delete_item(iid):
                print("Item deleted.")
            else:
                print("Error deleting item.")

def cmd_recognize_image():
    path = input("Path to image file (or Enter to cancel): ").strip()
    if not path:
        print("Cancelled.")
        return
    if not os.path.isfile(path):
        print("File not found:", path)
        return
    try:
        import recognizer
        result = recognizer.recognize(path)
        print("Recognition result:", result)
    except ImportError:
        print("Recognizer not implemented yet.")
    except Exception as e:
        print("Error while running recognizer:", e)

# ---------- Main ----------

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
        elif choice == "6": cmd_consume_item()
        elif choice == "7": cmd_recognize_image()
        elif choice == "8":
            img_path = input("Path to image with barcode: ").strip()
            scan_and_add_product(img_path)
        elif choice == "0":
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
