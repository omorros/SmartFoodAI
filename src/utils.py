import csv, os, datetime as dt
from typing import Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "shelf_life.csv")

# cache mapping: name_lower -> days (int)
_SHELF = None

def _load_shelf():
    global _SHELF
    if _SHELF is not None:
        return _SHELF
    _SHELF = {}
    try:
        with open(DATA_PATH, newline='', encoding='utf-8') as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                name = (r.get("name") or "").strip().lower()
                days = r.get("days")
                try:
                    days = int(days) if days not in (None, "") else None
                except ValueError:
                    days = None
                if name and days is not None and name not in _SHELF:
                    # store by name only, ignore location
                    _SHELF[name] = days
    except FileNotFoundError:
        _SHELF = {}
    return _SHELF

def shelf_life_days(name: str, location: Optional[str] = None) -> Optional[int]:
    """
    Return shelf-life days for `name`, ignoring `location`.
    Tries exact case-insensitive match, then substring match.
    """
    if not name:
        return None
    shelf = _load_shelf()
    key = name.strip().lower()
    # exact match
    if key in shelf:
        return shelf[key]
    # substring match (e.g., "green apple" -> "apple")
    for k, days in shelf.items():
        if k in key or key in k:
            return days
    return None

def estimated_expiry(purchased_iso: str, days: int) -> str:
    """
    Return expiry date (ISO) by adding `days` to purchased_iso.
    purchased_iso may be an ISO date or None -> today.
    """
    if not purchased_iso:
        purchased = dt.date.today()
    else:
        purchased = dt.date.fromisoformat(purchased_iso)
    return (purchased + dt.timedelta(days=days)).isoformat()

def days_left(expiry_iso: Optional[str]) -> Optional[int]:
    """
    Return number of days until expiry (int). If expiry_iso is None or invalid -> None.
    If expired, returns negative or zero accordingly.
    """
    if not expiry_iso:
        return None
    try:
        exp = dt.date.fromisoformat(expiry_iso)
    except Exception:
        return None
    return (exp - dt.date.today()).days
