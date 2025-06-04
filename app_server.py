# app_server.py - Web server for the Telegram Mini App interface

from flask import Flask, jsonify

import models

app = Flask(__name__, static_folder="frontend", static_url_path="/")

@app.route("/")
def index_page():
    """Serve the main interface page (frontend/index.html)."""
    return app.send_static_file("index.html")

@app.route("/api/signals")
def get_signals():
    """Provide a JSON of recent signals for the web interface."""
    # Return the last 20 signals (thread-safe access)
    with models.signals_lock:
        recent_signals = models.signals[-20:]
        data = [
            {
                "time": sig.time,
                "asset": sig.asset,
                "direction": sig.direction,
                "amount": sig.amount,
                "entry_price": sig.entry_price,
                "result": sig.result
            } for sig in recent_signals
        ]
    return jsonify(data)
