from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time

BASE_URL = "https://www.jobagent.ch/"


def scrape_jobagent(max_pages=3):
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"{BASE_URL}?page={page_num}"
            print(f"[jobagent] Opening {url}")

            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            job_items = page.query_selector_all("li.item")
            print(f"Found {len(job_items)} job items")

            if not job_items:
                break

            for item in job_items:
                title_el = item.query_selector(".jobtitle")
                link_el = item.query_selector("a.title")
                company_el = item.query_selector(".company a")
                location_el = item.query_selector(".location")

                title = title_el.inner_text().strip() if title_el else ""
                link = link_el.get_attribute("href") if link_el else ""
                company = company_el.inner_text().strip() if company_el else ""
                location = location_el.inner_text().strip() if location_el else ""

                if not title or not link:
                    continue

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "source": "jobagent.ch",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            time.sleep(2)

        browser.close()

    return jobs


def save_to_csv(jobs, filename="jobagent_jobs.csv"):
    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} jobs to {filename}")


if __name__ == "__main__":
    jobs = scrape_jobagent(max_pages=3)
    save_to_csv(jobs)
