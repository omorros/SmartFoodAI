import os, csv, datetime as dt
from functools import lru_cache

# path to data/shelf_life.csv (go up one folder from /src to project root)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SHELF_LIFE_CSV = os.path.join(DATA_DIR, "shelf_life.csv")

@lru_cache(maxsize=1)
def _load_shelf_life():
    """Load shelf_life.csv -> list of dicts"""
    rows = []
    if not os.path.exists(SHELF_LIFE_CSV):
        return rows
    with open(SHELF_LIFE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # normalize
            row = {k: (v.strip() if isinstance(v, str) else v) for k,v in row.items()}
            row["name_lc"] = row["name"].lower()
            row["location"] = row.get("location", "Fridge")
            row["days"] = int(row["days"])
            rows.append(row)
    return rows

def shelf_life_days(name: str, location: str = "Fridge") -> int | None:
    """Get default shelf-life (days) for a given item name + location."""
    name_lc = (name or "").strip().lower()
    loc = (location or "Fridge").strip().title()
    best = None
    for row in _load_shelf_life():
        if row["name_lc"] == name_lc and row["location"].title() == loc:
            best = row["days"]; break
    return best  # None if not found

def estimated_expiry(purchased_on: str, days: int) -> str:
    """YYYY-MM-DD + days -> new YYYY-MM-DD."""
    p = dt.date.fromisoformat(purchased_on)
    return (p + dt.timedelta(days=days)).isoformat()

def days_left(expiry_on: str) -> int | None:
    """Return days remaining until expiry. None if no date."""
    if not expiry_on: return None
    try:
        e = dt.date.fromisoformat(expiry_on)
    except Exception:
        return None
    return (e - dt.date.today()).days
