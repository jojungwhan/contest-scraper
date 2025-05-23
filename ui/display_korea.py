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