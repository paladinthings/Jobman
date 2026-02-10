import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os

BASE_URL = "https://www.jobs.ch/en/vacancies/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CSV_FILE = "jobs.csv"


def build_url(keyword="", location="", page=1):
    params = []

    if keyword:
        params.append(f"term={keyword}")

    if location:
        params.append(f"location={location}")

    if page > 1:
        params.append(f"page={page}")

    query = "&".join(params)
    return f"{BASE_URL}?{query}"


def scrape_page(url):
    """
    Scrape a single results page.
    """
    response = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []

    for card in soup.select("a[data-cy='job-link']"):
        title = card.get_text(strip=True)
        link = "https://www.jobs.ch" + card.get("href", "")

        container = card.find_parent("article")
        company = ""
        location = ""

        if container:
            company_el = container.select_one("[data-cy='company-name']")
            location_el = container.select_one("[data-cy='job-location']")

            if company_el:
                company = company_el.get_text(strip=True)

            if location_el:
                location = location_el.get_text(strip=True)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return jobs


def scrape_all(keyword="", location="", max_pages=5):
    """
    Scrape multiple pages.
    """
    all_jobs = []

    for page in range(1, max_pages + 1):
        url = build_url(keyword, location, page)
        print(f"Scraping: {url}")

        jobs = scrape_page(url)

        if not jobs:
            print("No more jobs found. Stopping pagination.")
            break

        all_jobs.extend(jobs)

        time.sleep(2)

    return all_jobs


def save_to_csv(jobs):
    """
    Save jobs to CSV with deduplication.
    """
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.drop_duplicates(subset="link", inplace=True)
        combined.to_csv(CSV_FILE, index=False)
    else:
        new_df.to_csv(CSV_FILE, index=False)


def run_scraper():
    """
    Main scraper function.
    """
    print(f"\nRunning scraper at {datetime.now()}")

    jobs = scrape_all(
        keyword="engineer",   # change filter here
        location="Zurich",    # change filter here
        max_pages=5           # adjust as needed
    )

    if jobs:
        save_to_csv(jobs)
        print(f"Saved {len(jobs)} jobs.")
    else:
        print("No jobs found.")


if __name__ == "__main__":
    while True:
        run_scraper()

        print("Sleeping for 4 hours...\n")
        time.sleep(4 * 60 * 60) 

