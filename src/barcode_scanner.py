import requests
import pyzxing
from db_manager import add_item
import datetime as dt

from utils import parse_date_input

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
        "categories": p.get("categories", "").strip()
    }


# --- MAIN INTEGRATION ---
def scan_and_add_product(image_path: str):
    """
    Full workflow:
    1) Scan barcode from image
    2) Fetch product info via API
    3) Ask user for missing data if not found
    4) Save into SmartFoodAI database
    """
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

    purchased_raw = input("Purchased on (YYYY-MM-DD or '3' = 3 days ago) [today]: ").strip()
    from utils import parse_date_input
    purchased = parse_date_input(purchased_raw) or dt.date.today().isoformat()

    expiry = input("Expiry date (YYYY-MM-DD) [optional]: ").strip() or None


    try:
        iid = add_item(name, category, qty, unit, location, purchased, expiry, source="barcode", notes=f"barcode:{barcode}")
        print(f"Saved item ID {iid}: {name} ({barcode})")
    except Exception as e:
        print("Error saving item:", e)
