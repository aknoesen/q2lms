#!/usr/bin/env python3
"""
Question Database Manager - Streamlit Web Interface
Replaces MATLAB QuestionDatabaseManager with modern web interface
Supports Phase 3 & 4 JSON formats with subtopic organization
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import zipfile
import os
import io
import base64
from datetime import datetime
import re

# Import the existing Python modules from the modules directory
import sys
import os

# Add modules directory to Python path
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

try:
    from database_transformer import transform_json_to_csv
    from simple_qti import csv_to_qti
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    st.error("⚠️ Backend modules not found. Please ensure database_transformer.py and simple_qti.py are in the 'modules' folder.")

# Page configuration
st.set_page_config(
    page_title="Question Database Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better LaTeX rendering and styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .latex-preview {
        background-color: #fafafa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        font-family: 'Times New Roman', serif;
    }
    .question-preview {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def load_database_from_json(json_content):
    """Load and process JSON database content"""
    try:
        data = json.loads(json_content)
        
        # Handle both formats: {"questions": [...]} or direct [...]
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
            metadata = data.get('metadata', {})
        elif isinstance(data, list):
            questions = data
            metadata = {}
        else:
            st.error("❌ Unexpected JSON structure")
            return None, None, None
        
        # Convert to DataFrame using same logic as database_transformer.py
        rows = []
        for i, q in enumerate(questions):
            # Generate question ID
            question_id = f"Q_{i+1:05d}"
            
            # Extract basic fields with defaults and handle None values
            question_type = q.get('type', 'multiple_choice')
            title = q.get('title', f"Question {i+1}")
            question_text = q.get('question_text', '')
            correct_answer = q.get('correct_answer', '')
            points = q.get('points', 1)
            tolerance = q.get('tolerance', 0.05)
            topic = q.get('topic', 'General')
            subtopic = q.get('subtopic', '')
            difficulty = q.get('difficulty', 'Easy')
            
            # Handle image file (could be list, string, or None)
            image_file = q.get('image_file', [])
            if image_file is None:
                image_file = ''
            elif isinstance(image_file, list):
                image_file = image_file[0] if image_file else ''
            elif not isinstance(image_file, str):
                image_file = str(image_file) if image_file else ''
            
            # Extract feedback fields (handle None values)
            feedback_correct = q.get('feedback_correct', '') or ''
            feedback_incorrect = q.get('feedback_incorrect', '') or ''
            general_feedback = feedback_correct  # Use correct feedback as default
            
            # Handle choices for multiple choice questions (handle None values)
            choices = q.get('choices', [])
            if choices is None:
                choices = []
            elif not isinstance(choices, list):
                choices = []
            
            choice_a = choices[0] if len(choices) > 0 else ''
            choice_b = choices[1] if len(choices) > 1 else ''
            choice_c = choices[2] if len(choices) > 2 else ''
            choice_d = choices[3] if len(choices) > 3 else ''
            
            # Handle None values for tolerance and points
            if tolerance is None:
                tolerance = 0.05
            if points is None:
                points = 1
            
            # Convert correct_answer to string
            if correct_answer is None:
                correct_answer = ''
            else:
                correct_answer = str(correct_answer)
            
            # Create row
            row = {
                'ID': question_id,
                'Type': question_type,
                'Title': title,
                'Question_Text': question_text,
                'Choice_A': choice_a,
                'Choice_B': choice_b,
                'Choice_C': choice_c,
                'Choice_D': choice_d,
                'Correct_Answer': correct_answer,
                'Points': points,
                'Tolerance': tolerance,
                'Feedback': general_feedback,
                'Correct_Feedback': feedback_correct,
                'Incorrect_Feedback': feedback_incorrect,
                'Image_File': image_file,
                'Topic': topic,
                'Subtopic': subtopic,
                'Difficulty': difficulty
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df, metadata, questions
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON: {e}")
        return None, None, None
    except Exception as e:
        st.error(f"❌ Error processing database: {e}")
        return None, None, None

def display_database_summary(df, metadata):
    """Display comprehensive database summary"""
    st.markdown('<div class="main-header">📊 Database Overview</div>', unsafe_allow_html=True)
    
    # Key metrics in columns
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
    
    # Metadata information
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
    """Create interactive summary charts"""
    
    # Topics and Subtopics breakdown
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
    
    # Subtopics (if available)
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
    
    # Question types
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
    """Apply filtering interface and return filtered dataframe"""
    st.sidebar.markdown("## 🔍 Filter Questions")
    
    # Create a copy for filtering
    filtered_df = df.copy()
    
    # Topic filter
    topics = ['All'] + sorted(df['Topic'].unique().tolist())
    selected_topic = st.sidebar.selectbox("📚 Topic", topics)
    
    if selected_topic != 'All':
        filtered_df = filtered_df[filtered_df['Topic'] == selected_topic]
    
    # Subtopic filter (dynamic based on topic selection)
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
    
    # Difficulty filter
    difficulties = ['All'] + sorted(df['Difficulty'].unique().tolist())
    selected_difficulty = st.sidebar.selectbox("⚡ Difficulty", difficulties)
    
    if selected_difficulty != 'All':
        filtered_df = filtered_df[filtered_df['Difficulty'] == selected_difficulty]
    
    # Question type filter
    types = ['All'] + sorted(df['Type'].unique().tolist())
    selected_type = st.sidebar.selectbox("📝 Question Type", types)
    
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]
    
    # Points filter
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
    
    # Search functionality
    search_term = st.sidebar.text_input("🔍 Search in Questions", "")
    if search_term:
        mask = (
            filtered_df['Title'].str.contains(search_term, case=False, na=False) |
            filtered_df['Question_Text'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # Show filter summary
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**📊 Results: {len(filtered_df)} questions**")
    if len(filtered_df) < len(df):
        st.sidebar.markdown(f"*Filtered from {len(df)} total*")
    
    return filtered_df

def render_latex_in_text(text):
    """Convert LaTeX notation to display format"""
    if not text or not isinstance(text, str):
        return text
    
    # Handle $$...$$ (display math)
    text = re.sub(r'\$\$(.*?)\$\$', r'$$\1$$', text)
    # Handle $...$ (inline math) 
    text = re.sub(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', r'$\1$', text)
    
    return text

def display_question_preview(question_row):
    """Display a single question with proper formatting"""
    
    st.markdown('<div class="question-preview">', unsafe_allow_html=True)
    
    # Header with metadata
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{question_row['Title']}**")
    with col2:
        st.markdown(f"🏷️ **{question_row['Type'].replace('_', ' ').title()}**")
    with col3:
        difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
        difficulty_icon = difficulty_colors.get(question_row['Difficulty'], '⚪')
        st.markdown(f"{difficulty_icon} **{question_row['Difficulty']}**")
    with col4:
        st.markdown(f"**{question_row['Points']} pts**")
    
    # Topic and subtopic info
    topic_info = f"📚 {question_row['Topic']}"
    if question_row['Subtopic'] and question_row['Subtopic'] not in ['', 'N/A']:
        topic_info += f" → {question_row['Subtopic']}"
    st.markdown(f"*{topic_info}*")
    
    st.markdown("---")
    
    # Question text with LaTeX rendering
    question_text = render_latex_in_text(question_row['Question_Text'])
    st.markdown(f"**Question:** {question_text}")
    
    # Handle different question types
    if question_row['Type'] == 'multiple_choice':
        st.markdown("**Choices:**")
        choices = ['A', 'B', 'C', 'D']
        for choice in choices:
            choice_text = question_row[f'Choice_{choice}']
            if choice_text and choice_text.strip():
                choice_text = render_latex_in_text(choice_text)
                if choice_text == question_row['Correct_Answer']:
                    st.markdown(f"• **{choice}:** {choice_text} ✅")
                else:
                    st.markdown(f"• **{choice}:** {choice_text}")
    
    elif question_row['Type'] == 'numerical':
        correct_answer = render_latex_in_text(str(question_row['Correct_Answer']))
        st.markdown(f"**Correct Answer:** {correct_answer}")
        if question_row['Tolerance'] and float(question_row['Tolerance']) > 0:
            st.markdown(f"**Tolerance:** ±{question_row['Tolerance']}")
    
    elif question_row['Type'] == 'true_false':
        st.markdown(f"**Correct Answer:** {question_row['Correct_Answer']}")
    
    elif question_row['Type'] == 'fill_in_blank':
        correct_answer = render_latex_in_text(str(question_row['Correct_Answer']))
        st.markdown(f"**Correct Answer:** {correct_answer}")
    
    # Feedback
    if question_row['Correct_Feedback']:
        with st.expander("💡 View Feedback"):
            correct_feedback = render_latex_in_text(question_row['Correct_Feedback'])
            st.markdown(f"**Correct:** {correct_feedback}")
            if question_row['Incorrect_Feedback']:
                incorrect_feedback = render_latex_in_text(question_row['Incorrect_Feedback'])
                st.markdown(f"**Incorrect:** {incorrect_feedback}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_download_link(data, filename, link_text):
    """Create a download link for data"""
    if isinstance(data, pd.DataFrame):
        csv_data = data.to_csv(index=False)
        b64 = base64.b64encode(csv_data.encode()).decode()
    else:
        b64 = base64.b64encode(data).decode()
    
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def export_to_csv(df, filename="filtered_questions.csv"):
    """Export filtered questions to CSV"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )

def create_qti_package(df, original_questions, quiz_title):
    """Create QTI package from filtered questions"""
    if not BACKEND_AVAILABLE:
        st.error("❌ Backend modules not available for QTI generation")
        return
    
    try:
        with st.spinner("🔄 Creating QTI package..."):
            # Create temporary JSON file with filtered questions
            filtered_question_ids = df['ID'].tolist()
            
            # Map back to original questions
            filtered_questions = []
            for i, q in enumerate(original_questions):
                question_id = f"Q_{i+1:05d}"
                if question_id in filtered_question_ids:
                    filtered_questions.append(q)
            
            # Create temporary JSON file
            temp_json = {
                "questions": filtered_questions,
                "metadata": {
                    "generated_by": "Streamlit Question Database Manager",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_questions": len(filtered_questions),
                    "filter_applied": True
                }
            }
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(temp_json, temp_file, indent=2)
                temp_json_path = temp_file.name
            
            # Convert JSON to CSV
            temp_csv_path = temp_json_path.replace('.json', '.csv')
            success = transform_json_to_csv(temp_json_path, temp_csv_path)
            
            if success:
                # Create QTI package
                qti_success = csv_to_qti(temp_csv_path, quiz_title)
                
                if qti_success:
                    # Read the created ZIP file
                    zip_filename = f"{quiz_title}.zip"
                    if os.path.exists(zip_filename):
                        with open(zip_filename, 'rb') as f:
                            zip_data = f.read()
                        
                        # Offer download
                        st.success(f"✅ QTI package created successfully!")
                        st.download_button(
                            label="📦 Download QTI Package",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip"
                        )
                        
                        # Cleanup
                        os.unlink(zip_filename)
                    else:
                        st.error("❌ QTI package file not found")
                else:
                    st.error("❌ Failed to create QTI package")
            else:
                st.error("❌ Failed to convert JSON to CSV")
            
            # Cleanup temporary files
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
            if os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)
                
    except Exception as e:
        st.error(f"❌ Error creating QTI package: {str(e)}")

def quiz_builder_interface(df, original_questions):
    """Advanced quiz builder interface"""
    st.markdown("### 🎯 Custom Quiz Builder")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Quiz Configuration:**")
        quiz_title = st.text_input("Quiz Title", "Custom_Quiz")
        target_count = st.number_input("Number of Questions", min_value=1, max_value=len(df), value=min(10, len(df)))
        
        # Advanced criteria
        use_random = st.checkbox("Randomize Selection", True)
        enforce_distribution = st.checkbox("Enforce Difficulty Distribution", False)
        
        if enforce_distribution:
            easy_pct = st.slider("Easy %", 0, 100, 40)
            medium_pct = st.slider("Medium %", 0, 100, 40)
            hard_pct = 100 - easy_pct - medium_pct
            st.write(f"Hard %: {hard_pct}")
    
    with col2:
        st.markdown("**Preview Selection:**")
        
        if st.button("🎲 Generate Quiz"):
            if enforce_distribution and len(df) >= target_count:
                # Calculate target counts for each difficulty
                easy_target = int(target_count * easy_pct / 100)
                medium_target = int(target_count * medium_pct / 100)
                hard_target = target_count - easy_target - medium_target
                
                # Sample from each difficulty level
                quiz_questions = pd.DataFrame()
                
                for difficulty, target in [('Easy', easy_target), ('Medium', medium_target), ('Hard', hard_target)]:
                    if target > 0:
                        available = df[df['Difficulty'] == difficulty]
                        if len(available) > 0:
                            sample_size = min(target, len(available))
                            if use_random:
                                sample = available.sample(n=sample_size)
                            else:
                                sample = available.head(sample_size)
                            quiz_questions = pd.concat([quiz_questions, sample])
                
                st.session_state['quiz_questions'] = quiz_questions
            else:
                # Simple random or sequential sampling
                if use_random:
                    quiz_questions = df.sample(n=min(target_count, len(df)))
                else:
                    quiz_questions = df.head(target_count)
                st.session_state['quiz_questions'] = quiz_questions
    
    # Display generated quiz
    if 'quiz_questions' in st.session_state:
        quiz_df = st.session_state['quiz_questions']
        st.markdown(f"**Generated Quiz: {len(quiz_df)} questions**")
        
        # Quiz statistics
        quiz_stats_col1, quiz_stats_col2, quiz_stats_col3 = st.columns(3)
        with quiz_stats_col1:
            st.metric("Total Points", quiz_df['Points'].sum())
        with quiz_stats_col2:
            difficulty_dist = quiz_df['Difficulty'].value_counts()
            st.write("**Difficulty:**")
            for diff, count in difficulty_dist.items():
                st.write(f"• {diff}: {count}")
        with quiz_stats_col3:
            topic_dist = quiz_df['Topic'].value_counts()
            st.write("**Topics:**")
            for topic, count in topic_dist.items():
                st.write(f"• {topic}: {count}")
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            export_to_csv(quiz_df, f"{quiz_title}.csv")
        with col2:
            if st.button("📦 Create QTI Package"):
                create_qti_package(quiz_df, original_questions, quiz_title)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    # 📊 Question Database Manager
    
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    
    ---
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "📁 Upload Question Database (JSON)",
        type=['json'],
        help="Upload a Phase 3 or Phase 4 JSON question database file"
    )
    
    if uploaded_file is not None:
        # Load and process the database
        content = uploaded_file.read().decode('utf-8')
        
        with st.spinner("🔄 Processing database..."):
            df, metadata, original_questions = load_database_from_json(content)
        
        if df is not None:
            # Store in session state
            st.session_state['df'] = df
            st.session_state['metadata'] = metadata
            st.session_state['original_questions'] = original_questions
            st.session_state['filename'] = uploaded_file.name
            
            st.success(f"✅ Database loaded successfully! {len(df)} questions processed.")
    
    # Main interface (only show if database is loaded)
    if 'df' in st.session_state:
        df = st.session_state['df']
        metadata = st.session_state['metadata']
        original_questions = st.session_state['original_questions']
        
        # Apply filters
        filtered_df = apply_filters(df)
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Browse Questions", "🎯 Quiz Builder", "📥 Export"])
        
        with tab1:
            display_database_summary(df, metadata)
            st.markdown("---")
            create_summary_charts(df)
        
        with tab2:
            st.markdown(f"### 📋 Filtered Questions ({len(filtered_df)} results)")
            
            if len(filtered_df) > 0:
                # Pagination
                items_per_page = st.selectbox("Questions per page", [5, 10, 20, 50], index=1)
                total_pages = (len(filtered_df) - 1) // items_per_page + 1
                
                if total_pages > 1:
                    page = st.selectbox("Page", range(1, total_pages + 1))
                    start_idx = (page - 1) * items_per_page
                    end_idx = start_idx + items_per_page
                    page_df = filtered_df.iloc[start_idx:end_idx]
                else:
                    page_df = filtered_df
                
                # Display questions
                for idx, question in page_df.iterrows():
                    display_question_preview(question)
                    st.markdown("---")
            else:
                st.warning("🔍 No questions match the current filters.")
        
        with tab3:
            if len(filtered_df) > 0:
                quiz_builder_interface(filtered_df, original_questions)
            else:
                st.warning("🔍 No questions available for quiz building. Adjust your filters.")
        
        with tab4:
            st.markdown("### 📥 Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 CSV Export**")
                st.markdown("Export filtered questions as CSV file for further analysis or backup.")
                if len(filtered_df) > 0:
                    export_to_csv(filtered_df, f"filtered_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                else:
                    st.warning("No questions to export")
            
            with col2:
                st.markdown("**📦 QTI Package**")
                st.markdown("Create Canvas-ready QTI package for direct import into your LMS.")
                
                if len(filtered_df) > 0:
                    qti_title = st.text_input("QTI Package Name", "Question_Package")
                    if st.button("🚀 Generate QTI Package"):
                        create_qti_package(filtered_df, original_questions, qti_title)
                else:
                    st.warning("No questions to export")
            
            # Export summary
            st.markdown("---")
            st.markdown("### 📋 Export Summary")
            if len(filtered_df) > 0:
                difficulty_counts = filtered_df['Difficulty'].value_counts()
                type_counts = filtered_df['Type'].value_counts()
                topic_counts = filtered_df['Topic'].value_counts()
                
                total_points = filtered_df['Points'].sum()
                avg_points = filtered_df['Points'].mean()
                
                st.info(f"""**Current Selection:**
- **Questions:** {len(filtered_df)}
- **Total Points:** {total_points:.0f}
- **Average Points:** {avg_points:.1f}

**Difficulty Distribution:**
{chr(10).join([f"- {diff}: {count}" for diff, count in difficulty_counts.items()])}

**Question Types:**
{chr(10).join([f"- {qtype}: {count}" for qtype, count in type_counts.items()])}

**Topics Covered:**
{chr(10).join([f"- {topic}: {count}" for topic, count in topic_counts.items()])}""")
            else:
                st.warning("No questions selected for export")
    
    else:
        # Landing page content
        st.markdown("""
        ## 🚀 Getting Started
        
        **Upload a JSON question database to begin:**
        
        1. **📁 Select File** - Choose your Phase 3 or Phase 4 JSON database
        2. **🔍 Filter Questions** - Use the sidebar to filter by topic, difficulty, type, etc.
        3. **👀 Preview Questions** - Browse and review questions with proper LaTeX rendering
        4. **🎯 Build Quizzes** - Create custom quizzes with advanced criteria
        5. **📥 Export** - Download CSV files or Canvas-ready QTI packages
        
        ---
        
        ### ✨ Key Features
        
        **🔍 Advanced Filtering:**
        - Filter by topic, subtopic, difficulty, question type
        - Search within question text and titles
        - Point value range selection
        
        **📊 Analytics & Visualization:**
        - Interactive charts showing question distribution
        - Comprehensive database statistics
        - Real-time filter result counts
        
        **🎯 Smart Quiz Builder:**
        - Custom question count and criteria
        - Difficulty distribution enforcement
        - Random or sequential sampling
        
        **📥 Flexible Export Options:**
        - CSV export for analysis and backup
        - Direct QTI package generation for Canvas
        - Preserves all metadata and LaTeX formatting
        
        **🧮 Mathematical Notation Support:**
        - Proper LaTeX rendering in question preview
        - Complex mathematical expressions supported
        - Canvas-compatible equation formatting
        
        ---
        
        ### 📚 Supported Question Types
        
        - **Multiple Choice** - Traditional A/B/C/D questions
        - **Numerical** - Mathematical calculations with tolerance
        - **True/False** - Binary choice questions
        - **Fill in the Blank** - Text-based answers
        
        ### 🗃️ Database Format Support
        
        - **Phase 3 Format** - Basic topic organization
        - **Phase 4 Format** - Enhanced with subtopic support
        - **Automatic Detection** - Seamlessly handles both formats
        
        """)
        
        # Sample database info
        st.markdown("### 📋 Sample Database Structure")
        with st.expander("View Expected JSON Format"):
            st.code('''
{
  "questions": [
    {
      "type": "multiple_choice",
      "title": "Basic Ohm's Law Application",
      "question_text": "A circuit has a 12V battery connected to a 4Ω resistor...",
      "choices": ["3A", "48A", "8A", "0.33A"],
      "correct_answer": "3A",
      "points": 2,
      "tolerance": null,
      "feedback_correct": "Correct! Using Ohm's Law: I = V/R = 12V/4Ω = 3A",
      "feedback_incorrect": "Remember Ohm's Law: I = V/R...",
      "image_file": null,
      "topic": "Circuit Analysis",
      "subtopic": "Basic Laws",
      "difficulty": "Easy"
    }
  ],
  "metadata": {
    "subject": "Electrical Engineering",
    "format_version": "Phase Four",
    "topics_covered": ["Circuit Analysis", "Signal Processing"],
    "subtopics_covered": ["Basic Laws", "Op-Amps"]
  }
}
            ''', language='json')

if __name__ == "__main__":
    main()