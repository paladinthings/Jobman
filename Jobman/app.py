from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
import sqlite3
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret"

DB_FILE = "jobs.db"

def get_db():
    return sqlite3.connect(DB_FILE)

def load_jobs():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, password_hash, role
            FROM users
            WHERE username = ?
        """, (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["role"] = user[2]
            return redirect(url_for("index"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    df = load_jobs()
    df = load_jobs()

    keyword = request.args.get("keyword", "").lower()
    location = request.args.get("location", "").lower()
    source = request.args.get("source", "").lower()

    if keyword:
        df = df[df["title"].str.lower().str.contains(keyword, na=False)]

    if location:
        df = df[df["location"].str.lower().str.contains(location, na=False)]

    if source:
        df = df[df["source"].str.lower().str.contains(source, na=False)]

    total_jobs = len(df)

    jobs = df.sort_values(by="scraped_at", ascending=False).to_dict(orient="records")
    return render_template("index.html", jobs=jobs, total_jobs=total_jobs)

@app.route("/api/favorites", methods=["GET"])
def api_get_favorites():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT job_link, title
        FROM favorites
        WHERE user_id = ?
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    data = [{"link": r[0], "title": r[1]} for r in rows]
    return jsonify(data)


@app.route("/api/favorites/add", methods=["POST"])
def api_add_favorite():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    link = data.get("link")
    title = data.get("title")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO favorites (user_id, job_link, title, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        session["user_id"],
        link,
        title,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/favorites/remove", methods=["POST"])
def api_remove_favorite():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    link = data.get("link")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM favorites
        WHERE job_link = ?
        AND user_id = ?
    """, (link, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, due, details, done
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "title": r[1],
            "due": r[2],
            "details": r[3],
            "done": bool(r[4])
        })

    return jsonify(tasks)

@app.route("/api/tasks/add", methods=["POST"])
def api_add_task():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (user_id, title, due, details, done, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        data.get("title", ""),
        data.get("due", ""),
        data.get("details", ""),
        0,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/tasks/delete", methods=["POST"])
def api_delete_task():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    task_id = data.get("id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM tasks
        WHERE id = ?
        AND user_id = ?
    """, (task_id, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/tasks/toggle", methods=["POST"])
def api_toggle_task():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    task_id = data.get("id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET done = CASE WHEN done = 1 THEN 0 ELSE 1 END
        WHERE id = ?
        AND user_id = ?
    """, (task_id, session["user_id"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/notes", methods=["GET"])
def api_get_notes():
    if "user_id" not in session:
        return jsonify({"content": ""})

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content
        FROM notes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session["user_id"],))

    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"content": row[0]})
    else:
        return jsonify({"content": ""})

@app.route("/api/notes/save", methods=["POST"])
def api_save_notes():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    content = data.get("content", "")

    conn = get_db()
    cursor = conn.cursor()

    # Remove old notes for this user
    cursor.execute("""
        DELETE FROM notes
        WHERE user_id = ?
    """, (session["user_id"],))

    # Insert new note
    cursor.execute("""
        INSERT INTO notes (user_id, content, updated_at)
        VALUES (?, ?, ?)
    """, (
        session["user_id"],
        content,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/chat", methods=["GET"])
def api_get_chat():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, message, created_at
        FROM chat_messages
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    conn.close()

    messages = []
    for r in rows:
        messages.append({
            "username": r[0],
            "message": r[1],
            "time": r[2]
        })

    return jsonify(messages)

@app.route("/api/chat/send", methods=["POST"])
def api_send_chat():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"status": "error"})

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username
        FROM users
        WHERE id = ?
    """, (session["user_id"],))

    user = cursor.fetchone()
    username = user[0] if user else "unknown"

    cursor.execute("""
        INSERT INTO chat_messages (user_id, username, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        session["user_id"],
        username,
        message,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/kanban", methods=["GET"])
def api_get_kanban():
    if "user_id" not in session:
        return jsonify({})

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, link, column_name
        FROM kanban_cards
        WHERE user_id = ?
    """, (session["user_id"],))

    rows = cursor.fetchall()
    conn.close()

    data = {}
    for title, link, column in rows:
        if column not in data:
            data[column] = []
        data[column].append({
            "title": title,
            "link": link
        })

    return jsonify(data)

@app.route("/api/kanban/save", methods=["POST"])
def api_save_kanban():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 403

    data = request.json or {}

    conn = get_db()
    cursor = conn.cursor()

    # Clear old board for this user
    cursor.execute("""
        DELETE FROM kanban_cards
        WHERE user_id = ?
    """, (session["user_id"],))

    # Insert all cards
    for column, cards in data.items():
        for card in cards:
            cursor.execute("""
                INSERT INTO kanban_cards (user_id, title, link, column_name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                card.get("title"),
                card.get("link"),
                column,
                datetime.now().isoformat()
            ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


# ==============================
# FETCH JOB DETAILS LIVE
# ==============================
@app.route("/job-details")
def job_details():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL"}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        # Try common description containers
        selectors = [
            "[data-testid='job-description']",
            ".job-description",
            "#job-description",
            "article",
            "main"
        ]

        text = ""
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    break

        return jsonify({"description": text[:8000]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
