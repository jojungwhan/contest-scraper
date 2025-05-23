from scraper.contest_scraper import scrape_contests
from scraper.ics_scraper_playwright import scrape_ics_competitions_playwright
import json

if __name__ == "__main__":
    # Scrape Contest Korea
    print("Scraping Contest Korea...")
    korea_data = scrape_contests(max_pages=20)
    with open("contests_korea.json", "w", encoding="utf-8") as f:
        json.dump(korea_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(korea_data)} contests to contests_korea.json")

    # Scrape ICS competitions
    print("Scraping ICS competitions (Playwright)...")
    ics_data = scrape_ics_competitions_playwright(headless=True)
    with open("ics_competitions.json", "w", encoding="utf-8") as f:
        json.dump(ics_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(ics_data)} competitions to ics_competitions.json") 