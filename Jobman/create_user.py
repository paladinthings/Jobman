import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_FILE = "jobs.db"

username = "Daniel"
password = "user"   # change later
role = "user"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
INSERT INTO users (username, password_hash, role, created_at)
VALUES (?, ?, ?, ?)
""", (
    username,
    generate_password_hash(password),
    role,
    datetime.now().isoformat()
))

conn.commit()
conn.close()

print("user created.")
