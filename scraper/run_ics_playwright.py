from scraper.ics_scraper_playwright import scrape_ics_competitions_playwright
import json
from datetime import datetime

if __name__ == "__main__":
    data = scrape_ics_competitions_playwright(headless=True)
    ts = datetime.now().strftime("%Y-%m-%d")
    obj = {'last_scraped': ts, 'contests': data}
    with open("ics_competitions.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} competitions to ics_competitions.json") 