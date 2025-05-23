import logging
import requests
from bs4 import BeautifulSoup
import time
from .utils import extract_days_left


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
    
    try:
        # Set the number of pages to scrape
        pages_to_scrape = max_pages if max_pages is not None else float('inf')
        logging.info(f"Will attempt to scrape up to {pages_to_scrape} pages")
        
        # Scrape each page until we hit the limit or find an invalid page
        while True:
            # Check if we've hit the page limit
            if page > pages_to_scrape:
                break
                
            params["page"] = page
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            # If we get a 404 or no content, we've reached the end
            if response.status_code == 404 or len(response.content) == 0:
                logging.info(f"Reached end of available pages at page {page-1}")
                break
                
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the main container
            main_container = soup.find('div', class_='list_style_2')
            if not main_container:
                logging.info(f"No more contests found at page {page}")
                break
                
            # Get all list items within the container that have a title div
            contest_items = main_container.find_all('li', class_=lambda x: x != 'icon_1' and x != 'icon_2')
            
            if not contest_items:
                logging.info(f"No contest items found on page {page}")
                break
                
            logging.info(f"Found {len(contest_items)} contest items on page {page}")
            
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
                    href = title_link['href']
                    if not href.startswith('/sub/'):
                        href = '/sub/' + href.lstrip('/')
                    link = "https://www.contestkorea.com" + href
                    
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
                            # Remove '대상.' and clean up spaces
                            target = target_li.text.replace('대상.', '').strip()
                            # Remove multiple spaces and newlines
                            target = ' '.join(target.split())
                    
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
                    
                    logging.info(f"Successfully processed contest: {title}")
                    
                except Exception as e:
                    logging.error(f"Error processing item on page {page}: {str(e)}")
                    continue
            
            # Move to next page
            page += 1
            
            # Add a small delay to avoid overloading the server
            time.sleep(1)
        
        return all_contests
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error occurred: {str(e)}")
        return all_contests
    except Exception as e:
        logging.error(f"Error scraping contests: {str(e)}")
        return all_contests 