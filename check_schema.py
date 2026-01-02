from db import get_db

db = get_db()

rows = db.execute("PRAGMA table_info(order_items);").fetchall()
db.close()

for r in rows:
    print(dict(r))
