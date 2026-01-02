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
                flash("Необхідно вибрати або ввести клієнта", "warning")
                return redirect(url_for("orders_list"))


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


@app.route("/orders/<int:order_id>/items/add", methods=["POST"])
@login_required
def order_item_add(order_id: int):
    item_type = request.form.get("item_type", "cut")

    db = get_db()

    if item_type == "cut":
        film_owner = request.form.get("film_owner")  # our/client
        film_kind = request.form.get("film_kind")    # white/color/metal/reflective
        weed = request.form.get("weed") == "1"
        tape = request.form.get("tape") == "1"
        if tape and not weed:
            weed = True

        ws = request.form.getlist("cut_w_mm[]")
        hs = request.form.getlist("cut_h_mm[]")
        qs = request.form.getlist("cut_qty[]")

        sizes = []
        for w_s, h_s, q_s in zip(ws, hs, qs):
            w = int(w_s or 0)
            h = int(h_s or 0)
            q = int(q_s or 0)
            if w > 0 and h > 0 and q > 0:
                sizes.append({"w_mm": w, "h_mm": h, "qty": q})

        if not sizes:
            flash("Потрібно додати хоча б один розмір і кількість.", "warning")
            db.close()
            return redirect(url_for("order_view", order_id=order_id))

        params = {
            "film_owner": film_owner,
            "film_kind": film_kind,
            "weed": weed,
            "tape": tape,
            "sizes": sizes,
        }

        # qty у таблиці можна тримати 1 (бо реальна кількість в sizes)
        db.execute("""
            INSERT INTO order_items (order_id, item_type, qty, params_json)
            VALUES (?, 'cut', 1, ?)
        """, (order_id, json.dumps(params, ensure_ascii=False)))

        db.commit()
        db.close()
        flash("Позицію (порізка) додано.", "success")
        return redirect(url_for("order_view", order_id=order_id))

    elif item_type == "template":
        # Рекомендую теж зробити qty біля розміру (як ти хочеш)
        w = int(request.form.get("tpl_w_mm", "0") or 0)
        h = int(request.form.get("tpl_h_mm", "0") or 0)
        q = int(request.form.get("tpl_qty", "1") or 1)

        if w <= 0 or h <= 0 or q <= 0:
            flash("Для шаблону вкажи розмір і кількість.", "warning")
            db.close()
            return redirect(url_for("order_view", order_id=order_id))

        params = {"sizes": [{"w_mm": w, "h_mm": h, "qty": q}]}
        db.execute("""
            INSERT INTO order_items (order_id, item_type, qty, width_mm, height_mm, params_json)
            VALUES (?, 'template', 1, ?, ?, ?)
        """, (order_id, w, h, json.dumps(params, ensure_ascii=False)))

        db.commit()
        db.close()
        flash("Позицію (шаблон) додано.", "success")
        return redirect(url_for("order_view", order_id=order_id))

    flash("Цей тип позиції поки не підтримується.", "info")
    db.close()
    return redirect(url_for("order_view", order_id=order_id))



if __name__ == "__main__":
    app.run(debug=True)
