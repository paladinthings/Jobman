from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

CSV_FILE = "jobs.csv"


def load_jobs():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["title", "company", "location", "link", "source", "scraped_at"])
    return pd.read_csv(CSV_FILE)


@app.route("/")
def index():
    df = load_jobs()

    keyword = request.args.get("keyword", "").lower()
    location = request.args.get("location", "").lower()
    source = request.args.get("source", "").lower()
    desc_search = request.args.get("description", "").lower()

    if keyword:
        df = df[df["title"].str.lower().str.contains(keyword, na=False)]

    if location:
        df = df[df["location"].str.lower().str.contains(location, na=False)]

    if source:
        df = df[df["source"].str.lower().str.contains(source, na=False)]

    if desc_search:
        df = df[df["description"].str.lower().str.contains(desc_search, na=False)]

    jobs = df.sort_values(by="scraped_at", ascending=False).to_dict(orient="records")

    return render_template("index.html", jobs=jobs)


if __name__ == "__main__":
    app.run(debug=True)
