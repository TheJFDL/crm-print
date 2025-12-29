from db import get_db

schema = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS clients (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id   INTEGER NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  status      TEXT NOT NULL DEFAULT 'Нове',
  title       TEXT,
  FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE RESTRICT
);
"""

db = get_db()
db.executescript(schema)

# Додамо тестового клієнта і заявку, щоб одразу побачити таблицю
db.execute("INSERT INTO clients(name) VALUES (?)", ("Тестовий клієнт",))
client_id = db.execute("SELECT id FROM clients ORDER BY id DESC LIMIT 1").fetchone()["id"]
db.execute("INSERT INTO orders(client_id, status, title) VALUES (?,?,?)",
           (client_id, "Нове", "Тестова заявка"))

db.commit()
db.close()

print("DB initialized: tables created + sample data inserted")
