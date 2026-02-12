import time
import os
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

CSV_FILE = "jobs.csv"


# ==============================
# Export (csv @ root folder)
# ==============================
def save_to_csv(jobs):
    new_df = pd.DataFrame(jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    # Das hier eliminiert duplikate WENN der Inhalt ALLER Felder identisch ist
    text_fields = ["title", "company", "location", "description", "link", "source"]
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

description = card.inner_text().strip()

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "description": description,
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

######## jobagent ######

def scrape_jobagent(page):
    jobs = []

    category_urls = [
        "https://www.jobagent.ch/administration-verwaltung-jobs",
        "https://www.jobagent.ch/banken-versicherungen-jobs",
        "https://www.jobagent.ch/bau-handwerk-immobilien-jobs",
        "https://www.jobagent.ch/gastro-hotellerie-tourismus-jobs",
        "https://www.jobagent.ch/informatik-jobs",
        "https://www.jobagent.ch/marketing-kommunikation-medien-jobs",
        "https://www.jobagent.ch/medizin-gesundheitswesen-jobs",
        "https://www.jobagent.ch/non-profit-soziales-bildung-jobs",
        "https://www.jobagent.ch/finanz-und-rechnungswesen-jobs",
        "https://www.jobagent.ch/personal-organisation-bildung-jobs",
        "https://www.jobagent.ch/planung-design-jobs",
        "https://www.jobagent.ch/produktion-operations-jobs",
        "https://www.jobagent.ch/recht-beratung-jobs",
        "https://www.jobagent.ch/schutz-sicherheit-jobs",
        "https://www.jobagent.ch/transport-verkehr-jobs",
        "https://www.jobagent.ch/verkauf-einkauf-kundenberatung-jobs",
        "https://www.jobagent.ch/diverse-jobs"
    ]

    for url in category_urls:
        print(f"[jobagent] {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        cards = page.query_selector_all("a[href*='/job/']")
        for card in cards:
            title = card.inner_text().strip()
            link = card.get_attribute("href")

            if link and not link.startswith("http"):
                link = "https://www.jobagent.ch" + link

            jobs.append({
                "title": title,
                "company": "",
                "location": "",
                "description": title,
                "link": link,
                "source": "jobagent.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs

#####gov######

def scrape_be_jobs(page):
    jobs = []

    urls = [
        "https://www.jobs.sites.be.ch/de/start/jobs/jobs-fuer-berufserfahrene-berufseinsteigende-und-studierende.html",
        "https://www.jobs.sites.be.ch/de/start/jobs/lehrstellen-und-praktika-fuer-schuelerinnen-und-schueler.html",
        "https://www.jobs.sites.be.ch/de/start/jobs/jobs-fuer-lehrpersonen.html"
    ]

    for url in urls:
        print(f"[be.ch] {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)

        links = page.query_selector_all("a")

        for link_el in links:
            title = link_el.inner_text().strip()
            href = link_el.get_attribute("href")

            if not title or not href:
                continue

            if not href.startswith("http"):
                href = "https://www.jobs.sites.be.ch" + href

            if "job" in href.lower():
                jobs.append({
                    "title": title,
                    "company": "Kanton Bern",
                    "location": "Bern",
                    "description": title,
                    "link": href,
                    "source": "be.ch",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    return jobs

######### lehrer ######

def scrape_steze(page):
    jobs = []

    url = "https://www.steze.apps.be.ch/steze/results"
    print("[steze] scraping")

    page.goto(url, timeout=60000)
    page.wait_for_timeout(5000)

    links = page.query_selector_all("a")

    for link_el in links:
        title = link_el.inner_text().strip()
        href = link_el.get_attribute("href")

        if not title or not href:
            continue

        if "job" in href.lower():
            jobs.append({
                "title": title,
                "company": "Kanton Bern",
                "location": "Bern",
                "description": title,
                "link": href,
                "source": "steze.be.ch",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return jobs


##### ictjobs #####

def scrape_ictjobs(page):
    jobs = []

    url = "https://ictjobs.ch/?fs="
    print("[ictjobs] scraping")

    page.goto(url, timeout=60000)
    page.wait_for_timeout(5000)

    cards = page.query_selector_all("a[href*='/job/']")

    for card in cards:
        title = card.inner_text().strip()
        link = card.get_attribute("href")

        if link and not link.startswith("http"):
            link = "https://ictjobs.ch" + link

        jobs.append({
            "title": title,
            "company": "",
            "location": "",
            "description": title,
            "link": link,
            "source": "ictjobs.ch",
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return jobs

# ==============================
# Die Maschine
# ==============================
def run_scraper():
    print(f"\nRunning scraper at {datetime.now()}")

    keyword = ""
    location = ""

    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        all_jobs.extend(scrape_jobs_ch(page, keyword, location))
        all_jobs.extend(scrape_indeed(page, keyword, location))
        all_jobs.extend(scrape_jobscout24(page, keyword, location))

# New sources
        all_jobs.extend(scrape_jobagent(page))
        all_jobs.extend(scrape_be_jobs(page))
        all_jobs.extend(scrape_steze(page))
        all_jobs.extend(scrape_ictjobs(page))

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

