from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

CSV_FILE = "jobs.csv"


def load_jobs():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=[
            "title", "company", "location",
            "link", "source", "description", "scraped_at"
        ])
    return pd.read_csv(CSV_FILE)


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
