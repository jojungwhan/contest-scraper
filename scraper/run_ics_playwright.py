from scraper.ics_scraper_playwright import scrape_ics_competitions_playwright
import json

if __name__ == "__main__":
    data = scrape_ics_competitions_playwright(headless=True)
    with open("ics_competitions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} competitions to ics_competitions.json") 