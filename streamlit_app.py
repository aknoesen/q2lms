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

# Test LaTeX processor integration
try:
    from modules.latex_processor import LaTeXProcessor, clean_text
    LATEX_PROCESSOR_AVAILABLE = True
except ImportError as e:
    LATEX_PROCESSOR_AVAILABLE = False

# Import existing backend modules
try:
    from database_transformer import transform_json_to_csv
    from simple_qti import csv_to_qti
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Question Database Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show module status
if LATEX_PROCESSOR_AVAILABLE:
    st.success("✅ LaTeX Processor ready!")
else:
    st.error("❌ LaTeX Processor not available")

if not BACKEND_AVAILABLE:
    st.error("⚠️ Backend modules not found. Please ensure database_transformer.py and simple_qti.py are in the 'modules' folder.")

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
    """Load and process JSON database content with automatic LaTeX processing"""
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
            return None, None, None, None
        
        # NEW: LaTeX Processing Step
        cleanup_reports = []
        processed_questions = questions  # Default to original questions
        
        if LATEX_PROCESSOR_AVAILABLE:
            with st.spinner("🧮 Processing LaTeX notation..."):
                processor = LaTeXProcessor()
                processed_questions, cleanup_reports = processor.process_question_database(questions)
                
                # Show cleanup summary
                if cleanup_reports:
                    questions_changed = len([r for r in cleanup_reports if r.changes_made])
                    total_unicode = sum(r.unicode_conversions for r in cleanup_reports)
                    total_fixes = sum(len(r.changes_made) for r in cleanup_reports)
                    
                    if questions_changed > 0:
                        st.success(f"🧮 LaTeX Processing Complete!")
                        st.info(f"""**Cleanup Summary:**
- Questions processed: {len(cleanup_reports)}
- Questions modified: {questions_changed}
- Unicode symbols converted: {total_unicode}
- Total formatting fixes: {total_fixes}
""")
                    else:
                        st.info("✨ LaTeX notation was already clean - no changes needed!")
                else:
                    st.info("✨ No LaTeX processing needed for this database")
        else:
            st.warning("⚠️ LaTeX processor not available - uploading without LaTeX processing")
        
        # Use processed questions for DataFrame conversion
        questions = processed_questions
        
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
        
        # Return processed data including cleanup reports
        return df, metadata, processed_questions, cleanup_reports
        
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON: {e}")
        return None, None, None, None
    except Exception as e:
        st.error(f"❌ Error processing database: {e}")
        return None, None, None, None

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
    """
    Enhanced LaTeX rendering for Streamlit with proper spacing and complete conversion
    Handles both math mode preservation and text mode symbol conversion
    """
    if not text or not isinstance(text, str):
        return text
    
    # Step 1: Preserve math environments ($$...$$ and $...$)
    math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'
    parts = re.split(math_pattern, text)
    
    # Step 2: LaTeX to Unicode conversion mapping
    latex_to_unicode = {
        # Greek letters
        r'\\Omega': 'Ω',
        r'\\mu': 'μ', 
        r'\\omega': 'ω',
        r'\\pi': 'π',
        r'\\alpha': 'α',
        r'\\beta': 'β',
        r'\\gamma': 'γ',
        r'\\delta': 'δ',
        r'\\theta': 'θ',
        r'\\lambda': 'λ',
        r'\\sigma': 'σ',
        r'\\phi': 'φ',
        r'\\tau': 'τ',
        
        # Mathematical symbols
        r'\\infty': '∞',
        r'\\pm': '±',
        r'\\mp': '∓',
        r'\\times': '×',
        r'\\div': '÷',
        r'\\neq': '≠',
        r'\\leq': '≤',
        r'\\geq': '≥',
        r'\\approx': '≈',
        r'\\angle': '∠',
        r'\\sqrt': '√',
        r'\\partial': '∂',
        r'\\nabla': '∇',
        r'\\sum': '∑',
        r'\\int': '∫',
        r'\\prod': '∏',
    }
    
    # Step 3: Process each part
    for i, part in enumerate(parts):
        # Only convert LaTeX in non-math parts (even indices)
        if i % 2 == 0:  # Non-math part
            
            # First handle specific patterns that need special treatment
            # Fix \muF pattern specifically
            part = re.sub(r'\\mu([A-Z])', r'μ\1', part)
            
            # Fix superscripts and subscripts with better patterns
            part = re.sub(r'\^{?([0-9])}?', lambda m: {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}.get(m.group(1), f'^{m.group(1)}'), part)
            part = re.sub(r'_{?([0-9])}?', lambda m: {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}.get(m.group(1), f'_{m.group(1)}'), part)
            
            # Fix multiplication symbol
            part = re.sub(r'\bx\b', '×', part)  # Replace standalone 'x' with multiplication
            part = re.sub(r'(\d)\s*x\s*(\d)', r'\1×\2', part)  # Replace 'x' between numbers
            
            # Apply general LaTeX to Unicode conversions
            for latex_cmd, unicode_char in latex_to_unicode.items():
                # Use proper word boundaries to avoid partial matches
                pattern = latex_cmd + r'(?=\s|$|[^a-zA-Z\\])'
                part = re.sub(pattern, unicode_char, part)
            
            # Step 4: Fix spacing around units and symbols - ENHANCED
            # Add space between numbers and Greek letters/symbols
            part = re.sub(r'(\d+)(Ω|μ|ω|π|α|β|γ|δ|θ|λ|σ|φ|τ|∞|°)', r'\1 \2', part)
            
            # Add space between numbers and units
            part = re.sub(r'(\d+)(Hz|V|A|W|F|H|Ω|S|m|s|J)', r'\1 \2', part)
            
            # Fix specific unit combinations with proper spacing
            part = re.sub(r'(\d+)\s*μ\s*([A-Z])', r'\1 μ\2', part)  # e.g., "10μF" → "10 μF"
            part = re.sub(r'(\d+)\s*m\s*([A-Z])', r'\1 m\2', part)  # e.g., "50mH" → "50 mH"
            part = re.sub(r'(\d+)\s*k\s*([A-Z])', r'\1 k\2', part)  # e.g., "2kΩ" → "2 kΩ"
            
            # Fix spacing around mathematical operators
            part = re.sub(r'(\w)\s*=\s*(\w)', r'\1 = \2', part)  # Ensure space around =
            part = re.sub(r'(\w)\s*\+\s*(\w)', r'\1 + \2', part)  # Ensure space around +
            part = re.sub(r'(\w)\s*-\s*(\w)', r'\1 - \2', part)   # Ensure space around -
            part = re.sub(r'(\w)\s*×\s*(\w)', r'\1 × \2', part)   # Ensure space around ×
            
            # Fix spacing around commas and periods in numbers
            part = re.sub(r'(\d),\s*(\d)', r'\1, \2', part)  # "120,000" stays, but "120, 000" gets space
            
            # Clean up LaTeX spacing commands
            part = re.sub(r'\\,', ' ', part)  # Convert LaTeX thin space
            part = re.sub(r'\\text\{([^}]+)\}', r'\1', part)  # Remove \text{} commands
            part = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', part)  # Remove \mathrm{} commands
            
            # Clean up extra spaces but preserve intentional spacing
            part = re.sub(r'\s{3,}', ' ', part)  # 3+ spaces to single space
            part = re.sub(r'([.!?])\s{2,}', r'\1 ', part)  # Clean up sentence endings
            part = part.strip()  # Remove leading/trailing spaces
        
        parts[i] = part
    
    # Step 5: Rejoin all parts
    result = ''.join(parts)
    
    # Step 6: Final cleanup - ensure math delimiters are properly spaced
    result = re.sub(r'([a-zA-Z0-9])\$', r'\1 $', result)  # Space before $
    result = re.sub(r'\$([a-zA-Z0-9])', r'$ \1', result)  # Space after $
    result = re.sub(r'([a-zA-Z0-9])\$\$', r'\1 $$', result)  # Space before $$
    result = re.sub(r'\$\$([a-zA-Z0-9])', r'$$ \1', result)  # Space after $$
    
    # Fix specific spacing issues around common patterns
    result = re.sub(r'(\w)\s*,\s*(\w)', r'\1, \2', result)  # Proper comma spacing
    result = re.sub(r'(\w)\s*\.\s*(\w)', r'\1. \2', result)  # Proper period spacing (when not decimals)
    result = re.sub(r'(\d+)\.\s*(\d+)', r'\1.\2', result)   # Keep decimal numbers together
    
    # Ensure parentheses have proper spacing
    result = re.sub(r'(\w)\s*\(\s*', r'\1(', result)  # Remove space before (
    result = re.sub(r'\s*\)\s*(\w)', r') \1', result)  # Space after )
    
    # Final cleanup of multiple spaces
    result = re.sub(r'\s{2,}', ' ', result)  # Multiple spaces to single
    
    return result

def display_question_preview(question_row):
    """Enhanced question preview with better LaTeX rendering"""
    
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
    
    # Question text with enhanced LaTeX rendering
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
                if choice_text == render_latex_in_text(question_row['Correct_Answer']):
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
    
    # Feedback with enhanced rendering
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


     # Enhanced Upload Interface for Phase 2A
     # Add this to your streamlit_app.py

def detect_database_format_and_type(json_content, filename):
    """
    Detect format version and database type from uploaded JSON
    Returns: (format_version, database_type, questions_count, metadata)
    """
    try:
        data = json.loads(json_content)
        
        # Determine structure type
        if isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
            metadata = data.get('metadata', {})
            structure_type = "structured"
        elif isinstance(data, list):
            questions = data
            metadata = {}
            structure_type = "simple_list"
        else:
            return None, "unknown", 0, {}
        
        # Detect format version
        format_version = "Unknown"
        if metadata.get('format_version'):
            format_version = metadata['format_version']
        elif len(questions) > 0:
            # Analyze first question to guess format
            sample_q = questions[0]
            if 'subtopic' in sample_q:
                format_version = "Phase Four"
            elif 'topic' in sample_q:
                format_version = "Phase Three"
            else:
                format_version = "Legacy"
        
        # Determine database type based on content analysis
        if len(questions) == 0:
            database_type = "empty"
        elif len(questions) < 10:
            database_type = "small_set"
        elif len(questions) < 50:
            database_type = "medium_set"
        else:
            database_type = "large_set"
        
        return format_version, database_type, len(questions), metadata
        
    except json.JSONDecodeError:
        return None, "invalid_json", 0, {}
    except Exception as e:
        return None, "error", 0, {}

def enhanced_upload_interface():
    """
    Enhanced upload interface with multiple file support and smart detection
    """
    st.markdown("## 📁 Database Upload & Management")
    
    # Upload mode selection
    upload_mode = st.radio(
        "Upload Mode:",
        ["Single Database", "Multiple Files (Batch)", "Append to Existing"],
        help="Choose how you want to upload and process your question databases"
    )
    
    if upload_mode == "Single Database":
        return handle_single_upload()
    elif upload_mode == "Multiple Files (Batch)":
        return handle_batch_upload()
    else:  # Append to Existing
        return handle_append_upload()

def handle_single_upload():
    """Handle single file upload with enhanced analysis"""
    
    uploaded_file = st.file_uploader(
        "📄 Upload Question Database (JSON)",
        type=['json'],
        help="Upload a single JSON question database file",
        key="single_upload"
    )
    
    if uploaded_file is not None:
        # Read and analyze the file
        content = uploaded_file.read().decode('utf-8')
        
        # Detect format and type
        format_version, db_type, question_count, metadata = detect_database_format_and_type(content, uploaded_file.name)
        
        if format_version is None:
            st.error(f"❌ Invalid file format: {db_type}")
            return None
        
        # Display file analysis
        with st.expander("📊 File Analysis", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Format", format_version)
            with col2:
                st.metric("Questions", question_count)
            with col3:
                st.metric("Type", db_type.replace('_', ' ').title())
            with col4:
                size_mb = len(content) / 1024 / 1024
                st.metric("Size", f"{size_mb:.2f} MB")
            
            if metadata:
                st.json(metadata, expanded=False)
        
        # Processing options
        st.markdown("### ⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_latex = st.checkbox("🧮 Auto-process LaTeX", value=True, help="Automatically clean LaTeX notation")
            validate_questions = st.checkbox("✅ Validate questions", value=True, help="Check for required fields and consistency")
        
        with col2:
            assign_new_ids = st.checkbox("🔄 Assign new IDs", value=False, help="Generate new question IDs (preserves originals)")
            preview_mode = st.checkbox("👁️ Preview mode", value=False, help="Show detailed processing steps")
        
        # Process button
        if st.button("🚀 Process Database", type="primary"):
            return process_single_database(content, {
                'filename': uploaded_file.name,
                'auto_latex': auto_latex,
                'validate_questions': validate_questions,
                'assign_new_ids': assign_new_ids,
                'preview_mode': preview_mode,
                'format_version': format_version,
                'metadata': metadata
            })
    
    return None

def handle_batch_upload():
    """Handle multiple file uploads for batch processing"""
    
    st.markdown("### 📚 Batch Upload (Multiple Files)")
    st.info("💡 Upload multiple JSON files to process them together or analyze differences")
    
    uploaded_files = st.file_uploader(
        "📄 Upload Multiple JSON Files",
        type=['json'],
        accept_multiple_files=True,
        help="Select multiple JSON question database files",
        key="batch_upload"
    )
    
    if uploaded_files and len(uploaded_files) > 0:
        st.success(f"📁 {len(uploaded_files)} files uploaded")
        
        # Analyze all files
        file_analysis = []
        total_questions = 0
        
        for uploaded_file in uploaded_files:
            content = uploaded_file.read().decode('utf-8')
            format_version, db_type, question_count, metadata = detect_database_format_and_type(content, uploaded_file.name)
            
            file_analysis.append({
                'filename': uploaded_file.name,
                'content': content,
                'format_version': format_version,
                'db_type': db_type,
                'question_count': question_count,
                'metadata': metadata,
                'size_kb': len(content) / 1024
            })
            total_questions += question_count
        
        # Display batch analysis
        st.markdown("### 📊 Batch Analysis")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(uploaded_files))
        with col2:
            st.metric("Total Questions", total_questions)
        with col3:
            avg_size = sum(f['size_kb'] for f in file_analysis) / len(file_analysis)
            st.metric("Avg Size", f"{avg_size:.1f} KB")
        
        # File details table
        st.markdown("### 📋 File Details")
        
        file_df = pd.DataFrame([
            {
                'Filename': f['filename'],
                'Format': f['format_version'],
                'Questions': f['question_count'],
                'Type': f['db_type'].replace('_', ' ').title(),
                'Size (KB)': f"{f['size_kb']:.1f}"
            }
            for f in file_analysis
        ])
        
        st.dataframe(file_df, use_container_width=True)
        
        # Batch processing options
        st.markdown("### ⚙️ Batch Processing Options")
        
        batch_operation = st.selectbox(
            "Choose batch operation:",
            [
                "Analyze Only (No Processing)",
                "Process Each File Separately", 
                "Merge All Files Into One Database",
                "Compare Files (Find Duplicates)",
                "Validate All Files"
            ]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            batch_latex = st.checkbox("🧮 Apply LaTeX processing to all", value=True)
            batch_validate = st.checkbox("✅ Validate all files", value=True)
        
        with col2:
            generate_report = st.checkbox("📊 Generate batch report", value=True)
            export_combined = st.checkbox("📦 Export combined results", value=False)
        
        if st.button("🚀 Execute Batch Operation", type="primary"):
            return process_batch_files(file_analysis, {
                'operation': batch_operation,
                'apply_latex': batch_latex,
                'validate_files': batch_validate,
                'generate_report': generate_report,
                'export_combined': export_combined
            })
    
    return None

def handle_append_upload():
    """Handle appending to existing database"""
    
    st.markdown("### ➕ Append to Existing Database")
    
    if 'df' not in st.session_state:
        st.warning("⚠️ No existing database loaded. Please load a database first using 'Single Database' mode.")
        return None
    
    # Show current database info
    current_df = st.session_state['df']
    st.info(f"📊 Current database: {len(current_df)} questions loaded")
    
    uploaded_file = st.file_uploader(
        "📄 Upload Additional Questions (JSON)",
        type=['json'],
        help="Upload questions to add to your current database",
        key="append_upload"
    )
    
    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        format_version, db_type, question_count, metadata = detect_database_format_and_type(content, uploaded_file.name)
        
        if format_version is None:
            st.error(f"❌ Invalid file format: {db_type}")
            return None
        
        # Show append analysis
        with st.expander("📊 Append Analysis", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Questions", len(current_df))
            with col2:
                st.metric("Adding Questions", question_count)
            with col3:
                st.metric("Total After", len(current_df) + question_count)
        
        # Append options
        st.markdown("### ⚙️ Append Options")
        
        col1, col2 = st.columns(2)
        with col1:
            handle_duplicates = st.selectbox(
                "Handle duplicates:",
                ["Skip duplicates", "Add with new IDs", "Replace existing", "Ask for each"]
            )
            
            renumber_ids = st.checkbox("🔄 Renumber all IDs sequentially", value=False)
        
        with col2:
            merge_metadata = st.checkbox("📋 Merge metadata", value=True)
            preserve_order = st.checkbox("📑 Preserve question order", value=True)
        
        if st.button("➕ Append to Database", type="primary"):
            return process_append_operation(content, {
                'filename': uploaded_file.name,
                'handle_duplicates': handle_duplicates,
                'renumber_ids': renumber_ids,
                'merge_metadata': merge_metadata,
                'preserve_order': preserve_order,
                'current_df': current_df
            })
    
    return None

def process_single_database(content, options):
    """Process a single database with enhanced options"""
    
    if options['preview_mode']:
        st.markdown("### 🔍 Processing Preview")
        
        with st.spinner("🔄 Analyzing database structure..."):
            # Show processing steps
            st.write("1. ✅ JSON parsing successful")
            st.write("2. ✅ Format detection complete")
            st.write("3. 🔄 Starting LaTeX processing...")
    
    # Use your existing load_database_from_json function with enhancements
    df, metadata, original_questions, cleanup_reports = load_database_from_json(content)
    
    if df is not None:
        # Apply additional processing based on options
        if options['assign_new_ids']:
            df = assign_new_question_ids(df)
        
        if options['validate_questions']:
            validation_results = validate_question_database(df)
            if validation_results['errors']:
                st.warning(f"⚠️ Found {len(validation_results['errors'])} validation issues")
                with st.expander("View Validation Issues"):
                    for error in validation_results['errors']:
                        st.write(f"• {error}")
        
        # Store enhanced data in session state
        st.session_state['df'] = df
        st.session_state['metadata'] = metadata
        st.session_state['original_questions'] = original_questions
        st.session_state['cleanup_reports'] = cleanup_reports
        st.session_state['filename'] = options['filename']
        st.session_state['processing_options'] = options
        
        st.success(f"✅ Database processed successfully! {len(df)} questions ready.")
        
        return df
    
    return None

def assign_new_question_ids(df):
    """Assign new sequential IDs while preserving originals"""
    df = df.copy()
    df['Original_ID'] = df['ID']  # Preserve original IDs
    df['ID'] = [f"Q_{i+1:05d}" for i in range(len(df))]  # New sequential IDs
    return df

def validate_question_database(df):
    """Validate question database for completeness and consistency"""
    errors = []
    warnings = []
    
    required_fields = ['ID', 'Type', 'Question_Text', 'Correct_Answer']
    
    for idx, row in df.iterrows():
        # Check required fields
        for field in required_fields:
            if pd.isna(row[field]) or str(row[field]).strip() == '':
                errors.append(f"Question {row['ID']}: Missing {field}")
        
        # Check question type specific requirements
        if row['Type'] == 'multiple_choice':
            choices = [row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
            if sum(1 for c in choices if c.strip()) < 2:
                warnings.append(f"Question {row['ID']}: Fewer than 2 choices for multiple choice")
        
        # Check points are numeric and positive
        try:
            points = float(row.get('Points', 0))
            if points <= 0:
                warnings.append(f"Question {row['ID']}: Points should be positive")
        except (ValueError, TypeError):
            errors.append(f"Question {row['ID']}: Points must be numeric")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0
    }

# You would add this function to your main() function in streamlit_app.py
def process_batch_files(file_analysis, options):
    """
    Process multiple files based on selected batch operation
    """
    operation = options['operation']
    
    st.markdown(f"### 🔄 Executing: {operation}")
    
    if operation == "Analyze Only (No Processing)":
        return display_batch_analysis_only(file_analysis)
    
    elif operation == "Process Each File Separately":
        return process_files_separately(file_analysis, options)
    
    elif operation == "Merge All Files Into One Database":
        return merge_all_files(file_analysis, options)
    
    elif operation == "Compare Files (Find Duplicates)":
        return compare_files_for_duplicates(file_analysis)
    
    elif operation == "Validate All Files":
        return validate_all_files(file_analysis)
    
    else:
        st.error(f"Unknown operation: {operation}")
        return None

def display_batch_analysis_only(file_analysis):
    """Display detailed analysis without processing"""
    
    st.markdown("### 📊 Detailed Batch Analysis")
    
    # Overall statistics
    total_questions = sum(f['question_count'] for f in file_analysis)
    total_size = sum(f['size_kb'] for f in file_analysis)
    formats = list(set(f['format_version'] for f in file_analysis))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Questions", total_questions)
    with col2:
        st.metric("Total Size", f"{total_size:.1f} KB")
    with col3:
        st.metric("Unique Formats", len(formats))
    with col4:
        avg_questions = total_questions / len(file_analysis) if file_analysis else 0
        st.metric("Avg Questions/File", f"{avg_questions:.1f}")
    
    # Format breakdown
    if len(formats) > 1:
        st.warning("⚠️ Multiple formats detected - consider standardizing")
        for fmt in formats:
            count = len([f for f in file_analysis if f['format_version'] == fmt])
            st.write(f"  • {fmt}: {count} files")
    
    # Individual file details
    st.markdown("### 📋 Individual File Analysis")
    for i, file_info in enumerate(file_analysis):
        with st.expander(f"📄 {file_info['filename']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Format:** {file_info['format_version']}")
                st.write(f"**Questions:** {file_info['question_count']}")
                st.write(f"**Type:** {file_info['db_type']}")
            with col2:
                st.write(f"**Size:** {file_info['size_kb']:.1f} KB")
                if file_info['metadata']:
                    st.json(file_info['metadata'], expanded=False)

def process_files_separately(file_analysis, options):
    """Process each file individually"""
    
    st.markdown("### 🔄 Processing Files Separately")
    
    processed_files = []
    
    for i, file_info in enumerate(file_analysis):
        st.markdown(f"#### Processing {i+1}/{len(file_analysis)}: {file_info['filename']}")
        
        with st.spinner(f"Processing {file_info['filename']}..."):
            # Process using existing function
            df, metadata, original_questions, cleanup_reports = load_database_from_json(file_info['content'])
            
            if df is not None:
                # Apply batch options
                if options['apply_latex']:
                    st.success(f"✅ LaTeX processing applied to {file_info['filename']}")
                
                if options['validate_files']:
                    validation_results = validate_question_database(df)
                    if validation_results['errors']:
                        st.warning(f"⚠️ {len(validation_results['errors'])} validation issues in {file_info['filename']}")
                
                processed_files.append({
                    'filename': file_info['filename'],
                    'df': df,
                    'metadata': metadata,
                    'original_questions': original_questions,
                    'cleanup_reports': cleanup_reports
                })
                
                st.success(f"✅ {file_info['filename']} processed successfully")
            else:
                st.error(f"❌ Failed to process {file_info['filename']}")
    
    # Store results in session state
    st.session_state['batch_processed_files'] = processed_files
    
    if options['generate_report']:
        generate_batch_processing_report(processed_files)
    
    st.success(f"🎉 Batch processing complete! {len(processed_files)} files processed successfully.")
    
    return processed_files

def merge_all_files(file_analysis, options):
    """Merge all files into a single database"""
    
    st.markdown("### 🔄 Merging All Files")
    
    all_questions = []
    all_metadata = []
    merge_stats = {
        'total_files': len(file_analysis),
        'total_questions': 0,
        'duplicates_found': 0,
        'id_conflicts': 0
    }
    
    for i, file_info in enumerate(file_analysis):
        st.write(f"📄 Processing {file_info['filename']}...")
        
        # Load the database
        df, metadata, original_questions, cleanup_reports = load_database_from_json(file_info['content'])
        
        if df is not None and original_questions:
            # Add source information to each question
            for question in original_questions:
                question['source_file'] = file_info['filename']
                question['source_index'] = i
            
            all_questions.extend(original_questions)
            all_metadata.append(metadata)
            merge_stats['total_questions'] += len(original_questions)
            
            st.success(f"✅ Added {len(original_questions)} questions from {file_info['filename']}")
        else:
            st.error(f"❌ Could not process {file_info['filename']}")
    
    if all_questions:
        # Create merged database structure
        merged_data = {
            "questions": all_questions,
            "metadata": {
                "generated_by": "Streamlit Question Database Manager - Batch Merge",
                "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "format_version": "Phase Four",
                "total_questions": len(all_questions),
                "source_files": [f['filename'] for f in file_analysis],
                "merge_stats": merge_stats
            }
        }
        
        # Convert to JSON and process normally
        merged_json = json.dumps(merged_data, indent=2)
        df, metadata, questions, cleanup_reports = load_database_from_json(merged_json)
        
        if df is not None:
            # Store in session state
            st.session_state['df'] = df
            st.session_state['metadata'] = metadata
            st.session_state['original_questions'] = questions
            st.session_state['cleanup_reports'] = cleanup_reports
            st.session_state['filename'] = f"merged_{len(file_analysis)}_files.json"
            
            st.success(f"🎉 Successfully merged {len(file_analysis)} files into {len(all_questions)} questions!")
            
            # Show merge summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files Merged", len(file_analysis))
            with col2:
                st.metric("Total Questions", len(all_questions))
            with col3:
                st.metric("Average per File", f"{len(all_questions)/len(file_analysis):.1f}")
            
            return df
    
    st.error("❌ No questions could be merged")
    return None

def compare_files_for_duplicates(file_analysis):
    """Compare files to find duplicate questions"""
    
    st.markdown("### 🔍 Comparing Files for Duplicates")
    
    # This is a simplified comparison - you could make it more sophisticated
    all_questions_data = []
    
    for file_info in file_analysis:
        df, metadata, original_questions, cleanup_reports = load_database_from_json(file_info['content'])
        if df is not None:
            for idx, row in df.iterrows():
                all_questions_data.append({
                    'source_file': file_info['filename'],
                    'question_text': row['Question_Text'],
                    'correct_answer': row['Correct_Answer'],
                    'topic': row.get('Topic', ''),
                    'title': row.get('Title', '')
                })
    
    # Find potential duplicates based on question text similarity
    duplicates = []
    for i, q1 in enumerate(all_questions_data):
        for j, q2 in enumerate(all_questions_data[i+1:], i+1):
            # Simple duplicate detection - could be made more sophisticated
            if (q1['question_text'].strip().lower() == q2['question_text'].strip().lower() and 
                q1['source_file'] != q2['source_file']):
                duplicates.append((q1, q2))
    
    if duplicates:
        st.warning(f"⚠️ Found {len(duplicates)} potential duplicate questions across files")
        
        for i, (q1, q2) in enumerate(duplicates[:10]):  # Show first 10
            with st.expander(f"Duplicate {i+1}: {q1['title'][:50]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**File:** {q1['source_file']}")
                    st.write(f"**Question:** {q1['question_text'][:100]}...")
                with col2:
                    st.write(f"**File:** {q2['source_file']}")
                    st.write(f"**Question:** {q2['question_text'][:100]}...")
        
        if len(duplicates) > 10:
            st.info(f"... and {len(duplicates) - 10} more duplicates")
    else:
        st.success("✅ No obvious duplicates found between files")
    
    return duplicates

def validate_all_files(file_analysis):
    """Validate all files and show results"""
    
    st.markdown("### ✅ Validating All Files")
    
    validation_summary = {
        'total_files': len(file_analysis),
        'valid_files': 0,
        'files_with_errors': 0,
        'total_errors': 0,
        'total_warnings': 0
    }
    
    for file_info in file_analysis:
        st.markdown(f"#### Validating {file_info['filename']}")
        
        df, metadata, original_questions, cleanup_reports = load_database_from_json(file_info['content'])
        
        if df is not None:
            validation_results = validate_question_database(df)
            
            if validation_results['is_valid']:
                st.success(f"✅ {file_info['filename']} - All validations passed")
                validation_summary['valid_files'] += 1
            else:
                st.error(f"❌ {file_info['filename']} - {len(validation_results['errors'])} errors found")
                validation_summary['files_with_errors'] += 1
                validation_summary['total_errors'] += len(validation_results['errors'])
                
                # Show first few errors
                for error in validation_results['errors'][:3]:
                    st.write(f"  • {error}")
                
                if len(validation_results['errors']) > 3:
                    st.write(f"  • ... and {len(validation_results['errors']) - 3} more errors")
            
            if validation_results['warnings']:
                st.warning(f"⚠️ {len(validation_results['warnings'])} warnings")
                validation_summary['total_warnings'] += len(validation_results['warnings'])
        else:
            st.error(f"❌ Could not load {file_info['filename']}")
    
    # Summary
    st.markdown("### 📊 Validation Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valid Files", validation_summary['valid_files'])
    with col2:
        st.metric("Files with Errors", validation_summary['files_with_errors'])
    with col3:
        st.metric("Total Errors", validation_summary['total_errors'])
    with col4:
        st.metric("Total Warnings", validation_summary['total_warnings'])
    
    return validation_summary

def generate_batch_processing_report(processed_files):
    """Generate a comprehensive batch processing report"""
    
    st.markdown("### 📊 Batch Processing Report")
    
    if not processed_files:
        st.warning("No files were successfully processed")
        return
    
    # Overall statistics
    total_questions = sum(len(f['df']) for f in processed_files)
    
    report_data = {
        'processing_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'files_processed': len(processed_files),
        'total_questions': total_questions,
        'files': []
    }
    
    for file_info in processed_files:
        df = file_info['df']
        file_report = {
            'filename': file_info['filename'],
            'questions': len(df),
            'topics': df['Topic'].nunique(),
            'difficulty_distribution': df['Difficulty'].value_counts().to_dict(),
            'type_distribution': df['Type'].value_counts().to_dict(),
            'total_points': df['Points'].sum()
        }
        report_data['files'].append(file_report)
    
    # Display report
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", len(processed_files))
    with col2:
        st.metric("Total Questions", total_questions)
    with col3:
        avg_questions = total_questions / len(processed_files)
        st.metric("Avg Questions/File", f"{avg_questions:.1f}")
    
    # File-by-file breakdown
    for file_report in report_data['files']:
        with st.expander(f"📄 {file_report['filename']} - {file_report['questions']} questions"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Topics:** {file_report['topics']}")
                st.write(f"**Total Points:** {file_report['total_points']}")
            with col2:
                st.write("**Difficulty:**")
                for diff, count in file_report['difficulty_distribution'].items():
                    st.write(f"  • {diff}: {count}")

def process_append_operation(content, options):
    """Process appending new questions to existing database"""
    
    st.markdown("### ➕ Appending to Existing Database")
    
    # Load the new questions
    df_new, metadata_new, questions_new, cleanup_reports_new = load_database_from_json(content)
    
    if df_new is None:
        st.error("❌ Could not load new questions")
        return None
    
    # Get current database
    df_current = options['current_df']
    
    st.write(f"📊 Current database: {len(df_current)} questions")
    st.write(f"📄 Adding from {options['filename']}: {len(df_new)} questions")
    
    # Handle duplicate detection (simplified)
    duplicate_handling = options['handle_duplicates']
    
    if duplicate_handling == "Skip duplicates":
        # Simple duplicate detection based on question text
        existing_texts = set(df_current['Question_Text'].str.strip().str.lower())
        new_texts = df_new['Question_Text'].str.strip().str.lower()
        
        duplicates_mask = new_texts.isin(existing_texts)
        df_to_add = df_new[~duplicates_mask]
        
        if duplicates_mask.sum() > 0:
            st.warning(f"⚠️ Skipped {duplicates_mask.sum()} duplicate questions")
        
        st.info(f"📊 Adding {len(df_to_add)} unique questions")
    
    else:
        df_to_add = df_new
        st.info(f"📊 Adding all {len(df_to_add)} questions")
    
    if len(df_to_add) > 0:
        # Combine databases
        if options['renumber_ids']:
            # Renumber all IDs sequentially
            combined_df = pd.concat([df_current, df_to_add], ignore_index=True)
            combined_df['ID'] = [f"Q_{i+1:05d}" for i in range(len(combined_df))]
        else:
            # Keep existing IDs, assign new ones for added questions
            max_id = len(df_current)
            df_to_add = df_to_add.copy()
            df_to_add['ID'] = [f"Q_{max_id + i + 1:05d}" for i in range(len(df_to_add))]
            combined_df = pd.concat([df_current, df_to_add], ignore_index=True)
        
        # Update session state
        st.session_state['df'] = combined_df
        st.session_state['filename'] = f"appended_{options['filename']}"
        
        st.success(f"✅ Successfully appended {len(df_to_add)} questions!")
        st.info(f"📊 Total database size: {len(combined_df)} questions")
        
        return combined_df
    
    else:
        st.warning("⚠️ No questions to append")
        return None 

def add_prominent_tab_css():
    """
    Just add this CSS to make existing tabs more prominent
    """
    st.markdown("""
    <style>
    /* Make tabs more prominent */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #f1f3f4;
        padding: 12px;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        padding: 15px 25px;
        background-color: white;
        border-radius: 10px;
        color: #333;
        font-weight: 700;
        font-size: 17px;
        border: 2px solid #e0e0e0;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 12px rgba(0,0,0,0.15);
        border-color: #1f77b4;
        background-color: #f8f9ff;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f77b4, #0d6efd);
        color: white !important;
        border-color: #0d6efd;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(31, 119, 180, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)                

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    # 📊 Question Database Manager
    
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    
    ---
    """)
     # ADD THIS ONE LINE:
    add_prominent_tab_css()

    # Enhanced Upload Interface - ALWAYS visible
    enhanced_upload_interface()
    
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


if __name__ == "__main__":
    main()