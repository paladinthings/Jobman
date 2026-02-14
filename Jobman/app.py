from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

DB_FILE = "jobs.db"

def get_db():
    return sqlite3.connect(DB_FILE)

def load_jobs():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df

@app.route("/")
def index():
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
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT job_link, title FROM favorites")
        rows = cursor.fetchall()
        conn.close()

        data = [{"link": r[0], "title": r[1]} for r in rows]
        return jsonify(data)

    except Exception as e:
        print("Favorites GET error:", e)
        return jsonify([]), 500


@app.route("/api/favorites/add", methods=["POST"])
def api_add_favorite():
    try:
        data = request.json
        link = data.get("link")
        title = data.get("title")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO favorites (job_link, title, created_at)
            VALUES (?, ?, ?)
        """, (link, title, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        print("Favorites ADD error:", e)
        return jsonify({"status": "error"}), 500


@app.route("/api/favorites/remove", methods=["POST"])
def api_remove_favorite():
    try:
        data = request.json
        link = data.get("link")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE job_link = ?", (link,))
        conn.commit()
        conn.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        print("Favorites REMOVE error:", e)
        return jsonify({"status": "error"}), 500

@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, due, details, done
        FROM tasks
        ORDER BY created_at DESC
    """)
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
    data = request.json

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (title, due, details, done, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
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
    data = request.json
    task_id = data.get("id")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/tasks/toggle", methods=["POST"])
def api_toggle_task():
    data = request.json
    task_id = data.get("id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET done = CASE WHEN done = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/api/notes", methods=["GET"])
def api_get_notes():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM notes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"content": row[0]})
    else:
        return jsonify({"content": ""})

@app.route("/api/notes/save", methods=["POST"])
def api_save_notes():
    data = request.json
    content = data.get("content", "")

    conn = get_db()
    cursor = conn.cursor()

    # Clear old note
    cursor.execute("DELETE FROM notes")

    # Insert new note
    cursor.execute("""
        INSERT INTO notes (content, updated_at)
        VALUES (?, ?)
    """, (content, datetime.now().isoformat()))

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
