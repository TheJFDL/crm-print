from flask import Flask, render_template, request, redirect, url_for
from config import SECRET_KEY
from db import get_db

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

@app.route("/")
def orders_list():
    db = get_db()
    orders = db.execute("""
        SELECT o.id, o.created_at, o.status, o.title, o.created_by, o.assigned_to, c.name as client_name
        FROM orders o
        JOIN clients c ON c.id = o.client_id
        ORDER BY o.created_at DESC
    """).fetchall()

    clients = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    db.close()

    return render_template(
        "orders_list.html",
        orders=orders,
        clients=clients,
        statuses=_order_statuses(),
        assignees=_assignees()
    )


@app.route("/orders/new", methods=["GET", "POST"])
def order_new():
    db = get_db()

    if request.method == "POST":
        client_id = request.form.get("client_id") or ""
        new_client_name = (request.form.get("new_client_name") or "").strip()
        title = (request.form.get("title") or "").strip()
        status = request.form.get("status") or "Нове"
        created_by = request.form.get("created_by") or "Менеджер"
        assigned_to = request.form.get("assigned_to") or "Менеджер"


        # 1) якщо обрали існуючого
        if client_id.isdigit():
            cid = int(client_id)

        # 2) або створюємо нового (якщо ввели ім'я)
        elif new_client_name:
            cur = db.execute("INSERT INTO clients(name) VALUES (?)", (new_client_name,))
            cid = cur.lastrowid
            

        else:
            # немає ні вибору, ні нового клієнта
            clients = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
            db.close()
            return render_template(
                "order_new.html",
                clients=clients,
                statuses=_order_statuses(),
                error="Вибери клієнта або введи нового."
            )

        cur = db.execute(
            "INSERT INTO orders(client_id, status, title, created_by, assigned_to) VALUES (?,?,?,?,?)",
            (cid, status, title, created_by, assigned_to)
        )

        order_id = cur.lastrowid
        db.commit()
        db.close()
        return redirect(url_for("order_view", order_id=order_id))

    clients = db.execute("SELECT id, name FROM clients ORDER BY name").fetchall()
    db.close()
    return render_template("order_new.html", clients=clients, statuses=_order_statuses(), error=None)

@app.route("/orders/<int:order_id>")
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
    assigned_to = request.form.get("assigned_to")

    db = get_db()
    if status:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    if assigned_to:
        db.execute("UPDATE orders SET assigned_to=? WHERE id=?", (assigned_to, order_id))
    db.commit()
    db.close()

    return redirect(url_for("orders_list"))


def _order_statuses():
    return [
        "Нове",
        "Очікує макет",
        "Макет на перевірці",
        "В роботі",
        "На друці",
        "Постобробка",
        "Готово",
        "Видано / Закрито",
        "Скасовано",
    ]

def _assignees():
    return ["Менеджер", "Дизайнер 1", "Дизайнер 2"]


if __name__ == "__main__":
    app.run(debug=True)
