from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import SECRET_KEY
from db import get_db
from werkzeug.security import check_password_hash
from functools import wraps
import json
import sqlite3


app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        db = get_db()
        u = db.execute(
            "SELECT id, username, full_name, role, password_hash FROM users WHERE username=? AND is_active=1",
            (username,)
        ).fetchone()
        db.close()

        if u and check_password_hash(u["password_hash"], password):
            session["user_id"] = u["id"]
            session["full_name"] = u["full_name"]
            session["role"] = u["role"]
            return redirect(url_for("orders_list"))

        return render_template("login.html", error="Невірний логін чи пароль")

    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def current_user():
    return {
        "user_id": session.get("user_id"),
        "full_name": session.get("full_name"),
        "role": session.get("role"),
    }

@app.route("/clients")
@login_required
def clients_list():
    return "Clients page (soon)"

@app.route("/payments")
@login_required
def payments_list():
    return "Payments page (soon)"

@app.route("/reports")
@login_required
def reports():
    return "Reports page (soon)"


@app.route("/")
@login_required
def orders_list():
    db = get_db()
    orders = db.execute("""
        SELECT
            o.id, o.created_at, o.status, o.title,
            c.name AS client_name,
            COALESCE(u.full_name, o.created_by) AS creator_name
        FROM orders o
        JOIN clients c ON c.id = o.client_id
        LEFT JOIN users u ON u.id = o.created_by_user_id
        ORDER BY o.created_at DESC
    """).fetchall()


    clients_rows = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    clients = [{"id": r["id"], "name": r["name"]} for r in clients_rows]

    db.close()

    return render_template(
        "orders_list.html",
        orders=orders,
        clients=clients,
        statuses=_order_statuses(),
    )


@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def order_new():
    db = get_db()

    if request.method == "POST":
        client_id = request.form.get("client_id") or ""
        title = (request.form.get("title") or "").strip()
        status = request.form.get("status") or "Нове"


        client_id = (request.form.get("client_id") or "").strip()
        client_name = (request.form.get("client_name") or "").strip()

        if client_id.isdigit():
            cid = int(client_id)
        else:
            if not client_name:
                # помилка: не ввели клієнта
                clients = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
                clients_rows = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
                clients = [{"id": r["id"], "name": r["name"]} for r in clients_rows]
                db.close()
                return render_template(
                    "orders_list.html",
                    orders=orders,
                    clients=clients,
                    statuses=_order_statuses(),
                )


            # 1) пробуємо знайти існуючого по точній назві (без різниці регістру)
            row = db.execute(
                "SELECT id FROM clients WHERE lower(trim(name)) = lower(trim(?)) LIMIT 1",
                (client_name,)
            ).fetchone()

            if row:
                cid = row["id"]
            else:
                # 2) створюємо нового
                cur = db.execute("INSERT INTO clients(name) VALUES (?)", (client_name,))
                cid = cur.lastrowid

        u = current_user()
        created_by_user_id = u["user_id"]
        created_by_name = u["full_name"]  # можемо лишити як дубль-текст для зручності

        cur = db.execute(
            "INSERT INTO orders(client_id, status, title, created_by, created_by_user_id) VALUES (?,?,?,?,?)",
            (cid, status, title, created_by_name, created_by_user_id)
        )


        order_id = cur.lastrowid
        db.commit()
        db.close()
        return redirect(url_for("order_view", order_id=order_id))

    clients = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    db.close()
    return render_template("order_new.html", clients=clients, statuses=_order_statuses(), error=None)

@app.route("/orders/<int:order_id>")
@login_required
def order_view(order_id: int):
    db = get_db()
    order = db.execute("""
        SELECT o.*, c.name AS client_name
        FROM orders o
        JOIN clients c ON c.id = o.client_id
        WHERE o.id = ?
    """, (order_id,)).fetchone()

    if order is None:
        db.close()
        return "Order not found", 404

    items = db.execute("""
        SELECT * FROM order_items
        WHERE order_id = ?
        ORDER BY id DESC
    """, (order_id,)).fetchall()

    db.close()
    return render_template("order_view.html", order=order, items=items, statuses=_order_statuses())

@app.route("/orders/<int:order_id>/quick_update", methods=["POST"])
def order_quick_update(order_id: int):
    status = request.form.get("status")

    db = get_db()
    if status:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    db.commit()
    db.close()

    return redirect(url_for("orders_list"))


def _order_statuses():
    return [
        "Нове",
        "Запустити",
        "В роботі",
        "Готово",
        "Скасовано",
    ]



if __name__ == "__main__":
    app.run(debug=True)
