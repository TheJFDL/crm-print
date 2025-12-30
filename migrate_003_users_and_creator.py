from db import get_db

db = get_db()
db.execute("PRAGMA foreign_keys = ON;")

# users (якщо ще не існує)
db.executescript("""
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  full_name     TEXT NOT NULL,
  role          TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  is_active     INTEGER NOT NULL DEFAULT 1,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
""")

# додаємо orders.created_by_user_id (якщо ще нема)
try:
    db.execute("ALTER TABLE orders ADD COLUMN created_by_user_id INTEGER;")
except Exception:
    pass

db.commit()
db.close()
print("Migration OK")
