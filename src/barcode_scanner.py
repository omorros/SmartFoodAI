import requests
import pyzxing
import datetime as dt
from db_manager import add_item
from utils import parse_date_input
from semantic_mapper import get_closest_category  # <-- AI semantic mapping

# --- BARCODE SCANNER (offline image detection) ---
def scan_barcode_local(image_path: str):
    """
    Detect and decode barcodes from an image using pyzxing (offline, cross-platform).
    Returns the barcode number as string, or None if not detected.
    """
    reader = pyzxing.BarCodeReader()
    results = reader.decode(image_path)

    if not results:
        print("No barcode detected.")
        return None

    data = results[0].get("raw", None)
    print(f"Detected barcode: {data}")
    return data


# --- OPEN FOOD FACTS LOOKUP (online) ---
def lookup_product_by_barcode(barcode: str) -> dict | None:
    """
    Query Open Food Facts API for product details.
    Returns dict with product_name, brand, category or None if not found.
    """
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
        "categories": p.get("categories", "").strip(),
        "expiration_date": p.get("expiration_date", "").strip()
    }


# --- MAIN INTEGRATION WORKFLOW ---
def scan_and_add_product(image_path: str):
    """
    Full workflow:
    1) Scan barcode from image
    2) Fetch product info via API
    3) Use AI category refinement + expiry prediction
    4) Save into SmartFoodAI database
    """
    barcode = scan_barcode_local(image_path)
    if not barcode:
        return

    product_info = lookup_product_by_barcode(barcode)

    if product_info:
        print(f"Product found: {product_info['product_name']} | Brand: {product_info['brands']} | Category: {product_info['categories']}")
        name = product_info["product_name"] or input("Enter product name: ").strip()
        category = product_info["categories"].split(",")[0].lower() if product_info["categories"] else input("Enter category: ").strip().lower()
    else:
        print("Product not found in OpenFoodFacts.")
        name = input("Enter product name manually: ").strip()
        category = input("Enter category manually: ").strip().lower()

    # --- AI semantic refinement ---
    try:
        auto_cat, score = get_closest_category(name)
        if auto_cat:
            print(f"AI-refined category: {auto_cat} (similarity={score:.2f})")
            use_auto = input("Use AI category instead? [Y/n]: ").strip().lower()
            if use_auto in ("", "y", "yes"):
                category = auto_cat
    except Exception as e:
        print("Semantic mapping skipped:", e)

    qty = float(input("Quantity (e.g., 1): ") or "1")
    unit = input("Unit (g, L, pcs): ").strip() or "pcs"
    location = (input("Location (Fridge/Freezer/Pantry) [Fridge]: ").strip() or "Fridge").title()

    purchased_raw = input("Purchased on (YYYY-MM-DD or '3' = 3 days ago) [today]: ").strip()
    purchased = parse_date_input(purchased_raw) or dt.date.today().isoformat()

    # --- Predict shelf life using your FastAPI ---
    expiry = None
    try:
        payload = {
            "category": category,
            "location": location.lower(),
            "packaging": "sealed",
            "state": "raw",
            "temperature": 4 if location.lower() == "fridge" else 20
        }
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        if response.status_code == 200:
            data = response.json()
            predicted_days = data.get("predicted_shelf_life_days")
            if predicted_days:
                expiry_date = dt.date.today() + dt.timedelta(days=float(predicted_days))
                expiry = expiry_date.isoformat()
                print(f"Predicted shelf life: ~{predicted_days:.1f} days (expiry: {expiry})")

                confirm = input("Is this expiry accurate? (y/n or custom date YYYY-MM-DD): ").strip().lower()
                if confirm == "n":
                    expiry = input("Enter expiry date manually (YYYY-MM-DD): ").strip()
                elif len(confirm) == 10 and "-" in confirm:
                    expiry = confirm
                else:
                    print("Using predicted expiry.")
        else:
            print("API error:", response.text)
    except Exception as e:
        print("Prediction skipped:", e)

    # --- If OpenFoodFacts provided expiry, prefer it ---
    if not expiry and product_info and product_info.get("expiration_date"):
        expiry = product_info["expiration_date"]
        print(f"Using expiry from OpenFoodFacts: {expiry}")

    # --- Save to DB ---
    try:
        iid = add_item(
            name,
            category,
            qty,
            unit,
            location,
            purchased,
            expiry,
            "Barcode",
            f"{product_info.get('brands', 'Unknown')} | {barcode}"
        )
        print(f"Saved item ID {iid}: {name} ({barcode})")
    except Exception as e:
        print("Error saving item:", e)
