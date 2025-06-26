import streamlit as st
from modules.utils import render_latex_in_text
# REMOVE CanvasLaTeXConverter import
# from modules.export.latex_converter import CanvasLaTeXConverter # <-- REMOVE THIS LINE

# REMOVE CanvasLaTeXConverter instantiation
# _simple_browse_latex_converter_instance = CanvasLaTeXConverter() # <-- REMOVE THIS LINE

def simple_browse_questions_tab(filtered_df):
    st.markdown(f"### 📋 Browse Questions ({len(filtered_df)} results)")
    if len(filtered_df) > 0:
        # FIXED: Add "Show All" option and make it the default (index=0)
        page_options = ["Show All", 10, 20, 50]
        items_per_page_selection = st.selectbox("Questions per page", page_options, index=0)
        
        # Handle "Show All" option
        if items_per_page_selection == "Show All":
            page_df = filtered_df
            st.info(f"Showing all {len(filtered_df)} questions")
        else:
            items_per_page = items_per_page_selection
            total_pages = (len(filtered_df) - 1) // items_per_page + 1
            
            if total_pages > 1:
                if 'current_page' not in st.session_state:
                    st.session_state['current_page'] = 1
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                with col1:
                    if st.button("⬅️ Previous", key="editor_prev_bottom") and st.session_state['current_page'] > 1:
                        st.session_state['current_page'] -= 1
                        st.rerun()
                with col2:
                    if st.button("⏪ First", key="editor_first_bottom"):
                        st.session_state['current_page'] = 1
                        st.rerun()
                with col3:
                    if st.button("⏩ Last", key="editor_last_bottom"):
                        st.session_state['current_page'] = total_pages
                        st.rerun()
                with col4:
                    if st.button("Next ➡️", key="editor_next_bottom") and st.session_state['current_page'] < total_pages:
                        st.session_state['current_page'] += 1
                        st.rerun()
                st.info(f"Page {st.session_state['current_page']} of {total_pages} ({len(filtered_df)} total questions)")
                start_idx = (st.session_state['current_page'] - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_df = filtered_df.iloc[start_idx:end_idx]
            else:
                page_df = filtered_df
                st.info(f"Showing all {len(filtered_df)} questions")
        
        st.markdown("---")
        for idx, (_, question) in enumerate(page_df.iterrows()):
            st.markdown(f"### Question {idx + 1}")
            # Use a simple preview (relying on st.markdown's native LaTeX detection)
            # Pass latex_converter=None for this rollback
            st.markdown(f"**Question:** {render_latex_in_text(question['Question_Text'], latex_converter=None)}")
            st.markdown("---")
    else:
        st.warning("🔍 No questions match the current filters.")