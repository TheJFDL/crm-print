from db import get_db

sql = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS order_items (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id        INTEGER NOT NULL,
  product_type    TEXT NOT NULL DEFAULT 'other',
  width_mm        REAL,
  height_mm       REAL,
  qty             INTEGER NOT NULL DEFAULT 1,
  material        TEXT,
  finishing       TEXT,
  note            TEXT,
  area_m2         REAL,
  perimeter_m     REAL,
  grommets_qty    INTEGER,
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
"""

db = get_db()
db.executescript(sql)
db.commit()
db.close()

print("Migration OK: order_items created")
