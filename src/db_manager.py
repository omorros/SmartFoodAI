import sqlite3, os, datetime as dt
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
