import streamlit as st
import pandas as pd

def display_ics_competitions(ics_competitions):
    st.subheader("ICS Competitions (competitionsciences.org)")
    if ics_competitions:
        df = pd.DataFrame(ics_competitions)

        # Split categories by comma and strip whitespace, then explode for filtering
        all_tags = set()
        for cats in df['Categories'].dropna():
            tags = [tag.strip() for tag in cats.split(',')]
            all_tags.update(tags)
        unique_tags = sorted(all_tags)

        # Uncheck All logic (only uncheck, do not update table)
        if 'ics_uncheck_all' not in st.session_state:
            st.session_state.ics_uncheck_all = False
        if 'ics_tag_states' not in st.session_state:
            st.session_state.ics_tag_states = {tag: True for tag in unique_tags}
        uncheck_all = st.button("Uncheck All Tags", key="ics_uncheck_all_btn")
        if uncheck_all:
            for tag in unique_tags:
                st.session_state.ics_tag_states[tag] = False

        # Use checkboxes for each tag and an Apply button
        st.subheader("Filter by Category Tag")
        with st.form(key="ics_tag_filter_form"):
            tag_states = {}
            cols = st.columns(4)
            for i, tag in enumerate(unique_tags):
                col = cols[i % 4]
                tag_states[tag] = col.checkbox(tag, value=st.session_state.ics_tag_states.get(tag, True), key=f"ics_tag_{tag}")
            apply_filters = st.form_submit_button("Apply Filters")

        # Only update filtered_df when Apply Filters is pressed
        if 'ics_selected_tags' not in st.session_state or apply_filters:
            st.session_state.ics_selected_tags = [tag for tag, checked in tag_states.items() if checked]
            st.session_state.ics_tag_states = tag_states.copy()
        selected_tags = st.session_state.ics_selected_tags

        # Filter dataframe by selected tags (show if any tag in Categories matches)
        def has_selected_tag(cat_str):
            if pd.isna(cat_str):
                return False
            tags = [tag.strip() for tag in cat_str.split(',')]
            return any(tag in selected_tags for tag in tags)

        if selected_tags:
            filtered_df = df[df['Categories'].apply(has_selected_tag)]
        else:
            filtered_df = df

        # Sort by Title (or any other field if needed)
        filtered_df = filtered_df.sort_values('Title', ascending=True)

        # Create a container for the summary
        summary_container = st.empty()

        # Display competition count
        st.subheader(f"Showing {len(filtered_df)} competitions")

        # Create a form for the table
        with st.form(key="ics_competitions_form"):
            # Add checkboxes to the dataframe
            filtered_df['Select'] = False

            # Reorder columns
            column_order = ['Select', 'Title', 'Ages', 'Categories', 'Link']
            filtered_df = filtered_df[column_order]

            # Display the data with sortable columns
            st.dataframe(
                filtered_df,
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select competitions to view summary",
                        default=False,
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        help="Competition title",
                    ),
                    "Ages": st.column_config.TextColumn(
                        "Ages",
                        help="Eligible ages",
                    ),
                    "Categories": st.column_config.TextColumn(
                        "Categories",
                        help="Competition categories",
                    ),
                    "Link": st.column_config.LinkColumn(
                        "Link",
                        help="Competition link",
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
                    summary = f"""
### {row['Title']}

**Ages:** {row['Ages']}

**Categories:** {row['Categories']}

**Link:** {row['Link']}
"""
                    summary_container.markdown(summary)

        # Add download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download ICS Competitions CSV",
            data=csv,
            file_name="ics_competitions.csv",
            mime="text/csv",
            key="ics_download_button"
        )

        # Display summary
        st.info(f"Found {len(ics_competitions)} ICS competitions.")
    else:
        st.warning("No ICS competitions found or error occurred while scraping.") 