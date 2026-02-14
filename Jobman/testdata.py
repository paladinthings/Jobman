from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time
import os
import sqlite3

DB_FILE = "jobs.db"


def save_jobs_to_db(jobs):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for job in jobs:
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
    conn.close()

SOURCE_FILE = "sources_test.txt"


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
def scrape_jobs_ch(page, keyword, location, max_pages=1):
    jobs = []

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

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "link": "https://www.jobs.ch" + href,
                "source": "jobs.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# JOBSCOUT24 SCRAPER
# ==============================
def scrape_jobscout24(page, keyword, location, max_pages=200):
    jobs = []

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

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "link": href,
                "source": "jobscout24.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# INDEED SCRAPER
# ==============================
def scrape_indeed(page, keyword, location, max_pages=200):
    jobs = []

    for p in range(max_pages):
        start = p * 10
        url = f"https://ch.indeed.com/jobs?q={keyword}&l={location}&start={start}"
        print(f"[indeed] {keyword}/{location} page {p+1}")

        page.goto(url)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("div.job_seen_beacon")
        print(f"Found {len(cards)} jobs")

        if not cards:
            break

        for card in cards:
            title_el = card.query_selector("h2 a span")
            company_el = card.query_selector("[data-testid='company-name']")
            location_el = card.query_selector("[data-testid='text-location']")
            link_el = card.query_selector("h2 a")

            title = title_el.inner_text().strip() if title_el else ""
            company = company_el.inner_text().strip() if company_el else ""
            job_loc = location_el.inner_text().strip() if location_el else ""
            href = link_el.get_attribute("href") if link_el else ""

            if not title or not href:
                continue

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "link": "https://ch.indeed.com" + href,
                "source": "indeed.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


# ==============================
# CAREERJET SCRAPER
# ==============================
def scrape_careerjet(page, keyword, location, max_pages=1):
    jobs = []

    for p in range(1, max_pages + 1):
        url = f"https://www.careerjet.ch/jobs?s={keyword}&l={location}&p={p}"
        print(f"[careerjet] {keyword}/{location} page {p}")

        page.goto(url)
        page.wait_for_timeout(3000)

        job_cards = page.query_selector_all("article.job")
        print(f"Found {len(job_cards)} jobs")

        if not job_cards:
            break

        for card in job_cards:
            title_el = card.query_selector("h2 a")
            title = ""
            link = ""

            if title_el:
                title = title_el.inner_text().strip()
                href = title_el.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        link = href
                    else:
                        link = "https://www.careerjet.ch" + href

            company_el = card.query_selector(".company")
            company = company_el.inner_text().strip() if company_el else ""

            location_el = card.query_selector(".location")
            location_text = location_el.inner_text().strip() if location_el else ""

            jobs.append({
                "title": title,
                "company": company,
                "location": location_text,
                "link": link,
                "source": "careerjet.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        time.sleep(2)

    return jobs



# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nBeep boop d maschine isch am dänke {datetime.now()}")

    sources = load_sources()
    if not sources:
        print("No valid sources found.\n")
        return

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for site, keyword, location in sources:
            if site == "jobs.ch":
                all_jobs.extend(scrape_jobs_ch(page, keyword, location))

            elif site == "jobscout24.ch":
                all_jobs.extend(scrape_jobscout24(page, keyword, location))

            elif site == "careerjet.ch":
                all_jobs.extend(scrape_careerjet(page, keyword, location))

            elif site == "indeed.ch":
                all_jobs.extend(scrape_indeed(page, keyword, location))

            else:
                print(f"Unknown site: {site}")

        browser.close()

    if all_jobs:
        save_jobs_to_db(all_jobs)
        print(f"{len(all_jobs)} jobs saved to database.")
    
    else:
        print("No jobs found.")



# ==============================
# LOOP EVERY 4 HOURS
# ==============================
if __name__ == "__main__":
    while True:
        run_scraper()
        print("D maschine geit ga schlafe -4 h...\n")
        time.sleep(4 * 60 * 60)
