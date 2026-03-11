"""
Apprenticeship Scraper
Searches findapprenticeship.service.gov.uk for matching listings.
Paginates through all results and stores new jobs in the database.

The gov.uk service aggregates apprenticeships from all UK employers
including NHS, civil service, private sector, etc.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urlencode, urljoin

from config import Config
from shared.logger import get_logger
import database

logger = get_logger("scraper")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

BASE_URL = Config.SEARCH_BASE_URL


def _build_search_url(keyword: str, page: int = 1) -> str:
    """Build the search URL for a given keyword and page number."""
    params = {
        "searchTerm": keyword,
        "location": Config.SEARCH_LOCATION,
        "distance": Config.SEARCH_DISTANCE_MILES,
        "pageNumber": page,
        "sort": "AgeDesc",  # newest first
    }
    return f"{BASE_URL}/apprenticeships/search?{urlencode(params)}"


def _parse_listing_card(card: BeautifulSoup) -> Optional[dict]:
    """Parse a single job card from the search results page."""
    try:
        # Title + URL
        title_tag = card.select_one("h2 a, .vacancy-title a, [data-automation='vacancy-title']")
        if not title_tag:
            title_tag = card.find("a", href=True)
        if not title_tag:
            return None

        title = title_tag.get_text(strip=True)
        relative_url = title_tag.get("href", "")
        url = urljoin(BASE_URL, relative_url)

        # Company
        company_tag = card.select_one(
            ".employer, [data-automation='vacancy-employer'], .vacancy-employer"
        )
        company = company_tag.get_text(strip=True) if company_tag else "Unknown Employer"

        # Location
        location_tag = card.select_one(
            ".location, [data-automation='vacancy-location'], .vacancy-location"
        )
        location = location_tag.get_text(strip=True) if location_tag else ""

        # Wage
        wage_tag = card.select_one(
            ".wage, [data-automation='vacancy-wage'], .vacancy-wage"
        )
        wage = wage_tag.get_text(strip=True) if wage_tag else ""

        # Closing date
        closing_tag = card.select_one(
            ".closing-date, [data-automation='closing-date'], .vacancy-closing-date"
        )
        closing_date = closing_tag.get_text(strip=True) if closing_tag else ""

        # Apprenticeship level
        level_tag = card.select_one(
            ".apprenticeship-level, [data-automation='apprenticeship-level']"
        )
        level = level_tag.get_text(strip=True) if level_tag else ""

        # Description snippet
        desc_tag = card.select_one(".description, .vacancy-description, p.body-m")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        return {
            "title": title,
            "url": url,
            "company": company,
            "location": location,
            "wage": wage,
            "closing_date": closing_date,
            "apprenticeship_level": level,
            "description_snippet": description,
        }

    except Exception as e:
        logger.debug(f"Failed to parse listing card: {e}")
        return None


def _get_total_pages(soup: BeautifulSoup) -> int:
    """Extract total number of pages from pagination."""
    try:
        # Look for pagination or result count
        result_tag = soup.select_one(".search-results-count, [data-automation='vacancy-count']")
        if result_tag:
            text = result_tag.get_text(strip=True)
            # e.g. "Showing 1 to 10 of 342 results"
            import re
            match = re.search(r"of (\d[\d,]*)", text)
            if match:
                total = int(match.group(1).replace(",", ""))
                return (total // 10) + 1

        # Fallback: count pagination links
        pages = soup.select(".pagination a, [data-automation='pagination'] a")
        if pages:
            nums = []
            for p in pages:
                try:
                    nums.append(int(p.get_text(strip=True)))
                except ValueError:
                    pass
            return max(nums) if nums else 1

    except Exception:
        pass
    return 1


def _matches_level_filter(job: dict) -> bool:
    """Check if the job matches the configured apprenticeship level filter."""
    if not Config.SEARCH_LEVELS:
        return True  # No filter = include all
    level = job.get("apprenticeship_level", "").lower()
    return any(l.lower() in level for l in Config.SEARCH_LEVELS)


def scrape_keyword(keyword: str) -> List[dict]:
    """Scrape all pages for a single keyword and return new job listings."""
    logger.info(f"Scraping keyword: '{keyword}' in {Config.SEARCH_LOCATION}...")
    new_jobs = []
    page = 1
    total_pages = None

    session = requests.Session()
    session.headers.update(HEADERS)

    while True:
        url = _build_search_url(keyword, page)
        logger.debug(f"  Page {page}: {url}")

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"  Request failed for page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        if total_pages is None:
            total_pages = _get_total_pages(soup)
            logger.info(f"  Found ~{total_pages} page(s) of results.")

        # Find all job cards (gov.uk uses article tags or li items)
        cards = soup.select(
            "article.vacancy-details-link, li.vacancy, .vacancy-card, "
            "[data-automation='vacancy-result'], article[class*='vacancy']"
        )

        if not cards:
            # Fallback: grab all article tags
            cards = soup.find_all("article")

        if not cards:
            logger.debug(f"  No cards found on page {page} — may have reached the end.")
            break

        for card in cards:
            job = _parse_listing_card(card)
            if not job:
                continue
            if not _matches_level_filter(job):
                continue
            if database.is_seen(job["url"]):
                continue

            database.add_job(**job)
            new_jobs.append(job)
            logger.info(f"  + Found: {job['title']} at {job['company']} ({job['location']})")

        if page >= total_pages:
            break

        page += 1
        time.sleep(1.5)  # Be polite to the server

    return new_jobs


def scrape_all_keywords() -> List[dict]:
    """Scrape all configured keywords and return all new jobs found."""
    all_new = []
    for keyword in Config.SEARCH_KEYWORDS:
        keyword = keyword.strip()
        if not keyword:
            continue
        new = scrape_keyword(keyword)
        all_new.extend(new)
        time.sleep(2)

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for job in all_new:
        if job["url"] not in seen_urls:
            seen_urls.add(job["url"])
            unique.append(job)

    logger.info(f"Scraping complete — {len(unique)} new listing(s) found across all keywords.")
    return unique
