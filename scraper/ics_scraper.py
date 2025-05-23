import requests
from bs4 import BeautifulSoup
import logging

ICS_COMPETITIONS_URL = "https://www.competitionsciences.org/competitions/"

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

def parse_competitions_from_soup(soup):
    competitions = []
    for comp in soup.find_all('div', class_='middle-wrapper'):
        # Title and link
        h3 = comp.find('h3')
        a = h3.find('a') if h3 else None
        title = a.get_text(strip=True) if a else None
        link = a['href'] if a and a.has_attr('href') else None
        # Ages
        ages_p = comp.find('p', class_='ages')
        ages = ages_p.find('span').get_text(strip=True) if ages_p and ages_p.find('span') else None
        # Categories
        cat_p = comp.find('p', class_='categories')
        categories = cat_p.find('span').get_text(strip=True) if cat_p and cat_p.find('span') else None
        competitions.append({
            'Title': title,
            'Link': link,
            'Ages': ages,
            'Categories': categories,
        })
    logger.info(f"Parsed {len(competitions)} competitions from current page.")
    return competitions

def scrape_ics_competitions(max_pages=56):
    try:
        competitions = []
        page_url = ICS_COMPETITIONS_URL
        page_count = 0
        while page_url and (max_pages is None or page_count < max_pages):
            logger.info(f"Fetching page: {page_url}")
            resp = requests.get(page_url, headers=HEADERS)
            logger.info(f"Page status: {resp.status_code}")
            if resp.status_code != 200:
                logger.error(f"Failed to fetch page: {page_url} (status {resp.status_code})")
                break
            soup = BeautifulSoup(resp.text, 'lxml')
            comps = parse_competitions_from_soup(soup)
            competitions.extend(comps)
            logger.info(f"Total competitions so far: {len(competitions)}")
            # Find next page
            nav = soup.find('div', class_='nav-links')
            next_link = None
            if nav:
                next_a = nav.find('a', class_='next')
                if next_a and next_a.has_attr('href'):
                    next_link = next_a['href']
            page_url = next_link
            page_count += 1
        logger.info(f"Scraping complete. Total competitions: {len(competitions)}")
        return competitions
    except Exception as e:
        logger.exception(f"Error occurred while scraping ICS competitions: {e}")
        return [] 