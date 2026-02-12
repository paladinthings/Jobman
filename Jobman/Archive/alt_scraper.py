import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CSV_FILE = "jobs.csv"


# ==============================
# JOBS.CH SCRAPER
# ==============================
def scrape_jobs_ch(keyword, location, max_pages=50):
    base_url = "https://www.jobs.ch/en/vacancies/"
    jobs = []

    for page in range(1, max_pages + 1):
        params = {
            "term": keyword,
            "location": location,
            "page": page
        }

        print(f"[jobs.ch] Page {page}")
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("a[data-cy='job-link']")
        if not cards:
            break

        for card in cards:
            title = card.get_text(strip=True)
            link = "https://www.jobs.ch" + card.get("href", "")

            jobs.append({
                "title": title,
                "company": "",
                "location": location,
                "link": link,
                "source": "jobs.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        time.sleep(2)

    return jobs


# ==============================
# INDEED CH SCRAPER
# ==============================
def scrape_indeed(keyword, location, max_pages=50):
    base_url = "https://ch.indeed.com/"
    jobs = []

    for page in range(max_pages):
        start = page * 10

        params = {
            "q": keyword,
            "l": location,
            "start": start
        }

        print(f"[indeed] Page {page + 1}")
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("a.tapItem")
        if not cards:
            break

        for card in cards:
            title_el = card.select_one("h2 span")
            company_el = card.select_one(".companyName")
            location_el = card.select_one(".companyLocation")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            job_loc = location_el.get_text(strip=True) if location_el else ""

            link = "https://ch.indeed.com" + card.get("href", "")

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "link": link,
                "source": "indeed.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        time.sleep(2)

    return jobs


# ==============================
# JOBSCOUT24 SCRAPER
# ==============================
def scrape_jobscout24(keyword, location, max_pages=50):
    base_url = "https://www.jobscout24.ch/en/jobs"
    jobs = []

    for page in range(1, max_pages + 1):
        params = {
            "term": keyword,
            "location": location,
            "page": page
        }

        print(f"[jobscout24] Page {page}")
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("a[href*='/en/job/']")
        if not cards:
            break

        for card in cards:
            title = card.get_text(strip=True)
            link = card.get("href")

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

        time.sleep(2)

    return jobs


# ==============================
# CSV STORAGE
# ==============================
def save_to_csv(jobs):
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.drop_duplicates(subset="link", inplace=True)
        combined.to_csv(CSV_FILE, index=False)
    else:
        new_df.to_csv(CSV_FILE, index=False)


# ==============================
# MAIN SCRAPER
# ==============================
def run_scraper():
    print(f"\nBeep boop d maschine isch am dänke {datetime.now()}")

    keyword = "ICT"
    location = "Bern"

    all_jobs = []

    all_jobs.extend(scrape_jobs_ch(keyword, location))
    all_jobs.extend(scrape_indeed(keyword, location))
    all_jobs.extend(scrape_jobscout24(keyword, location))

    if all_jobs:
        save_to_csv(all_jobs)
        print(f"{len(all_jobs)} jobs exportiert.")
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