import asyncio
from playwright.sync_api import sync_playwright
import logging
import time

def parse_competitions_from_page(page):
    competitions = []
    # Wait for competition entries to load
    page.wait_for_selector('div.middle-wrapper', timeout=10000)
    comps = page.query_selector_all('div.middle-wrapper')
    for comp in comps:
        # Title and link
        h3 = comp.query_selector('h3')
        a = h3.query_selector('a') if h3 else None
        title = a.inner_text().strip() if a else None
        link = a.get_attribute('href') if a else None
        # Ages
        ages_p = comp.query_selector('p.ages span')
        ages = ages_p.inner_text().strip() if ages_p else None
        # Categories
        cat_p = comp.query_selector('p.categories span')
        categories = cat_p.inner_text().strip() if cat_p else None
        competitions.append({
            'Title': title,
            'Link': link,
            'Ages': ages,
            'Categories': categories,
        })
    logging.info(f"Parsed {len(competitions)} competitions from current page.")
    return competitions

def scrape_ics_competitions_playwright(max_pages=56, headless=False):
    competitions = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page_url = "https://www.competitionsciences.org/competitions/"
        page_count = 0
        while page_url and (max_pages is None or page_count < max_pages):
            logging.info(f"Navigating to: {page_url}")
            page.goto(page_url, timeout=60000)
            comps = parse_competitions_from_page(page)
            competitions.extend(comps)
            # Find next page
            next_a = page.query_selector('div.nav-links a.next.page-numbers')
            next_link = next_a.get_attribute('href') if next_a else None
            page_url = next_link
            page_count += 1
            time.sleep(1)
        browser.close()
    logging.info(f"Scraping complete. Total competitions: {len(competitions)}")
    return competitions 