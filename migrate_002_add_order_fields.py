from db import get_db

sql = """
ALTER TABLE orders ADD COLUMN created_by TEXT;
ALTER TABLE orders ADD COLUMN assigned_to TEXT;
"""

db = get_db()
# SQLite ругнеться якщо колонка вже існує — тому робимо try на кожен ALTER
for stmt in [s.strip() + ";" for s in sql.split(";") if s.strip()]:
    try:
        db.execute(stmt)
    except Exception as e:
        # якщо вже додано — пропускаємо
        pass

db.commit()
db.close()
print("Migration OK: created_by, assigned_to added")
