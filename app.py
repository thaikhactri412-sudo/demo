import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = "database.db"
API_KEY = os.environ.get("API_KEY", "mat_khau_bi_mat_123")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_code TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            class_name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT NOT NULL,
            checkin_time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT a.student_code, s.full_name, s.class_name, a.checkin_time, a.status
        FROM attendance a
        LEFT JOIN students s ON a.student_code = s.student_code
        ORDER BY a.id DESC
        LIMIT 100
    """)
    records = cur.fetchall()
    conn.close()
    return render_template("index.html", records=records)

@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    # Kiểm tra khóa bảo mật gửi từ máy tính ở trường
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"ok": False, "msg": "Sai API Key"}), 401

    data = request.get_json(force=True)
    code = data.get("student_code")
    if not code:
        return jsonify({"ok": False, "msg": "Thiếu student_code"}), 400

    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    status = "Đi muộn" if now.strftime("%H:%M:%S") > "07:00:00" else "Đúng giờ"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = now.strftime("%Y-%m-%d")
    cur.execute(
        "SELECT id FROM attendance WHERE student_code = ? AND checkin_time LIKE ?",
        (code, f"{today}%")
    )
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO attendance (student_code, checkin_time, status) VALUES (?, ?, ?)",
            (code, time_str, status)
        )
        conn.commit()
    conn.close()
    return jsonify({"ok": True, "time": time_str, "status": status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)