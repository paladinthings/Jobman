import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

CSV_FILE = "jobs.csv"


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


def extract_description(page):
    """Try multiple selectors for job descriptions."""
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
                return text[:5000]  # limit size

    return ""


def scrape_jobs(page, keyword, location):
    jobs = []
    url = f"https://www.jobs.ch/en/vacancies/?term={keyword}&location={location}"

    page.goto(url, timeout=60000)
    page.wait_for_timeout(3000)

    cards = page.query_selector_all("a[data-cy='job-link']")

    for card in cards[:10]:  # limit for performance
        title = card.inner_text().strip()
        link = "https://www.jobs.ch" + card.get_attribute("href")

        # open job page
        job_page = page.context.new_page()
        job_page.goto(link, timeout=60000)
        job_page.wait_for_timeout(3000)

        description = extract_description(job_page)
        job_page.close()

        jobs.append({
            "title": title,
            "company": "",
            "location": location,
            "link": link,
            "source": "jobs.ch",
            "description": description,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return jobs


def run_scraper():
    print(f"\nRunning scraper at {datetime.now()}")

    keyword = "engineer"
    location = "Zurich"

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        all_jobs.extend(scrape_jobs(page, keyword, location))

        browser.close()

    if all_jobs:
        save_to_csv(all_jobs)
        print(f"Saved {len(all_jobs)} jobs.")
    else:
        print("No jobs found.")


if __name__ == "__main__":
    while True:
        run_scraper()
        print("Sleeping for 4 hours...\n")
        time.sleep(4 * 60 * 60)
