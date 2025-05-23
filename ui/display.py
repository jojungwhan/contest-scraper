import streamlit as st
import pandas as pd

def generate_contest_summary(contest):
    """Generate a summary of the contest details."""
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
    return summary

def display_contests(contests):
    if contests:
        df = pd.DataFrame(contests)
        
        # Sort by D-Day (ascending order - smallest/most urgent first)
        df = df.sort_values('D-Day', ascending=True)
        
        # Create a container for the summary
        summary_container = st.empty()
        
        # Get unique categories for filtering
        unique_categories = sorted(df['Category'].unique())
        
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
        
        # Create a form for the table
        with st.form(key="contests_form"):
            # Add checkboxes to the dataframe
            filtered_df['Select'] = False
            
            # Reorder columns
            column_order = ['Select', 'D-Day', 'Title', 'Category', 'Organization', 'Target', 'Date Info', 'Link']
            filtered_df = filtered_df[column_order]
            
            # Display the data with sortable columns
            st.dataframe(
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
            )
            
            # Add submit button
            submit_button = st.form_submit_button("View Selected Summary")
            
            # Handle form submission
            if submit_button:
                selected_rows = filtered_df[filtered_df['Select'] == True]
                for _, row in selected_rows.iterrows():
                    summary = generate_contest_summary(row)
                    summary_container.markdown(summary)
        
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

def display_ics_competitions(ics_competitions):
    st.subheader("ICS Competitions (competitionsciences.org)")
    if ics_competitions:
        df = pd.DataFrame(ics_competitions)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download ICS Competitions CSV",
            data=csv,
            file_name="ics_competitions.csv",
            mime="text/csv",
            key="ics_download_button"
        )
        st.info(f"Found {len(ics_competitions)} ICS competitions.")
    else:
        st.warning("No ICS competitions found or error occurred while scraping.") 