import csv
import os
import re
import datetime as dt
from typing import Optional

# try to use rapidfuzz for fuzzy name matching (optional)
try:
    from rapidfuzz import process, fuzz
    _RAPID_AVAILABLE = True
except Exception:
    _RAPID_AVAILABLE = False

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
                if name and days is not None:
                    _SHELF[name] = days
    except FileNotFoundError:
        _SHELF = {}
    return _SHELF

def shelf_life_days(name: str, location: Optional[str] = None) -> Optional[int]:
    """
    Return shelf-life days for `name`. Matching ignores `location`.
    Order of attempts:
      1) exact case-insensitive match
      2) substring match
      3) fuzzy match (rapidfuzz) if available
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

    # fuzzy match (best effort) if rapidfuzz is available
    if _RAPID_AVAILABLE and shelf:
        choices = list(shelf.keys())
        match = process.extractOne(key, choices, scorer=fuzz.token_set_ratio)
        if match:
            matched_name, score, _ = match
            if score >= 75:
                return shelf.get(matched_name)

    # no rule found
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

def parse_date_input(s: Optional[str]) -> Optional[str]:
    """
    Parse a user-entered date string into ISO YYYY-MM-DD.
    Accepts:
      - "" or None -> today's date (ISO)
      - "today" / "t"
      - "yesterday" / "y"
      - "N" or "Nd" or "N days ago" -> N days ago (e.g. "3", "3d", "3 days ago")
      - "YYYY-MM-DD"
      - "MM-DD" or "MM/DD" -> assumes current year
      - "DD" -> assumes current month/year
    Returns ISO date string or None if parsing fails.
    """
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return dt.date.today().isoformat()
    low = s.lower()
    if low in ("today", "t"):
        return dt.date.today().isoformat()
    if low in ("yesterday", "y", "yd"):
        return (dt.date.today() - dt.timedelta(days=1)).isoformat()

    # relative days: "3", "3d", "3 days ago"
    m = re.match(r"^(-?\d+)\s*(?:d(?:ays?)?)?$", low)
    if m:
        n = int(m.group(1))
        return (dt.date.today() - dt.timedelta(days=n)).isoformat()

    m = re.match(r"^(\d+)\s*days?\s*ago$", low)
    if m:
        n = int(m.group(1))
        return (dt.date.today() - dt.timedelta(days=n)).isoformat()

    # ISO date
    try:
        d = dt.date.fromisoformat(s)
        return d.isoformat()
    except Exception:
        pass

    # MM-DD or MM/DD
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})$", s)
    if m:
        mm = int(m.group(1))
        dd = int(m.group(2))
        try:
            d = dt.date(dt.date.today().year, mm, dd)
            return d.isoformat()
        except Exception:
            return None

    # DD only
    if re.match(r"^\d{1,2}$", s):
        dd = int(s)
        today = dt.date.today()
        try:
            d = dt.date(today.year, today.month, dd)
            return d.isoformat()
        except Exception:
            return None

    return None

def safe_input(prompt, valid_options=None, allow_empty=False):
    """
    Generic input function that validates user input.
    - valid_options: list of allowed lowercase strings (optional)
    - allow_empty: if True, empty input returns None
    """
    while True:
        user_input = input(prompt).strip()
        if user_input == "" and allow_empty:
            return None
        if valid_options and user_input.lower() not in valid_options:
            print(f"Invalid input. Valid options are: {', '.join(valid_options)}.")
            continue
        return user_input
