import streamlit as st
import plotly.express as px
from typing import Optional
from .app_config import AppConfig

def display_database_summary(df, metadata):
    st.markdown('<div class="main-header">📊 Database Overview</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Questions", len(df))
    with col2:
        unique_topics = df['Topic'].nunique()
        st.metric("Topics", unique_topics)
    with col3:
        unique_subtopics = len([s for s in df['Subtopic'].unique() if s and s != 'N/A'])
        st.metric("Subtopics", unique_subtopics)
    with col4:
        total_points = df['Points'].sum()
        st.metric("Total Points", f"{total_points:.0f}")
    if metadata:
        st.markdown("### 📋 Database Metadata")
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            if 'subject' in metadata:
                st.info(f"**Subject:** {metadata['subject']}")
            if 'format_version' in metadata:
                st.info(f"**Format:** {metadata['format_version']}")
        with meta_col2:
            if 'generation_date' in metadata:
                st.info(f"**Generated:** {metadata['generation_date']}")
            if 'total_questions' in metadata:
                st.info(f"**Expected Questions:** {metadata['total_questions']}")

def create_summary_charts(df, chart_key_suffix: Optional[str] = None):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📚 Topics Distribution")
        topic_counts = df['Topic'].value_counts()
        fig_topics = px.pie(
            values=topic_counts.values,
            names=topic_counts.index,
            title="Questions by Topic"
        )
        fig_topics.update_traces(textposition='inside', textinfo='percent+label')
        topics_chart_key = f"topics_chart_{chart_key_suffix}" if chart_key_suffix else "topics_chart_default"
        st.plotly_chart(fig_topics, use_container_width=True, key=topics_chart_key)
    with col2:
        st.markdown("### 🎯 Difficulty Distribution")
        difficulty_counts = df['Difficulty'].value_counts()
        colors = {'Easy': '#90EE90', 'Medium': '#FFD700', 'Hard': '#FF6347'}
        color_sequence = [colors.get(level, '#1f77b4') for level in difficulty_counts.index]
        fig_difficulty = px.bar(
            x=difficulty_counts.index,
            y=difficulty_counts.values,
            title="Questions by Difficulty",
            color=difficulty_counts.index,
            color_discrete_sequence=color_sequence
        )
        fig_difficulty.update_layout(showlegend=False)
        difficulty_chart_key = f"difficulty_chart_{chart_key_suffix}" if chart_key_suffix else "difficulty_chart_default"
        st.plotly_chart(fig_difficulty, use_container_width=True, key=difficulty_chart_key)
    subtopics = df[df['Subtopic'].notna() & (df['Subtopic'] != '') & (df['Subtopic'] != 'N/A')]['Subtopic'].value_counts()
    if len(subtopics) > 0:
        st.markdown("### 🔍 Subtopics Distribution")
        fig_subtopics = px.bar(
            x=subtopics.values,
            y=subtopics.index,
            orientation='h',
            title="Questions by Subtopic"
        )
        fig_subtopics.update_layout(height=max(400, len(subtopics) * 30))
        subtopics_chart_key = f"subtopics_chart_{chart_key_suffix}" if chart_key_suffix else "subtopics_chart_default"
        st.plotly_chart(fig_subtopics, use_container_width=True, key=subtopics_chart_key)
    st.markdown("### 📝 Question Types")
    type_counts = df['Type'].value_counts()
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_types = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title="Questions by Type"
        )
        types_chart_key = f"types_chart_{chart_key_suffix}" if chart_key_suffix else "types_chart_default"
        st.plotly_chart(fig_types, use_container_width=True, key=types_chart_key)
    with col2:
        st.markdown("**Type Breakdown:**")
        for qtype, count in type_counts.items():
            percentage = (count / len(df)) * 100
            st.write(f"• **{qtype}**: {count} ({percentage:.1f}%)")

def apply_filters(df):
    st.sidebar.markdown("## 🔍 Filter Questions")
    filtered_df = df.copy()
    topics = ['All'] + sorted(df['Topic'].unique().tolist())
    selected_topic = st.sidebar.selectbox("📚 Topic", topics)
    if selected_topic != 'All':
        filtered_df = filtered_df[filtered_df['Topic'] == selected_topic]
    available_subtopics = filtered_df[
        filtered_df['Subtopic'].notna() & 
        (filtered_df['Subtopic'] != '') & 
        (filtered_df['Subtopic'] != 'N/A')
    ]['Subtopic'].unique()
    if len(available_subtopics) > 0:
        subtopics = ['All'] + sorted(available_subtopics.tolist())
        selected_subtopic = st.sidebar.selectbox("🎯 Subtopic", subtopics)
        if selected_subtopic != 'All':
            filtered_df = filtered_df[filtered_df['Subtopic'] == selected_subtopic]
    difficulties = ['All'] + sorted(df['Difficulty'].unique().tolist())
    selected_difficulty = st.sidebar.selectbox("⚡ Difficulty", difficulties)
    if selected_difficulty != 'All':
        filtered_df = filtered_df[filtered_df['Difficulty'] == selected_difficulty]
    types = ['All'] + sorted(df['Type'].unique().tolist())
    selected_type = st.sidebar.selectbox("📝 Question Type", types)
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]
    min_points, max_points = int(df['Points'].min()), int(df['Points'].max())
    if min_points < max_points:
        points_range = st.sidebar.slider(
            "💎 Points Range", 
            min_points, max_points, 
            (min_points, max_points)
        )
        filtered_df = filtered_df[
            (filtered_df['Points'] >= points_range[0]) & 
            (filtered_df['Points'] <= points_range[1])
        ]
    search_term = st.sidebar.text_input("🔍 Search in Questions", "")
    if search_term:
        mask = (
            filtered_df['Title'].str.contains(search_term, case=False, na=False) |
            filtered_df['Question_Text'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**📊 Results: {len(filtered_df)} questions**")
    if len(filtered_df) < len(df):
        st.sidebar.markdown(f"*Filtered from {len(df)} total*")
    return filtered_df

def create_category_selection_interface(df):
    """
    Create a dedicated, full-width category selection interface for the SELECTING_CATEGORIES state.
    This replaces the sidebar filtering approach with a main-area selection interface.
    
    Args:
        df: DataFrame containing all questions
        
    Returns:
        tuple: (filtered_df, continue_to_questions_clicked)
    """
    st.markdown('<div class="main-header">🏷️ Select Question Categories</div>', unsafe_allow_html=True)
    st.markdown("Configure your question selection criteria below. Use the filters to narrow down questions by topic, subtopic, difficulty, and other attributes.")
    
    # Initialize session state for category selection
    if 'category_selection' not in st.session_state:
        st.session_state.category_selection = {
            'topics': [],
            'subtopics': [],
            'difficulties': [],
            'types': [],
            'points_range': None,
            'search_term': ''
        }
    
    # Create the main selection interface
    st.markdown("### 📚 Topic Selection")
    
    # Topics multiselect
    available_topics = sorted(df['Topic'].unique().tolist())
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_topics = st.multiselect(
            "Select topics to include:",
            available_topics,
            default=st.session_state.category_selection['topics'],
            key="topic_multiselect",
            help="Choose one or more topics. Leave empty to include all topics."
        )
        st.session_state.category_selection['topics'] = selected_topics
    
    with col2:
        if AppConfig.create_red_button("Select All Topics", "secondary-action", "select_all_topics"):
            st.session_state.category_selection['topics'] = available_topics
            st.rerun()
        
        if AppConfig.create_red_button("Clear Topics", "secondary-action", "clear_topics"):
            st.session_state.category_selection['topics'] = []
            st.rerun()
    
    # Filter data based on topics for subtopic selection
    if selected_topics:
        topic_filtered_df = df[df['Topic'].isin(selected_topics)]
    else:
        topic_filtered_df = df
    
    # Subtopics multiselect (filtered by selected topics)
    st.markdown("### 🎯 Subtopic Selection")
    available_subtopics = topic_filtered_df[
        topic_filtered_df['Subtopic'].notna() & 
        (topic_filtered_df['Subtopic'] != '') & 
        (topic_filtered_df['Subtopic'] != 'N/A')
    ]['Subtopic'].unique()
    
    if len(available_subtopics) > 0:
        available_subtopics = sorted(available_subtopics.tolist())
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_subtopics = st.multiselect(
                "Select subtopics to include:",
                available_subtopics,
                default=st.session_state.category_selection['subtopics'],
                key="subtopic_multiselect",
                help="Choose specific subtopics. Leave empty to include all available subtopics."
            )
            st.session_state.category_selection['subtopics'] = selected_subtopics
        
        with col2:
            if AppConfig.create_red_button("Select All Subtopics", "secondary-action", "select_all_subtopics"):
                st.session_state.category_selection['subtopics'] = available_subtopics
                st.rerun()
            
            if AppConfig.create_red_button("Clear Subtopics", "secondary-action", "clear_subtopics"):
                st.session_state.category_selection['subtopics'] = []
                st.rerun()
    else:
        st.info("No subtopics available for the selected topics.")
        selected_subtopics = []
    
    # Difficulty and Type Selection
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Difficulty Selection")
        available_difficulties = sorted(df['Difficulty'].unique().tolist())
        selected_difficulties = st.multiselect(
            "Select difficulty levels:",
            available_difficulties,
            default=st.session_state.category_selection['difficulties'],
            key="difficulty_multiselect",
            help="Choose difficulty levels to include."
        )
        st.session_state.category_selection['difficulties'] = selected_difficulties
    
    with col2:
        st.markdown("### 📝 Question Type Selection")
        available_types = sorted(df['Type'].unique().tolist())
        selected_types = st.multiselect(
            "Select question types:",
            available_types,
            default=st.session_state.category_selection['types'],
            key="type_multiselect",
            help="Choose question types to include."
        )
        st.session_state.category_selection['types'] = selected_types
    
    # Points Range and Search
    st.markdown("### 💎 Advanced Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        min_points, max_points = int(df['Points'].min()), int(df['Points'].max())
        if min_points < max_points:
            if st.session_state.category_selection['points_range'] is None:
                default_range = (min_points, max_points)
            else:
                default_range = st.session_state.category_selection['points_range']
            
            points_range = st.slider(
                "Points Range:",
                min_points, max_points,
                default_range,
                key="points_slider",
                help="Filter questions by point value range."
            )
            st.session_state.category_selection['points_range'] = points_range
        else:
            points_range = (min_points, max_points)
    
    with col2:
        search_term = st.text_input(
            "Search in Questions:",
            value=st.session_state.category_selection['search_term'],
            key="search_input",
            help="Search in question titles and content."
        )
        st.session_state.category_selection['search_term'] = search_term
    
    # Apply all filters to get the final filtered dataset
    filtered_df = df.copy()
    
    # Apply topic filter
    if selected_topics:
        filtered_df = filtered_df[filtered_df['Topic'].isin(selected_topics)]
    
    # Apply subtopic filter
    if selected_subtopics:
        filtered_df = filtered_df[filtered_df['Subtopic'].isin(selected_subtopics)]
    
    # Apply difficulty filter
    if selected_difficulties:
        filtered_df = filtered_df[filtered_df['Difficulty'].isin(selected_difficulties)]
    
    # Apply type filter
    if selected_types:
        filtered_df = filtered_df[filtered_df['Type'].isin(selected_types)]
    
    # Apply points filter
    if min_points < max_points:
        filtered_df = filtered_df[
            (filtered_df['Points'] >= points_range[0]) & 
            (filtered_df['Points'] <= points_range[1])
        ]
    
    # Apply search filter
    if search_term:
        mask = (
            filtered_df['Title'].str.contains(search_term, case=False, na=False) |
            filtered_df['Question_Text'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # Display live question count and summary
    st.markdown("---")
    st.markdown("### 📊 Selection Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Selected Questions", len(filtered_df))
        st.metric("Total Available", len(df))
    
    with col2:
        if len(filtered_df) > 0:
            topics_in_selection = filtered_df['Topic'].nunique()
            st.metric("Topics in Selection", topics_in_selection)
            
            difficulties_in_selection = filtered_df['Difficulty'].nunique()
            st.metric("Difficulty Levels", difficulties_in_selection)
    
    with col3:
        if len(filtered_df) > 0:
            total_points = filtered_df['Points'].sum()
            st.metric("Total Points", f"{total_points:.0f}")
            
            avg_points = filtered_df['Points'].mean()
            st.metric("Average Points", f"{avg_points:.1f}")
    
    # Quick preview of selected questions
    if len(filtered_df) > 0:
        st.markdown("### 👀 Preview of Selected Questions")
        preview_df = filtered_df[['Title', 'Topic', 'Subtopic', 'Difficulty', 'Type', 'Points']].head(5)
        st.dataframe(preview_df, use_container_width=True)
        
        if len(filtered_df) > 5:
            st.info(f"Showing 5 of {len(filtered_df)} selected questions. All questions will be available for selection in the next step.")
    else:
        st.warning("⚠️ No questions match your current selection criteria. Please adjust your filters.")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    continue_clicked = False
    with col2:
        if len(filtered_df) > 0:
            continue_clicked = AppConfig.create_red_button(
                f"Continue to Questions ({len(filtered_df)} selected)",
                "primary-action",
                "continue_to_questions"
            )
        else:
            st.info("👆 Adjust filters above to select questions before continuing.")
    
    with col1:
        if AppConfig.create_red_button("Reset All Filters", "secondary-action", "reset_all_filters"):
            st.session_state.category_selection = {
                'topics': [],
                'subtopics': [],
                'difficulties': [],
                'types': [],
                'points_range': None,
                'search_term': ''
            }
            st.rerun()
    
    return filtered_df, continue_clicked
