import streamlit as st
import plotly.express as px

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

def create_summary_charts(df):
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
        st.plotly_chart(fig_topics, use_container_width=True)
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
        st.plotly_chart(fig_difficulty, use_container_width=True)
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
        st.plotly_chart(fig_subtopics, use_container_width=True)
    st.markdown("### 📝 Question Types")
    type_counts = df['Type'].value_counts()
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_types = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            title="Questions by Type"
        )
        st.plotly_chart(fig_types, use_container_width=True)
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
