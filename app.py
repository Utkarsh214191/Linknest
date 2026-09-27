"""
LinkNest — a link-shortening tool built for sharing campus resources
(notes, PYQs, drive folders, group material) without WhatsApp link-rot.

Features:
- Shorten any URL, with an optional custom short code (e.g. /dbms-notes)
- Links auto-expire after 30 days, keeping the dashboard clutter-free
- Every link gets a click counter, so you know if people actually used it
- Every link gets an auto-generated QR code for posters / noticeboards
"""

import sqlite3
import string
import random
import io
from datetime import datetime, timedelta

from flask import Flask, request, redirect, render_template, abort, send_file, flash, url_for

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "linknest-dev-secret-change-this-in-production"

DB_PATH = "linknest.db"
LINK_LIFETIME_DAYS = 30
CODE_LENGTH = 6
CODE_CHARS = string.ascii_lowercase + string.digits


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            long_url TEXT NOT NULL,
            label TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            click_count INTEGER NOT NULL DEFAULT 0,
            last_clicked_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def generate_code(length=CODE_LENGTH):
    return "".join(random.choices(CODE_CHARS, k=length))


def code_exists(conn, code):
    return conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone() is not None


def is_expired(row):
    return datetime.fromisoformat(row["expires_at"]) < datetime.now()


@app.route("/", methods=["GET"])
def dashboard():
    conn = get_db()
    rows = conn.execute("SELECT * FROM links ORDER BY created_at DESC").fetchall()
    conn.close()

    active_links = []
    expired_count = 0
    for row in rows:
        if is_expired(row):
            expired_count += 1
            continue
        days_left = (datetime.fromisoformat(row["expires_at"]) - datetime.now()).days
        active_links.append({
            "code": row["code"],
            "long_url": row["long_url"],
            "label": row["label"] or row["long_url"],
            "click_count": row["click_count"],
            "days_left": max(days_left, 0),
            "created_at": row["created_at"][:10],
        })

    return render_template(
        "index.html",
        links=active_links,
        expired_count=expired_count,
        total_clicks=sum(l["click_count"] for l in active_links),
    )


@app.route("/create", methods=["POST"])
def create_link():
    long_url = request.form.get("long_url", "").strip()
    custom_code = request.form.get("custom_code", "").strip().lower()
    label = request.form.get("label", "").strip()

    if not long_url:
        flash("Please paste a URL to shorten.")
        return redirect(url_for("dashboard"))

    if not (long_url.startswith("http://") or long_url.startswith("https://")):
        long_url = "https://" + long_url

    conn = get_db()

    if custom_code:
        code = "".join(c for c in custom_code if c.isalnum() or c in "-_")
        if not code:
            flash("Custom code must contain letters, numbers, - or _.")
            conn.close()
            return redirect(url_for("dashboard"))
        if code_exists(conn, code):
            flash(f'The code "{code}" is already taken. Try another one.')
            conn.close()
            return redirect(url_for("dashboard"))
    else:
        code = generate_code()
        while code_exists(conn, code):
            code = generate_code()

    now = datetime.now()
    expires = now + timedelta(days=LINK_LIFETIME_DAYS)

    conn.execute(
        "INSERT INTO links (code, long_url, label, created_at, expires_at, click_count) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (code, long_url, label, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    conn.close()

    flash(f"Short link created: /{code}")
    return redirect(url_for("dashboard"))


@app.route("/<code>")
def follow_link(code):
    conn = get_db()
    row = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()

    if row is None or is_expired(row):
        conn.close()
        abort(404)

    conn.execute(
        "UPDATE links SET click_count = click_count + 1, last_clicked_at = ? WHERE code = ?",
        (datetime.now().isoformat(), code),
    )
    conn.commit()
    long_url = row["long_url"]
    conn.close()
    return redirect(long_url)


@app.route("/qr/<code>.png")
def qr_code(code):
    if not QR_AVAILABLE:
        abort(503, description="QR code support needs 'pip install qrcode[pil]'.")

    conn = get_db()
    row = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
    conn.close()
    if row is None:
        abort(404)

    short_url = request.host_url.rstrip("/") + "/" + code
    img = qrcode.make(short_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
