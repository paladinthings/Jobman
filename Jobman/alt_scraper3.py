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
            site = site.strip()
            keyword = keyword.strip()
            location = location.strip()

            sources.append((site, keyword, location))
            print(f"Loaded: {site} | {keyword} | {location}")

    print(f"Total sources loaded: {len(sources)}\n")
    return sources


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

        print(f"[jobs.ch] {keyword} / {location} Page {page}")
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("a[data-cy='job-link']")
        if not cards:
            print("No more results.")
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

        time.sleep(1)

    print(f"[jobs.ch] Found {len(jobs)} jobs\n")
    return jobs


# ==============================
# INDEED SCRAPER
# ==============================
def scrape_indeed(keyword, location="", max_pages=5):
    base_url = "https://ch.indeed.com/jobs"
    jobs = []

    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(max_pages):
        start = page * 10

        params = {
            "q": keyword,
            "start": start
        }

        if location:
            params["l"] = location

        print(f"[indeed] {keyword} / {location or 'ANY'} Page {page + 1}")

        response = session.get(base_url, params=params, timeout=30)

        print("Status:", response.status_code)

        soup = BeautifulSoup(response.text, "html.parser")

        job_cards = soup.select("div.job_seen_beacon")
        print(f"Found {len(job_cards)} job cards")

        if not job_cards:
            break

        for card in job_cards:
            title_el = card.select_one("h2 a span")
            company_el = card.select_one("[data-testid='company-name']")
            location_el = card.select_one("[data-testid='text-location']")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            job_loc = location_el.get_text(strip=True) if location_el else ""

            link_el = card.select_one("h2 a")
            link = ""
            if link_el:
                href = link_el.get("href")
                if href:
                    link = "https://ch.indeed.com" + href

            if title:
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "link": link,
                    "source": "indeed.ch",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        time.sleep(2)

    print(f"[indeed] Found {len(jobs)} jobs\n")
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

        print(f"[jobscout24] {keyword} / {location} Page {page}")
        response = requests.get(base_url, headers=HEADERS, params=params, timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.select("a[href*='/en/job/']")
        if not cards:
            print("No more results.")
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

        time.sleep(1)

    print(f"[jobscout24] Found {len(jobs)} jobs\n")
    return jobs

# ==============================
# JOBAGENT SCRAPER
# ==============================
def scrape_jobagent(keyword, location, max_pages=5):
    """
    For jobagent:
    keyword = category slug (e.g. administration-verwaltung)
    location is ignored (site does not support it in URL)
    """
    base_url = f"https://www.jobagent.ch/{keyword}-jobs"
    jobs = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"[jobagent] {keyword} Page {page}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"Error loading page: {e}")
            break

        job_links = soup.select("a[href*='/job/']")

        if not job_links:
            print("No more results.")
            break

        for link_el in job_links:
            title = link_el.get_text(strip=True)
            link = link_el.get("href")

            if not link:
                continue

            if not link.startswith("http"):
                link = "https://www.jobagent.ch" + link

            # Extract surrounding text for company/location
            parent = link_el.parent
            text_block = parent.get_text(" ", strip=True)

            company = ""
            job_loc = ""

            parts = text_block.split(title)
            if len(parts) > 1:
                remainder = parts[1].strip()
                pieces = remainder.split()
                if len(pieces) > 1:
                    job_loc = pieces[0]
                    company = " ".join(pieces[1:])

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "link": link,
                "source": "jobagent.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        time.sleep(1)

    print(f"[jobagent] Found {len(jobs)} jobs\n")
    return jobs


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

    text_fields = ["title", "company", "location", "source"]
    combined.drop_duplicates(subset=text_fields, inplace=True)

    combined.to_csv(CSV_FILE, index=False)
    print(f"CSV updated. Total entries: {len(combined)}\n")


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
    for site, keyword, location in sources:
        if site == "jobs.ch":
            all_jobs.extend(scrape_jobs_ch(keyword, location))
        elif site == "indeed.ch":
            all_jobs.extend(scrape_indeed(keyword, location))
        elif site == "jobscout24.ch":
            all_jobs.extend(scrape_jobscout24(keyword, location))
        elif site == "jobagent.ch":
            all_jobs.extend(scrape_jobagent(keyword, location))
        else:
            print(f"Unknown site: {site}")

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
