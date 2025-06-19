import streamlit as st
from modules.utils import render_latex_in_text

def simple_browse_questions_tab(filtered_df):
    st.markdown(f"### 📋 Browse Questions ({len(filtered_df)} results)")
    if len(filtered_df) > 0:
        items_per_page = st.selectbox("Questions per page", [10, 20, 50], index=1)
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
        st.markdown("---")
        for idx, (_, question) in enumerate(page_df.iterrows()):
            st.markdown(f"### Question {idx + 1}")
            # Use a simple preview (reuse display_question_preview if needed)
            st.markdown(f"**Question:** {render_latex_in_text(question['Question_Text'])}")
            st.markdown("---")
    else:
        st.warning("🔍 No questions match the current filters.")
