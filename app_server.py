# app_server.py - Web-сервер для Telegram Mini App интерфейса

from flask import Flask, jsonify
import models

app = Flask(__name__, static_folder="frontend", static_url_path="/")

@app.route("/")
def index_page():
    """Отдаёт главную страницу (frontend/index.html)."""
    return app.send_static_file("index.html")

@app.route("/analytics")
def analytics_page():
    """Отдаёт страницу аналитики (frontend/analytics.html)."""
    return app.send_static_file("analytics.html")

@app.route("/api/signals")
def get_signals():
    """
    Возвращает JSON со свежими сигналами для веб-интерфейса.
    Параметр limit передаётся через query-string (default: 20).
    """
    from flask import request
    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        limit = 20

    with models.signals_lock:
        recent_signals = models.signals[-limit:]
        data = [
            {
                "time": sig.time,
                "asset": sig.asset,
                "direction": sig.direction,
                "amount": sig.amount,
                "entry_price": sig.entry_price,
                "result": sig.result
            }
            for sig in recent_signals
        ]
    return jsonify(data)
