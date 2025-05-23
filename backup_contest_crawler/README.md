# Contest Korea Scraper

A Streamlit application that scrapes contest information from Contest Korea website and displays it in a table format.

## Features

- Scrapes contest information including title, organization, date info, and links
- Displays data in a clean, interactive table
- Allows downloading the data as CSV
- Auto-refresh functionality

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)
3. Click the "Refresh Contests" button to fetch the latest contest information
4. Use the download button to save the data as a CSV file

## Requirements

- Python 3.7+
- Streamlit
- Requests
- BeautifulSoup4
- Pandas
- lxml

## Note

This application is for educational purposes only. Please respect the website's terms of service and robots.txt when using this scraper. 