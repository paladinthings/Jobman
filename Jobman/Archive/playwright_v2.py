import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

CSV_FILE = "jobs.csv"


# ==============================
# CSV STORAGE WITH SMART DEDUPE
# ==============================
def save_to_csv(jobs):
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    # Only remove duplicates if ALL text fields match
    text_fields = ["title", "company", "location", "description", "link", "source"]
    combined.drop_duplicates(subset=text_fields, inplace=True)

    combined.to_csv(CSV_FILE, index=False)


# ==============================
# JOBS.CH
# ==============================
def scrape_jobs_ch(page, keyword, location, max_pages=3):
    jobs = []

    for p in range(1, max_pages + 1):
        url = f"https://www.jobs.ch/en/vacancies/?term={keyword}&location={location}&page={p}"
        print(f"[jobs.ch] Page {p}")

        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("a[data-cy='job-link']")
        if not cards:
            break

        for card in cards:
            title = card.inner_text().strip()
            link = "https://www.jobs.ch" + card.get_attribute("href")
            description = title

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "description": description,
                "link": link,
                "source": "jobs.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs

# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nRunning scraper at {datetime.now()}")

    keyword = "ICT"
    location = "Berne"

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        all_jobs.extend(scrape_jobs_ch(page, keyword, location))




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
