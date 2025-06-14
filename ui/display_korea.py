import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from scraper.marketing_content_generator import generate_marketing_content
import os
from urllib.parse import urljoin
import re

def generate_contest_summary(contest):
    """Generate a summary of the contest details, including scraped detail page content if possible."""
    detail_html = None
    detail_url = contest.get('Link')
    image_path = None
    if detail_url:
        try:
            resp = requests.get(detail_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')
            detail_area = soup.find('div', class_='view_detail_area')
            if detail_area:
                # Extract the main text content, preserving basic formatting
                detail_html = detail_area.prettify()
                # Try to extract image from <div class="img_area"><img ...>
                img_area = detail_area.find('div', class_='img_area')
                if img_area:
                    img_tag = img_area.find('img')
                    if img_tag and img_tag.has_attr('src'):
                        img_url = img_tag['src']
                        # Make absolute URL if needed
                        if img_url.startswith('/'):
                            img_url = urljoin('https://www.contestkorea.com', img_url)
                        # Download and save image locally
                        img_resp = requests.get(img_url, timeout=10)
                        if img_resp.status_code == 200:
                            img_dir = 'downloaded_images'
                            os.makedirs(img_dir, exist_ok=True)
                            img_filename = f"{contest['Title'][:50].replace(' ', '_').replace('/', '_')}.jpg"
                            image_path = os.path.join(img_dir, img_filename)
                            with open(image_path, 'wb') as f:
                                f.write(img_resp.content)
        except Exception as e:
            detail_html = None
            image_path = None
    if detail_html:
        # Remove <div class="img_area">...</div> from detail_html
        detail_html = re.sub(r'<div[^>]*class=["\"][^"\"]*img_area[^"\"]*["\"][^>]*>.*?</div>', '', detail_html, flags=re.IGNORECASE|re.DOTALL)
        summary = f"""
### {contest['Title']}

**Category:** {contest['Category']}

**Organization:** {contest['Organization']}

**Target Participants:** {contest['Target']}

**Deadline Information:**
{contest['Date Info']}

**Days Left:** {contest['D-Day']} days

**Application Link:** {contest['Link']}

---

**Contest Details:**
"""
        return summary, detail_html, image_path
    else:
        # Fallback to original summary
        summary = f"""
### {contest['Title']}

**Category:** {contest['Category']}

**Organization:** {contest['Organization']}

**Target Participants:** {contest['Target']}

**Deadline Information:**
{contest['Date Info']}

**Days Left:** {contest['D-Day']} days

**Application Link:** {contest['Link']}

**Keywords:**
- Category: {contest['Category']}
- Target: {contest['Target']}
- Application Method: Online (via contestkorea.com)
"""
        return summary, None, None

def display_contests(contests):
    if contests:
        df = pd.DataFrame(contests)
        
        # Sort by D-Day (ascending order - smallest/most urgent first)
        df = df.sort_values('D-Day', ascending=True)
        
        # Create a container for the summary
        summary_container = st.empty()
        
        # Get unique categories for filtering
        unique_categories = sorted(df['Category'].unique())
        # Clean up target strings for filter options
        def clean_target(t):
            t = t.replace('대상.', '').replace('대상 .', '').replace('대상', '').strip()
            return t
        unique_targets = sorted({clean_target(t) for targets in df['Target'].dropna() for t in targets.split(',') if '해당자' not in t})
        unique_targets = [t for t in unique_targets if t]  # Remove empty strings
        
        # Uncheck All logic for categories and targets
        if 'korea_uncheck_all' not in st.session_state:
            st.session_state.korea_uncheck_all = False
        uncheck_all = st.button("Uncheck All Filters", key="korea_uncheck_all_btn")
        if uncheck_all:
            st.session_state.korea_uncheck_all = True
        else:
            st.session_state.korea_uncheck_all = False
        
        # Use checkboxes for each category and target, and an Apply button
        st.subheader("Filter")
        with st.form(key="korea_filter_form"):
            cat_states = {}
            target_states = {}
            cat_cols = st.columns(4)
            for i, cat in enumerate(unique_categories):
                col = cat_cols[i % 4]
                default_checked = not st.session_state.korea_uncheck_all if f"korea_cat_{cat}" not in st.session_state else st.session_state[f"korea_cat_{cat}"]
                cat_states[cat] = col.checkbox(cat, value=default_checked, key=f"korea_cat_{cat}")
            target_cols = st.columns(4)
            for i, target in enumerate(unique_targets):
                col = target_cols[i % 4]
                default_checked = not st.session_state.korea_uncheck_all if f"korea_target_{target}" not in st.session_state else st.session_state[f"korea_target_{target}"]
                target_states[target] = col.checkbox(target, value=default_checked, key=f"korea_target_{target}")
            apply_filters = st.form_submit_button("Apply Filters")
        # Only update filtered_df when Apply Filters is pressed or Uncheck All is pressed
        if 'korea_selected_categories' not in st.session_state or apply_filters or st.session_state.korea_uncheck_all:
            st.session_state.korea_selected_categories = [cat for cat, checked in cat_states.items() if checked]
            st.session_state.korea_selected_targets = [target for target, checked in target_states.items() if checked]
        selected_categories = st.session_state.korea_selected_categories
        selected_targets = st.session_state.korea_selected_targets
        
        # Filter dataframe by selected categories AND selected targets
        def target_match(target_str):
            if pd.isna(target_str):
                return False
            targets = [t.strip() for t in target_str.split(',')]
            return any(t in selected_targets for t in targets)
        if selected_categories and selected_targets:
            filtered_df = df[df['Category'].isin(selected_categories) & df['Target'].apply(target_match)].copy()
        elif selected_categories:
            filtered_df = df[df['Category'].isin(selected_categories)].copy()
        elif selected_targets:
            filtered_df = df[df['Target'].apply(target_match)].copy()
        else:
            filtered_df = df.copy()
        
        # Display contest count
        st.subheader(f"Showing {len(filtered_df)} contests")
        
        # Create a form for the table
        selected_rows = pd.DataFrame()
        with st.form(key="contests_form"):
            filtered_df['Select'] = False
            column_order = ['Select', 'D-Day', 'Title', 'Category', 'Organization', 'Target', 'Date Info', 'Link']
            filtered_df = filtered_df[column_order]
            edited_df = st.data_editor(
                filtered_df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select contests to view summary",
                        default=False,
                    ),
                    "D-Day": st.column_config.NumberColumn(
                        "D-Day",
                        help="Days left until deadline",
                        format="%d",
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        help="Contest title",
                    ),
                    "Category": st.column_config.TextColumn(
                        "Category",
                        help="Contest category",
                    ),
                    "Organization": st.column_config.TextColumn(
                        "Organization",
                        help="Contest organizer",
                    ),
                    "Target": st.column_config.TextColumn(
                        "Target",
                        help="Target participants",
                    ),
                    "Date Info": st.column_config.TextColumn(
                        "Date Info",
                        help="Contest dates",
                    ),
                    "Link": st.column_config.LinkColumn(
                        "Link",
                        help="Contest link",
                    ),
                },
                hide_index=True,
                use_container_width=True,
                key="korea_data_editor"
            )
            submit_button = st.form_submit_button("View Selected Summary")
            if submit_button:
                selected_rows = edited_df[edited_df['Select'] == True]
                st.session_state['selected_rows'] = selected_rows
        # After the form, retrieve selected_rows from session state if available
        if 'selected_rows' in st.session_state:
            selected_rows = st.session_state['selected_rows']
        else:
            selected_rows = pd.DataFrame()
        # After the form, display summaries and buttons for selected rows
        if not isinstance(selected_rows, pd.DataFrame):
            selected_rows = pd.DataFrame(selected_rows)
        if not selected_rows.empty:
            for idx, row in selected_rows.iterrows():
                summary, detail_html, image_path = generate_contest_summary(row)
                summary_container.markdown(summary)
                if detail_html:
                    st.success("Contest detail page scraped successfully.")
                    st.markdown(detail_html, unsafe_allow_html=True)
                    if image_path:
                        img_key = f"show_full_{row['Title']}"
                        if img_key not in st.session_state:
                            st.session_state[img_key] = False
                        toggle_label = "Show Small Image" if st.session_state[img_key] else "Show Full Image"
                        if st.button(f"{toggle_label}: {row['Title']}", key=f"toggle_img_{row['Title']}_{idx}"):
                            st.session_state[img_key] = not st.session_state[img_key]
                            st.rerun()
                        if st.session_state[img_key]:
                            st.image(image_path, caption="Contest Poster (click button to shrink)")
                        else:
                            st.image(image_path, caption="Contest Poster (click button to enlarge)", width=200)
                    # Add a debug log to confirm this code path is reached
                    st.info(f"[DEBUG] Ready to show Generate Marketing Content button for {row['Title']} (idx={idx})")
                    if st.button(f"Generate Marketing Content for {row['Title']}", key=f"marketing_btn_{row['Title']}_{idx}"):
                        st.info("[DEBUG] Button pressed. Calling generate_marketing_content...")
                        with st.spinner("Generating marketing content with OpenAI..."):
                            try:
                                marketing_result = generate_marketing_content(detail_html)
                                st.success("[DEBUG] OpenAI API call succeeded.")
                                st.subheader("Marketing Content")
                                st.json(marketing_result)
                            except Exception as e:
                                st.error(f"[DEBUG] OpenAI API call failed: {e}")
                else:
                    st.warning("Could not scrape contest detail page. Showing basic info only.")
        
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