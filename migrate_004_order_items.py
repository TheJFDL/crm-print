# migrate_004_order_items.py
import sqlite3

DB_PATH = "crm.sqlite"  # <- підстав свій шлях до БД (як у init_db.py/db.py)

SQL = """
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  item_type TEXT NOT NULL CHECK(item_type IN ('print','cut','template')),
  qty INTEGER NOT NULL DEFAULT 1,
  width_mm INTEGER,
  height_mm INTEGER,
  params_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SQL)
    conn.commit()
    conn.close()
    print("OK: order_items ensured")

if __name__ == "__main__":
    main()
