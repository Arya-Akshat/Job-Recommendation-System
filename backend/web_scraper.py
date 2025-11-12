"""web_scraper.py

Clean implementation of a web scraper to fetch job postings and update
data/job_data.csv. Exposes fetch_and_update_jobs() which returns the
number of newly added jobs.
"""

import os
from typing import List, Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup


def _parse_job_element(li) -> Dict[str, str]:
    """Parse a single <li> job element into the expected job dict."""
    # Title and link
    a = li.find('a')
    if not a or not a.get('href'):
        return {}

    title = a.get_text(strip=True)
    link = a.get('href')
    if link.startswith('/'):
        link = f"https://jobs.python.org{link}"

    # Company
    company = ''
    comp_span = li.find('span', class_='listing-company-name')
    if comp_span:
        company = comp_span.get_text(separator=' ', strip=True)

    # Location
    location_el = li.find('span', class_='listing-location')
    location = location_el.get_text(strip=True) if location_el else ''

    # Job type
    job_type_el = li.find('span', class_='listing-job-type')
    job_type = job_type_el.get_text(strip=True) if job_type_el else ''

    # Posted date
    posted = ''
    posted_el = li.find('span', class_='listing-posted')
    if posted_el and posted_el.find('time'):
        posted = posted_el.find('time').get_text(strip=True)

    return {
        'Title': title,
        'Company': company,
        'Location': location,
        'Job Type': job_type,
        'Posted Date': posted,
        'Link': link,
        'Description': '',
        'Detail URL': link,
        'Company Name': company,
        'Company Logo': '',
        'Company Apply Url': '',
        'Processed Job Description': '',
        'Required Experience': 0,
        'skills': '',
    }


def fetch_and_update_jobs() -> int:
    """Scrape jobs.python.org and update data/job_data.csv.

    Returns the number of newly added jobs.
    """
    repo_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(repo_root, 'data')
    job_data_path = os.path.join(data_dir, 'job_data.csv')

    try:
        existing_df = pd.read_csv(job_data_path)
    except FileNotFoundError:
        existing_df = pd.DataFrame()

    url = 'https://jobs.python.org/'
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error fetching jobs: {e}')
        return 0

    soup = BeautifulSoup(resp.content, 'html.parser')
    container = soup.find('ol', class_='list-recent-jobs')
    if not container:
        print('Job list container not found on the page')
        return 0

    jobs: List[Dict[str, str]] = []
    for li in container.find_all('li'):
        parsed = _parse_job_element(li)
        if parsed:
            jobs.append(parsed)

    if not jobs:
        print('No jobs scraped')
        return 0

    new_df = pd.DataFrame(jobs)
    if not existing_df.empty:
        combined = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined = new_df

    deduped = combined.drop_duplicates(subset=['Link'], keep='first')
    new_count = max(0, len(deduped) - len(existing_df))

    os.makedirs(data_dir, exist_ok=True)
    deduped.to_csv(job_data_path, index=False)

    print(f'Scraped {len(new_df)} jobs, added {new_count} new ones')
    return new_count


if __name__ == '__main__':
    print(fetch_and_update_jobs())