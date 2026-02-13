from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time

BASE_URL = "https://www.careerjet.ch/jobs"
KEYWORD = ""
LOCATION = ""


def scrape_careerjet(keyword, location, max_pages=3):
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(1, max_pages + 1):
            url = f"{BASE_URL}?s={keyword}&l={location}&p={page_num}"
            print(f"[careerjet] Opening {url}")

            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            job_cards = page.query_selector_all("article.job")
            print(f"Found {len(job_cards)} jobs on page {page_num}")

            if not job_cards:
                break

            for card in job_cards:
                # Title and link
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

                # Company
                company_el = card.query_selector(".company")
                company = company_el.inner_text().strip() if company_el else ""

                # Location
                location_el = card.query_selector(".location")
                location_text = location_el.inner_text().strip() if location_el else ""

                # Debug print
                print("→", title)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "link": link,
                    "source": "careerjet.ch",
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            time.sleep(2)

        browser.close()

    return jobs


def save_to_csv(jobs, filename="careerjet_jobs.csv"):
    df = pd.DataFrame(jobs)
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} jobs to {filename}")


if __name__ == "__main__":
    jobs = scrape_careerjet(KEYWORD, LOCATION, max_pages=3)
    save_to_csv(jobs)
