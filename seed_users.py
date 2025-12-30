from werkzeug.security import generate_password_hash
from db import get_db

users = [
    ("manager", "Менеджер", "manager", "1234"),
    ("designer1", "Дизайнер 1", "designer", "1234"),
    ("designer2", "Дизайнер 2", "designer", "1234"),
]

db = get_db()
for username, full_name, role, pwd in users:
    try:
        db.execute(
            "INSERT INTO users(username, full_name, role, password_hash) VALUES (?,?,?,?)",
            (username, full_name, role, generate_password_hash(pwd))
        )
    except Exception:
        pass

db.commit()
db.close()
print("Seed OK (passwords: 1234)")
