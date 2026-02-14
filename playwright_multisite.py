from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time
import os
import sqlite3

DB_FILE = "jobs.db"


def open_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    return conn, cursor


def save_job(conn, cursor, job):
    cursor.execute("""
        INSERT OR IGNORE INTO jobs
        (title, company, location, link, source, description, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("link", ""),
        job.get("source", ""),
        job.get("description", ""),
        job.get("scraped_at", "")
    ))

    conn.commit()



SOURCE_FILE = "sources.txt"


# ==============================
# LOAD SOURCES
# ==============================
def load_sources():
    sources = []

    if not os.path.exists(SOURCE_FILE):
        print("sources.txt not found.")
        return sources

    print("\nLoading sources...")

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            raw = line.strip()

            if not raw or raw.startswith("#"):
                continue

            parts = raw.split("|")
            if len(parts) != 3:
                print(f"Invalid line {line_number}: {raw}")
                continue

            site, keyword, location = parts
            sources.append((site.strip(), keyword.strip(), location.strip()))
            print(f"Loaded: {site} | {keyword} | {location}")

    print(f"Total sources loaded: {len(sources)}\n")
    return sources


# ==============================
# JOBS.CH SCRAPER
# ==============================
def scrape_jobs_ch(page, conn, cursor, keyword, location, max_pages=300):
    

    for p in range(1, max_pages + 1):
        url = f"https://www.jobs.ch/en/vacancies/?term={keyword}&location={location}&page={p}"
        print(f"[jobs.ch] {keyword}/{location} page {p}")

        page.goto(url)
        page.wait_for_timeout(2000)

        links = page.query_selector_all("a[data-cy='job-link']")
        print(f"Found {len(links)} jobs")

        if not links:
            break

        for link in links:
            title = link.inner_text().strip()
            href = link.get_attribute("href")
            if not href:
                continue
            
            job = {
                "title": title,
                "company": "",
                "location": location,
                "link": "https://www.jobs.ch" + href,
                "source": "jobs.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            save_job(conn, cursor, job)



    


# ==============================
# JOBSCOUT24 SCRAPER
# ==============================
def scrape_jobscout24(page, conn, cursor, keyword, location, max_pages=300):
    

    for p in range(1, max_pages + 1):
        url = f"https://www.jobscout24.ch/en/jobs?term={keyword}&location={location}&page={p}"
        print(f"[jobscout24] {keyword}/{location} page {p}")

        page.goto(url)
        page.wait_for_timeout(2000)

        links = page.query_selector_all("a[href*='/en/job/']")
        print(f"Found {len(links)} jobs")

        if not links:
            break

        for link in links:
            title = link.inner_text().strip()
            href = link.get_attribute("href")

            if not href:
                continue

            if not href.startswith("http"):
                href = "https://www.jobscout24.ch" + href

            job = {
                "title": title,
                "company": "",
                "location": location,
                "link": href,
                "source": "jobscout24.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            save_job(conn, cursor, job)

    


    


# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nBeep boop d maschine isch am dänke {datetime.now()}")

    sources = load_sources()
    if not sources:
        print("No valid sources found.\n")
        return

    conn, cursor = open_db()


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site, keyword, location in sources:
            if site == "jobs.ch":
                scrape_jobs_ch(page, conn, cursor, keyword, location)

            elif site == "jobscout24.ch":
                scrape_jobscout24(page, conn, cursor, keyword, location)

            elif site == "careerjet.ch":
                scrape_careerjet(page, conn, cursor, keyword, location)

            elif site == "indeed.ch":
                scrape_indeed(page, conn, cursor, keyword, location)

            

            else:
                print(f"Unknown site: {site}")

        browser.close()

    conn.close()
    print("Scraping complete. Jobs stored live in database.")



# ==============================
# LOOP EVERY 4 HOURS
# ==============================
if __name__ == "__main__":
    while True:
        run_scraper()
        print("D maschine geit ga schlafe -4 h...\n")
        time.sleep(4 * 60 * 60)
