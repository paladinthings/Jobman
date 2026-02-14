import sqlite3
import pandas as pd

DB_FILE = "jobs.db"
CSV_FILE = "jobs.csv"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

df = pd.read_csv(CSV_FILE)

inserted = 0
skipped = 0

for _, row in df.iterrows():
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs
            (title, company, location, link, source, description, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("title", ""),
            row.get("company", ""),
            row.get("location", ""),
            row.get("link", ""),
            row.get("source", ""),
            row.get("description", ""),
            row.get("scraped_at", "")
        ))

        if cursor.rowcount == 1:
            inserted += 1
        else:
            skipped += 1

    except Exception as e:
        print("Error inserting row:", e)

conn.commit()
conn.close()

print(f"Inserted: {inserted}")
print(f"Skipped duplicates: {skipped}")
