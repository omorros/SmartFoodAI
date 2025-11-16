from db_manager import init_db, add_item, list_items, DB_PATH, get_item, update_item, delete_item, consume_item
import datetime as dt
from utils import shelf_life_days, estimated_expiry, days_left, parse_date_input, safe_input
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import re
import os
import requests
import datetime as dt
from semantic_mapper import get_closest_category


# ANSI color helpers
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
    print("[1] Add item manually")
    print("[2] View all items")
    print("[3] View items by urgency")
    print("[4] Edit item")
    print("[5] Delete item")
    print("[6] Consume item")
    print("[7] Recognize item from image")
    print("[8] Add item via barcode scan")
    print("[0] Exit")

import requests

def cmd_add_item():
    # --- Semantic AI food name and category detection ---
    user_food = input("Name of food item: ").strip()
    if not user_food:
        print("Please enter a valid food name.")
        return

    try:
        from semantic_mapper import get_closest_category
        auto_category, similarity = get_closest_category(user_food)
        print(f"Detected category: {auto_category} (similarity={similarity})")
        use_auto = input("Use this category? [Y/n]: ").strip().lower()
        if use_auto in ("", "y", "yes"):
            category = auto_category
        else:
            category = input("Enter category manually: ").strip().lower()
    except Exception as e:
        print("Error in semantic mapping:", e)
        category = input("Category (e.g., Fruit, Dairy, Meat, Snack, Vegetable, Grain): ").strip().lower()

    name = user_food
    qty = float(input("Qty (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip()
    location = (input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip() or "Fridge").title()

    # --- Context-aware packaging and state questions ---
    if category in ["meat", "fish", "snack", "dairy"]:
        packaging = input("Packaging (sealed/open) [sealed]: ").strip() or "sealed"
    else:
        packaging = "sealed"

    if category in ["meat", "fish", "dairy", "prepared food"]:
        state = input("State (raw/cooked) [raw]: ").strip() or "raw"
    else:
        state = "raw"

    # --- Temperature defaults based on location ---
    temperature = 4 if location.lower() == "fridge" else (-18 if location.lower() == "freezer" else 20)

    purchased_raw = input("Purchased on (YYYY-MM-DD or '3' = 3 days ago) [today]: ").strip()
    purchased = parse_date_input(purchased_raw) or dt.date.today().isoformat()
    expiry = None

    # --- Predict shelf life using FastAPI model ---
    try:
        payload = {
            "category": category,
            "location": location.lower(),
            "packaging": packaging.lower(),
            "state": state.lower(),
            "temperature": temperature
        }
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        if response.status_code == 200:
            data = response.json()
            predicted_days = data.get("predicted_shelf_life_days")
            if predicted_days:
                expiry_date = dt.date.today() + dt.timedelta(days=float(predicted_days))
                expiry = expiry_date.isoformat()
                print(f"Predicted shelf life: ~{predicted_days:.1f} days (expiry: {expiry})")

                confirm = input("Is this expiry accurate? (y/n or enter a custom date YYYY-MM-DD): ").strip().lower()
                if confirm == "n":
                    expiry = input("Enter expiry date manually (YYYY-MM-DD): ").strip()
                elif len(confirm) == 10 and "-" in confirm:
                    expiry = confirm
                else:
                    print("Using predicted expiry.")
            else:
                print("Could not get a prediction from API.")
        else:
            print("API error:", response.text)
    except Exception as e:
        print("Prediction failed:", e)

    # --- Save item to local database ---
    try:
        iid = add_item(name, category, qty, unit, location, purchased, expiry, source="AI", notes=None)
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
        dtxt = pad_visible(_color_days(dleft), W_DAYS)
        print(f"{iid:>{W_ID}d} | {dtxt} | {name[:W_NAME]:<{W_NAME}} | {qty:>{W_QTY}.1f} | {unit:<{W_UNIT}} | {(cat or '-').title():<{W_CAT}} | {loc:<{W_LOC}} | {pur or '-':<{W_PUR}} | {exp or '-':<{W_EXP}}")

def cmd_list_by_urgency():
    rows = list_items()
    annotated = [(days_left(exp), iid, name, qty, unit, cat, loc, pur, exp) for (iid, name, qty, unit, cat, loc, pur, exp) in rows]
    annotated.sort(key=lambda x: (x[0] is None, x[0] if x[0] is not None else 99999))
    print("\n" + f"{'ID':>2} | {'Days':<9} | {'Item':<15} | {'Qty':>6} | {'Unit':<4} | {'Category':<12} | {'Loc':<7} | {'Expiry':<10}")
    print("-" * 85)
    for (dleft, iid, name, qty, unit, cat, loc, pur, exp) in annotated:
        dtxt = pad_visible(_color_days(dleft), 9)
        print(f"{iid:>2d} | {dtxt} | {name[:15]:<15} | {qty:>6.1f} | {unit:<4} | {(cat or '-').title():<12} | {loc:<7} | {exp or '-':<10}")

def _show_items_brief():
    rows = list_items()
    if not rows:
        print("\nNo items in database.\n")
        return
    print("\n" + f"{'ID':>2}  | {'Days':<9} | {'Item':<15} | {'Qty':>6} | {'Unit':<4} | {'Expiry':<10}")
    print("-" * 60)
    for (iid, name, qty, unit, cat, loc, pur, exp) in rows:
        dtxt = pad_visible(_color_days(days_left(exp)), 9)
        print(f"{iid:>2}  | {dtxt} | {name[:15]:<15} | {qty:>6.1f} | {unit:<4} | {exp or '-':<10}")
    print()

def cmd_edit_item():
    _show_items_brief()
    s = safe_input("Enter item ID to edit (or Enter to cancel): ", allow_empty=True)
    if not s:
        print("Cancelled.")
        return
    if not s.isdigit():
        print("Invalid id.")
        return
    iid = int(s)
    row = get_item(iid)
    if not row:
        print("Item not found.")
        return
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print("Leave blank to keep current value.")
    n_name = input(f"Name [{name}]: ").strip() or name
    n_qty = input(f"Qty [{qty}]: ").strip()
    n_qty = float(n_qty) if n_qty else qty
    n_unit = input(f"Unit [{unit}]: ").strip() or unit
    n_cat = input(f"Category [{category or ''}]: ").strip() or category
    n_loc = (input(f"Location [{location}]: ").strip() or location).title()
    n_purchased_raw = input(f"Purchased on [{purchased or dt.date.today().isoformat()}]: ").strip()
    n_purchased = parse_date_input(n_purchased_raw) or purchased
    n_expiry = input(f"Expiry on [{expiry or ''}] (blank to auto/use existing): ").strip()
    if not n_expiry:
        if not expiry:
            days = shelf_life_days(n_name, n_loc)
            n_expiry = estimated_expiry(n_purchased, days) if days else None
        else:
            n_expiry = expiry
    n_source = input(f"Source [{source or ''}]: ").strip() or source
    n_notes = input(f"Notes [{notes or ''}]: ").strip() or notes
    update_item(iid, n_name, n_cat, n_qty, n_unit, n_loc, n_purchased, n_expiry, n_source, n_notes)
    print("Item updated.")

def cmd_delete_item():
    _show_items_brief()
    s = safe_input("Enter item ID to delete (or Enter to cancel): ", allow_empty=True)
    if not s:
        print("Cancelled.")
        return
    if not s.isdigit():
        print("Invalid id.")
        return
    iid = int(s)
    row = get_item(iid)
    if not row:
        print("Item not found.")
        return
    _, name, category, qty, unit, location, purchased, expiry, source, notes = row
    print(f"\nSelected: {iid} - {name} | {qty} {unit} | {category or '-'} | {location} | purchased: {purchased or '-'} | expiry: {expiry or '-'}")
    yn = safe_input("Delete this item? [y/N] ", valid_options=["y", "yes", "n", "no"], allow_empty=True)
    if yn in ("y", "yes"):
        delete_item(iid)
        print("Item deleted.")
    else:
        print("Cancelled.")

def cmd_consume_item():
    _show_items_brief()
    s = safe_input("Enter item ID to consume (or Enter to cancel): ", allow_empty=True)
    if not s:
        print("Cancelled.")
        return
    if not s.isdigit():
        print("Please enter a valid numeric ID.")
        return
    iid = int(s)
    row = get_item(iid)
    if not row:
        print("Item not found.")
        return
    _, name, _, qty, unit, _, _, _, _, _ = row
    print(f"\nCurrent: {name} - {qty} {unit}")
    while True:
        amount_input = safe_input(f"Amount to consume [all={qty}]: ", allow_empty=True)
        if amount_input is None or str(amount_input).lower() == "all":
            amount = qty
            break
        try:
            amount = float(amount_input)
            if amount <= 0:
                print("Please enter a positive number.")
                continue
            if amount > qty:
                print("Cannot consume more than available quantity.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a number or 'all'.")
    ok, new_qty = consume_item(iid, amount)
    if not ok:
        print("Error updating item.")
        return
    print(f"Updated: {new_qty} {unit} remaining")
    if new_qty <= 0:
        yn = safe_input("Item is empty. Delete it? [y/N] ", valid_options=["y", "yes", "n", "no"], allow_empty=True)
        if yn in ("y", "yes"):
            delete_item(iid)
            print("Item deleted.")
        else:
            print("Item retained in database.")

def cmd_recognize_image():
    path = safe_input("Path to image file (or Enter to cancel): ", allow_empty=True)
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
        print("Image path saved:", path)
    except Exception as e:
        print("Error while running recognizer:", e)

def main():
    init_db()
    print(f"Using database: {DB_PATH}")
    while True:
        menu()
        choice = safe_input("Choose an option: ", valid_options=[str(i) for i in range(9)], allow_empty=False)
        if choice == "1": cmd_add_item()
        elif choice == "2": cmd_list_items()
        elif choice == "3": cmd_list_by_urgency()
        elif choice == "4": cmd_edit_item()
        elif choice == "5": cmd_delete_item()
        elif choice == "6": cmd_consume_item()
        elif choice == "7": cmd_recognize_image()
        elif choice == "8":
            print("Select an image containing the barcode...")
            try:
                Tk().withdraw()
                img_path = askopenfilename(
                    title="Select Barcode Image",
                    filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")]
                )
                if not img_path:
                    print("No file selected.")
                else:
                    from barcode_scanner import scan_and_add_product
                    scan_and_add_product(img_path)
            except Exception as e:
                print("Error opening file dialog:", e)
        elif choice == "0":
            print("Exiting SmartFoodAI. Goodbye.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
