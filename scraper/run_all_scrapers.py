from scraper.contest_scraper import scrape_contests
from scraper.ics_scraper_playwright import scrape_ics_competitions_playwright
import json
from datetime import datetime

if __name__ == "__main__":
    # Scrape Contest Korea
    print("Scraping Contest Korea...")
    korea_data = scrape_contests(max_pages=20)
    ts_korea = datetime.now().strftime("%Y-%m-%d")
    korea_obj = {'last_scraped': ts_korea, 'contests': korea_data}
    with open("contests_korea.json", "w", encoding="utf-8") as f:
        json.dump(korea_obj, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(korea_data)} contests to contests_korea.json")

    # Scrape ICS competitions
    print("Scraping ICS competitions (Playwright)...")
    ics_data = scrape_ics_competitions_playwright(headless=True)
    ts = datetime.now().strftime("%Y-%m-%d")
    obj = {'last_scraped': ts, 'contests': ics_data}
    with open("ics_competitions.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(ics_data)} competitions to ics_competitions.json") 