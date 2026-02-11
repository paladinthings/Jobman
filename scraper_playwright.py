import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

CSV_FILE = "jobs.csv"


# ==============================
# CSV STORAGE
# ==============================
def save_to_csv(jobs):
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    # Only remove duplicates if ALL text fields match
    text_fields = ["title", "company", "location", "link", "source"]
    combined.drop_duplicates(subset=text_fields, inplace=True)

    combined.to_csv(CSV_FILE, index=False)


# ==============================
# JOBS.CH
# ==============================
def scrape_jobs_ch(page, keyword, location, max_pages=100):
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

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "link": link,
                "source": "jobs.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# INDEED CH
# ==============================
def scrape_indeed(page, keyword, location, max_pages=100):
    jobs = []

    for p in range(max_pages):
        start = p * 10
        url = f"https://ch.indeed.com/jobs?q={keyword}&l={location}&start={start}"
        print(f"[indeed] Page {p + 1}")

        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        cards = page.query_selector_all("a.tapItem")
        if not cards:
            break

        for card in cards:
            title_el = card.query_selector("h2 span")
            company_el = card.query_selector(".companyName")
            location_el = card.query_selector(".companyLocation")

            title = title_el.inner_text().strip() if title_el else ""
            company = company_el.inner_text().strip() if company_el else ""
            job_loc = location_el.inner_text().strip() if location_el else ""

            link = card.get_attribute("href")
            if link and not link.startswith("http"):
                link = "https://ch.indeed.com" + link

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "link": link,
                "source": "indeed.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# JOBSCOUT24
# ==============================
def scrape_jobscout24(page, keyword, location, max_pages=100):
    jobs = []

    for p in range(1, max_pages + 1):
        url = f"https://www.jobscout24.ch/en/jobs?term={keyword}&location={location}&page={p}"
        print(f"[jobscout24] Page {p}")

        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        cards = page.query_selector_all("a[href*='/en/job/']")
        if not cards:
            break

        for card in cards:
            title = card.inner_text().strip()
            link = card.get_attribute("href")

            if link and not link.startswith("http"):
                link = "https://www.jobscout24.ch" + link

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "link": link,
                "source": "jobscout24.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nRunning scraper at {datetime.now()}")

    keyword = "ICT"
    location = ""

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        all_jobs.extend(scrape_jobs_ch(page, keyword, location))
        all_jobs.extend(scrape_indeed(page, keyword, location))
        all_jobs.extend(scrape_jobscout24(page, keyword, location))

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

