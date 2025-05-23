import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging
import time

# Set page to wide mode (must be the first Streamlit command)
st.set_page_config(layout="wide")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize session state for storing scraped data
if 'contests_data' not in st.session_state:
    st.session_state.contests_data = []
if 'filter_counter' not in st.session_state:
    st.session_state.filter_counter = 0

def extract_days_left(dday_text):
    """Extract numeric days left from D-Day text."""
    try:
        # Remove any non-numeric characters except minus sign
        days = ''.join(c for c in dday_text if c.isdigit() or c == '-')
        return int(days) if days else 0
    except:
        return 0

def scrape_contests(max_pages=None):
    base_url = "https://www.contestkorea.com/sub/list.php"
    params = {
        "displayrow": "12",
        "int_gbn": "1",
        "Txt_sGn": "1",
        "Txt_key": "all",
        "Txt_word": "",
        "Txt_bcode": "",
        "Txt_code1[0]": "98",
        "Txt_code1[1]": "27",
        "Txt_code1[2]": "28",
        "Txt_code1[3]": "29",
        "Txt_aarea": "",
        "Txt_area": "",
        "Txt_sortkey": "a.int_sort",
        "Txt_sortword": "desc",
        "Txt_host": "",
        "Txt_award": "",
        "Txt_award2": "",
        "Txt_code3": "",
        "Txt_tipyn": "",
        "Txt_comment": "",
        "Txt_resultyn": "",
        "Txt_actcode": "",
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    all_contests = []
    page = 1
    
    # Progress bar for scraping
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Set the number of pages to scrape
        pages_to_scrape = max_pages if max_pages is not None else float('inf')
        logger.info(f"Will attempt to scrape up to {pages_to_scrape} pages")
        status_text.text(f"Scraping page 1...")
        
        # Scrape each page until we hit the limit or find an invalid page
        while True:
            # Check if we've hit the page limit
            if page > pages_to_scrape:
                break
                
            params["page"] = page
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            # If we get a 404 or no content, we've reached the end
            if response.status_code == 404 or len(response.content) == 0:
                logger.info(f"Reached end of available pages at page {page-1}")
                break
                
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the main container
            main_container = soup.find('div', class_='list_style_2')
            if not main_container:
                logger.info(f"No more contests found at page {page}")
                break
                
            # Get all list items within the container that have a title div
            contest_items = main_container.find_all('li', class_=lambda x: x != 'icon_1' and x != 'icon_2')
            
            if not contest_items:
                logger.info(f"No contest items found on page {page}")
                break
                
            logger.info(f"Found {len(contest_items)} contest items on page {page}")
            
            for item in contest_items:
                try:
                    # Get title and link from the title div
                    title_div = item.find('div', class_='title')
                    if not title_div:
                        continue
                        
                    title_link = title_div.find('a')
                    if not title_link:
                        continue
                        
                    # Get category and title
                    category_elem = title_link.find('span', class_='category')
                    title_elem = title_link.find('span', class_='txt')
                    
                    if not category_elem or not title_elem:
                        continue
                        
                    category = category_elem.text.strip()
                    title = title_elem.text.strip()
                    link = "https://www.contestkorea.com" + title_link['href']
                    
                    # Get host information
                    host_ul = item.find('ul', class_='host')
                    organization = "N/A"
                    target = "N/A"
                    
                    if host_ul:
                        host_li = host_ul.find('li', class_='icon_1')
                        if host_li:
                            organization = host_li.text.replace('주최.', '').strip()
                        
                        target_li = host_ul.find('li', class_='icon_2')
                        if target_li:
                            target = target_li.text.replace('대상.', '').strip()
                    
                    # Get date information
                    date_div = item.find('div', class_='date')
                    date_info = "N/A"
                    if date_div:
                        date_spans = date_div.find_all('span')
                        dates = []
                        for span in date_spans:
                            step = span.find('em')
                            if step:
                                step_text = step.text.strip()
                                date = span.text.replace(step_text, '').strip()
                                dates.append(f"{step_text}: {date}")
                        date_info = " | ".join(dates) if dates else "N/A"
                    
                    # Get D-day information
                    dday_div = item.find('div', class_='d-day')
                    days_left = 0
                    if dday_div:
                        dday = dday_div.find('span', class_='day')
                        if dday:
                            dday_text = dday.text.strip()
                            days_left = extract_days_left(dday_text)
                    
                    all_contests.append({
                        'Category': category,
                        'Title': title,
                        'Organization': organization,
                        'Target': target,
                        'Date Info': date_info,
                        'D-Day': days_left,  # Store as integer for sorting and display
                        'Link': link
                    })
                    
                    logger.info(f"Successfully processed contest: {title}")
                    
                except Exception as e:
                    logger.error(f"Error processing item on page {page}: {str(e)}")
                    continue
            
            # Update progress
            if pages_to_scrape != float('inf'):
                progress = page / pages_to_scrape
                progress_bar.progress(progress)
            status_text.text(f"Scraping page {page}...")
            
            # Move to next page
            page += 1
            
            # Add a small delay to avoid overloading the server
            time.sleep(1)
            
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Store the scraped data in session state
        st.session_state.contests_data = all_contests
        
        return all_contests
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error occurred: {str(e)}")
        return all_contests
    except Exception as e:
        logger.error(f"Error scraping contests: {str(e)}")
        return all_contests

def display_contests(contests):
    if contests:
        df = pd.DataFrame(contests)
        
        # Sort by D-Day
        df = df.sort_values('D-Day')
        
        # Reorder columns to put D-Day first
        column_order = [
            'D-Day',
            'Category',
            'Title',
            'Organization',
            'Target',
            'Date Info',
            'Link'
        ]
        df = df[column_order]
        
        # Get unique categories for filtering
        unique_categories = sorted(df['Category'].unique())
        
        # Increment the counter for unique key generation
        st.session_state.filter_counter += 1
        
        # Add category filter with a dynamic unique key
        st.subheader("Filter by Category")
        selected_categories = st.multiselect(
            "Select categories to display",
            options=unique_categories,
            default=unique_categories,
            help="Choose one or more categories to filter the contests",
            key=f"category_filter_{st.session_state.filter_counter}"
        )
        
        # Filter dataframe by selected categories
        if selected_categories:
            filtered_df = df[df['Category'].isin(selected_categories)]
        else:
            filtered_df = df
        
        # Display contest count
        st.subheader(f"Showing {len(filtered_df)} contests")
        
        # Display the data with maximum width columns
        st.dataframe(
            filtered_df,
            column_config={
                "D-Day": st.column_config.NumberColumn(
                    "D-Day",
                    width="max",
                    format="%d",
                ),
                "Category": st.column_config.TextColumn(
                    "Category",
                    width="max",
                ),
                "Title": st.column_config.TextColumn(
                    "Title",
                    width="max",
                ),
                "Organization": st.column_config.TextColumn(
                    "Organization",
                    width="max",
                ),
                "Target": st.column_config.TextColumn(
                    "Target",
                    width="max",
                ),
                "Date Info": st.column_config.TextColumn(
                    "Date Info",
                    width="max",
                ),
                "Link": st.column_config.LinkColumn(
                    "Link",
                    width="max",
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        
        # Add download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="contests.csv",
            mime="text/csv",
            key=f"download_button_{st.session_state.filter_counter}"
        )
        
        # Display summary
        st.info(f"Found {len(contests)} contests across all pages.")
    else:
        st.warning("No contests found or error occurred while scraping.")

def main():
    st.title("Contest Korea Scraper")
    
    # Add page limit option
    max_pages = st.slider(
        "Maximum number of pages to scrape",
        min_value=1,
        max_value=20,
        value=5,
        help="Limit the number of pages to scrape to avoid long loading times",
        key="page_limit_slider"  # Add a unique key for the slider
    )
    
    # Create a placeholder for the contests display
    contests_placeholder = st.empty()
    
    # Initialize session state for max_pages if not exists
    if 'current_max_pages' not in st.session_state:
        st.session_state.current_max_pages = max_pages
    
    # Force refresh if max_pages has changed
    if st.session_state.current_max_pages != max_pages:
        st.session_state.contests_data = []  # Clear existing data
        st.session_state.current_max_pages = max_pages
        # Force immediate refresh
        contests = scrape_contests(max_pages)
        with contests_placeholder.container():
            display_contests(contests)
    else:
        # Check if we already have data in session state
        if not st.session_state.contests_data:
            # Initial scraping if no data exists
            contests = scrape_contests(max_pages)
            with contests_placeholder.container():
                display_contests(contests)
        else:
            # Use existing data from session state
            with contests_placeholder.container():
                display_contests(st.session_state.contests_data)
    
    # Add refresh button
    if st.button("Refresh Contests"):
        contests = scrape_contests(max_pages)
        with contests_placeholder.container():
            display_contests(contests)

if __name__ == "__main__":
    main() 