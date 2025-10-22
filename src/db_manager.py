from typing import Optional
import sqlite3
import os
import datetime as dt

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "smartfood.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  qty REAL DEFAULT 1,
  unit TEXT DEFAULT '',
  location TEXT CHECK(location IN ('Fridge','Freezer','Pantry')) DEFAULT 'Fridge',
  purchased_on TEXT,
  expiry_on TEXT,
  source TEXT,
  notes TEXT
);
"""

def get_con():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = get_con()
    con.executescript(SCHEMA)
    con.commit()
    con.close()

def add_item(name, category=None, qty=1, unit="", location="Fridge",
             purchased_on=None, expiry_on=None, source=None, notes=None):
    con = get_con()
    purchased_on = purchased_on or dt.date.today().isoformat()
    cur = con.execute(
        """INSERT INTO items(name, category, qty, unit, location, purchased_on, expiry_on, source, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (name, category, qty, unit, location, purchased_on, expiry_on, source, notes)
    )
    con.commit()
    iid = cur.lastrowid      
    con.close()
    return iid               

def list_items():
    con = get_con()
    rows = con.execute("""SELECT id,name,qty,unit,category,location,purchased_on,expiry_on
                          FROM items""").fetchall()
    con.close()
    return rows

# --- new helpers for edit/delete ---
def get_item(item_id):
    """Return full row for item id or None."""
    con = get_con()
    row = con.execute("""SELECT id,name,category,qty,unit,location,purchased_on,expiry_on,source,notes
                         FROM items WHERE id = ?""", (item_id,)).fetchone()
    con.close()
    return row

def update_item(item_id, name, category, qty, unit, location, purchased_on, expiry_on, source=None, notes=None):
    """Update item by id. Provide full values (use existing to keep)."""
    con = get_con()
    con.execute(
        """UPDATE items SET name=?, category=?, qty=?, unit=?, location=?, purchased_on=?, expiry_on=?, source=?, notes=?
           WHERE id = ?""",
        (name, category, qty, unit, location, purchased_on, expiry_on, source, notes, item_id)
    )
    con.commit()
    con.close()

def delete_item(item_id):
    """Delete item by id. Returns True if row deleted."""
    con = get_con()
    cur = con.execute("DELETE FROM items WHERE id = ?", (item_id,))
    con.commit()
    affected = cur.rowcount
    con.close()
    return affected > 0

def consume_item(item_id: int, amount: float) -> tuple[bool, Optional[float]]:
    """
    Reduce item quantity by amount. Returns (success, new_qty).
    If new qty <= 0, item is kept but qty=0 is stored.
    """
    con = get_con()
    try:
        # Get current qty
        row = con.execute("SELECT qty FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return False, None
        current = row[0] or 0
        new_qty = max(0, current - amount)  # don't allow negative
        # Update
        con.execute("UPDATE items SET qty = ? WHERE id = ?", (new_qty, item_id))
        con.commit()
        return True, new_qty
    finally:
        con.close()
