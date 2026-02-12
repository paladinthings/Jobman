import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

CSV_FILE = "jobs.csv"
SOURCE_FILE = "sources.txt"


# ==============================
# CSV STORAGE WITH SMART DEDUP
# ==============================
def save_to_csv(jobs):
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    text_fields = ["title", "company", "location", "source", "description"]
    combined.drop_duplicates(subset=text_fields, inplace=True)

    combined.to_csv(CSV_FILE, index=False)


# ==============================
# LOAD URL SOURCES
# ==============================
def load_sources():
    if not os.path.exists(SOURCE_FILE):
        print("sources.txt not found.")
        return []

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    return urls


# ==============================
# DESCRIPTION EXTRACTION
# ==============================
def extract_description(page):
    selectors = [
        "[data-testid='job-description']",
        ".job-description",
        "#job-description",
        "article",
        "main"
    ]

    for sel in selectors:
        el = page.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if len(text) > 200:
                return text[:5000]

    return ""


# ==============================
# SCRAPE SINGLE SEARCH PAGE
# ==============================
def scrape_search_page(page, search_url, max_jobs=15):
    jobs = []

    print(f"Loading: {search_url}")
    page.goto(search_url, timeout=60000)
    page.wait_for_timeout(3000)

    cards = page.query_selector_all("a[data-cy='job-link']")

    for card in cards[:max_jobs]:
        try:
            title = card.inner_text().strip()
            link = "https://www.jobs.ch" + card.get_attribute("href")

            print(f"Scraping job: {title}")

            job_page = page.context.new_page()
            job_page.goto(link, timeout=60000)
            job_page.wait_for_timeout(3000)

            description = extract_description(job_page)
            job_page.close()

            jobs.append({
                "title": title,
                "company": "",
                "location": "",
                "link": link,
                "source": "jobs.ch",
                "description": description,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        except Exception as e:
            print("Error scraping job:", e)

    return jobs


# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nRunning scraper at {datetime.now()}")

    urls = load_sources()
    if not urls:
        print("No sources found.")
        return

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for url in urls:
            all_jobs.extend(scrape_search_page(page, url))

        browser.close()

    if all_jobs:
        save_to_csv(all_jobs)
        print(f"Saved {len(all_jobs)} jobs.")
    else:
        print("No jobs found.")


# ==============================
# LOOP EVERY 4 HOURS
# ==============================
if __name__ == "__main__":
    while True:
        run_scraper()
        print("Sleeping for 4 hours...\n")
        time.sleep(4 * 60 * 60)
