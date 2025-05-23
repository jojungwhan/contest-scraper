import streamlit as st
import logging
from scraper.contest_scraper import scrape_contests
from ui.display_korea import display_contests
from ui.display_ics import display_ics_competitions
import json
import os
import subprocess
from datetime import datetime, date

# Set page to wide mode (must be the first Streamlit command)
st.set_page_config(layout="wide")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

KOREA_JSON = "contests_korea.json"
ICS_JSON = "ics_competitions.json"
KOREA_TIMESTAMP_KEY = "contests_korea_last_scraped"
ICS_TIMESTAMP_KEY = "ics_competitions_last_scraped"

# Initialize session state for storing scraped data
if 'contests_data' not in st.session_state:
    st.session_state.contests_data = []
if 'filter_counter' not in st.session_state:
    st.session_state.filter_counter = 0
if 'ics_competitions' not in st.session_state:
    st.session_state.ics_competitions = []
if KOREA_TIMESTAMP_KEY not in st.session_state:
    st.session_state[KOREA_TIMESTAMP_KEY] = None
if ICS_TIMESTAMP_KEY not in st.session_state:
    st.session_state[ICS_TIMESTAMP_KEY] = None
if 'korea_autoscraped_today' not in st.session_state:
    st.session_state.korea_autoscraped_today = False

def load_json_with_timestamp(filename, timestamp_key):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get('last_scraped')
            if ts:
                st.session_state[timestamp_key] = ts
            return data.get('contests', data) if isinstance(data, dict) else data
        except Exception as e:
            st.warning(f"Failed to load {filename}: {e}")
            return []
    else:
        st.warning(f"{filename} not found. Please run the scraper.")
        return []

def save_json_with_timestamp(filename, data, timestamp_key):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    obj = {'last_scraped': ts, 'contests': data}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    st.session_state[timestamp_key] = ts

def load_ics_competitions_from_json():
    return load_json_with_timestamp(ICS_JSON, ICS_TIMESTAMP_KEY)

def update_ics_competitions_json():
    st.info("Updating ICS competitions using Playwright. Please wait...")
    try:
        result = subprocess.run([
            "python", "-m", "scraper.run_ics_playwright"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("ICS competitions updated successfully!")
        else:
            st.error(f"Failed to update ICS competitions. Error: {result.stderr}")
    except Exception as e:
        st.error(f"Exception while updating ICS competitions: {e}")
    # Save timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state[ICS_TIMESTAMP_KEY] = ts
    # Reload data
    st.session_state.ics_competitions = load_ics_competitions_from_json()

def load_korea_contests_from_json():
    return load_json_with_timestamp(KOREA_JSON, KOREA_TIMESTAMP_KEY)

def update_korea_contests_json():
    st.info("Scraping all Contest Korea contests. Please wait...")
    try:
        contests = scrape_contests(max_pages=20)
        save_json_with_timestamp(KOREA_JSON, contests, KOREA_TIMESTAMP_KEY)
        st.session_state.contests_data = contests
        st.session_state.korea_autoscraped_today = True
        st.success("Contest Korea contests updated successfully!")
    except Exception as e:
        st.error(f"Exception while scraping Contest Korea: {e}")

def check_and_auto_update(filename, timestamp_key, update_func, load_func):
    """If the date has changed since last scrape, auto-update."""
    last_scraped = None
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_scraped = data.get('last_scraped')
        except Exception:
            pass
    today_str = date.today().strftime("%Y-%m-%d")
    if not last_scraped or not last_scraped.startswith(today_str):
        update_func()
    else:
        # Load from file if not already loaded
        if not st.session_state.get(timestamp_key):
            load_func()

def main():
    st.title("Contest Korea Scraper")
    
    # Add page limit option (for display only, not for scraping)
    max_pages = st.slider(
        "Maximum number of pages to display",
        min_value=1,
        max_value=50,
        value=20,
        help="Limit the number of pages to display (scraping always fetches all)",
        key="page_limit_slider"
    )
    
    # Create a placeholder for the contests display
    contests_placeholder = st.empty()
    ics_placeholder = st.empty()
    
    # Always load cached data first
    if not st.session_state.contests_data:
        st.session_state.contests_data = load_json_with_timestamp(KOREA_JSON, KOREA_TIMESTAMP_KEY)

    # Show table immediately
    with contests_placeholder.container():
        # Only display up to max_pages * 12 items (12 per page)
        display_contests(st.session_state.contests_data[:max_pages*12])
        # Move the refresh button here, just below the filter/table
        if st.button("Refresh Contest Korea Contests"):
            update_korea_contests_json()
            st.session_state.contests_data = load_json_with_timestamp(KOREA_JSON, KOREA_TIMESTAMP_KEY)
            st.experimental_rerun()
    # Show last scrape time for Contest Korea
    if st.session_state[KOREA_TIMESTAMP_KEY]:
        st.caption(f"Contest Korea last scraped: {st.session_state[KOREA_TIMESTAMP_KEY]}")

    # If the date has changed, trigger a scrape in the background (but only once per session)
    last_scraped = st.session_state.get(KOREA_TIMESTAMP_KEY)
    today_str = date.today().strftime("%Y-%m-%d")
    if (not last_scraped or not last_scraped.startswith(today_str)) and not st.session_state.korea_autoscraped_today:
        st.info("Automatically scraping Contest Korea for today's data...")
        update_korea_contests_json()
        st.session_state.contests_data = load_json_with_timestamp(KOREA_JSON, KOREA_TIMESTAMP_KEY)
        st.experimental_rerun()

    # Auto-update if date has changed for ICS (but do not block Korea display)
    check_and_auto_update(ICS_JSON, ICS_TIMESTAMP_KEY, update_ics_competitions_json, lambda: st.session_state.update({'ics_competitions': load_ics_competitions_from_json()}))
    # Show last scrape time for ICS
    if st.session_state[ICS_TIMESTAMP_KEY]:
        st.caption(f"ICS competitions last scraped: {st.session_state[ICS_TIMESTAMP_KEY]}")
    # Button to update ICS competitions
    if st.button("Update ICS Competitions (Playwright)"):
        update_ics_competitions_json()
    # Display ICS table
    with ics_placeholder.container():
        display_ics_competitions(st.session_state.ics_competitions)

if __name__ == "__main__":
    main() 