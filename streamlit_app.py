#!/usr/bin/env python3
"""
Question Database Manager - Main Streamlit Application (Modular Version)
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

# Import modules
import sys
import os

# Add modules directory to Python path
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Import our modular components
try:
    from modules.session_manager import (
        initialize_session_state, clear_session_state, 
        display_enhanced_database_status, has_active_database
    )
    from modules.upload_handler import smart_upload_interface
    from modules.database_processor import (
        save_question_changes, delete_question, validate_single_question
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Module import error: {e}")
    SESSION_MANAGER_AVAILABLE = False

# Test LaTeX processor integration
try:
    from modules.latex_processor import LaTeXProcessor, clean_text
    LATEX_PROCESSOR_AVAILABLE = True
except ImportError as e:
    LATEX_PROCESSOR_AVAILABLE = False

# Import existing backend modules
try:
    from utilities.database_transformer import transform_json_to_csv
    from utilities.simple_qti import csv_to_qti
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
if SESSION_MANAGER_AVAILABLE:
    st.success("✅ Modular session management ready!")
else:
    st.error("❌ Session management modules not available")

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

def render_latex_in_text(text):
    """
    Enhanced LaTeX rendering for Streamlit with comprehensive mathematical notation support
    """
    if not text or not isinstance(text, str):
        return text
    
    # Preserve existing Unicode symbols first
    unicode_preservations = {
        'π': '###PI###',
        'Ω': '###OMEGA###', 
        'μ': '###MU###',
        'α': '###ALPHA###',
        'β': '###BETA###',
        'γ': '###GAMMA###',
        'δ': '###DELTA###',
        'θ': '###THETA###',
        'λ': '###LAMBDA###',
        'σ': '###SIGMA###',
        'φ': '###PHI###',
        'τ': '###TAU###',
        '·': '###DOT###',
        '×': '###TIMES###',
        '±': '###PLUSMINUS###'
    }
    
    # Temporarily replace Unicode with placeholders
    protected_text = text
    for unicode_char, placeholder in unicode_preservations.items():
        protected_text = protected_text.replace(unicode_char, placeholder)

    # Step 1: Preserve math environments ($$...$$ and $...$)
    math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'
    parts = re.split(math_pattern, protected_text)
    
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
            
            # Handle specific patterns that need special treatment
            part = re.sub(r'\\mu([A-Z])', r'μ\1', part)
            
            # Fix superscripts and subscripts with better patterns
            part = re.sub(r'\^{?([0-9])}?', lambda m: {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}.get(m.group(1), f'^{m.group(1)}'), part)
            part = re.sub(r'_{?([0-9])}?', lambda m: {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'}.get(m.group(1), f'_{m.group(1)}'), part)
            
            # Apply general LaTeX to Unicode conversions
            for latex_cmd, unicode_char in latex_to_unicode.items():
                if latex_cmd.startswith(r'\\'):
                    clean_cmd = latex_cmd.replace(r'\\', '\\\\')
                    pattern = clean_cmd + r'(?![a-zA-Z])'
                    part = re.sub(pattern, unicode_char, part)
            
            # Fix spacing around units and symbols
            part = re.sub(r'(\d+)(Ω|μ|ω|π|α|β|γ|δ|θ|λ|σ|φ|τ|∞|°)', r'\1 \2', part)
            part = re.sub(r'(\d+)(Hz|V|A|W|F|H|Ω|S|m|s|J)', r'\1 \2', part)
            part = re.sub(r'(\d+)\s*μ\s*([A-Z])', r'\1 μ\2', part)
            part = re.sub(r'(\d+)\s*m\s*([A-Z])', r'\1 m\2', part)
            part = re.sub(r'(\d+)\s*k\s*([A-Z])', r'\1 k\2', part)
            
            # Clean up LaTeX spacing commands
            part = re.sub(r'\\,', ' ', part)
            part = re.sub(r'\\text\{([^}]+)\}', r'\1', part)
            part = re.sub(r'\\mathrm\{([^}]+)\}', r'\1', part)
            part = re.sub(r'\s{3,}', ' ', part)
            part = part.strip()
        
        parts[i] = part
    
    # Rejoin all parts
    result = ''.join(parts)
    
    # Restore preserved Unicode symbols
    for unicode_char, placeholder in unicode_preservations.items():
        result = result.replace(placeholder, unicode_char)
    
    return result

def determine_correct_answer_letter(correct_answer_text, choice_texts):
    """Determine the correct answer letter (A, B, C, D) from the correct answer text"""
    if not correct_answer_text:
        return 'A'
    
    answer_clean = str(correct_answer_text).strip()
    
    # Case 1: Already a letter (A, B, C, D)
    if answer_clean.upper() in ['A', 'B', 'C', 'D']:
        return answer_clean.upper()
    
    # Case 2: Exact text match (case insensitive)
    answer_lower = answer_clean.lower()
    for letter, choice_text in choice_texts.items():
        if choice_text.lower().strip() == answer_lower:
            return letter
    
    # Case 3: Partial match for long answers
    if len(answer_clean) > 10:
        for letter, choice_text in choice_texts.items():
            if (len(choice_text) > 10 and 
                answer_lower in choice_text.lower()):
                return letter
    
    # Default fallback
    print(f"⚠️ Could not match '{answer_clean}' to any choice, defaulting to A")
    return 'A'

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

def display_question_preview(question_row):
    """Display question preview with correct answer highlighting"""
    
    st.markdown('<div class="question-preview">', unsafe_allow_html=True)
    
    # Handle both dict and pandas Series
    if hasattr(question_row, 'get'):
        get_value = lambda key, default='': question_row.get(key, default)
    else:
        get_value = lambda key, default='': question_row[key] if key in question_row else default
    
    # Header with metadata
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{get_value('Title')}**")
    with col2:
        question_type = get_value('Type', 'unknown')
        st.markdown(f"🏷️ **{question_type.replace('_', ' ').title()}**")
    with col3:
        difficulty = get_value('Difficulty', 'Unknown')
        difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
        difficulty_icon = difficulty_colors.get(difficulty, '⚪')
        st.markdown(f"{difficulty_icon} **{difficulty}**")
    with col4:
        points = get_value('Points', 1)
        st.markdown(f"**{points} pts**")
    
    # Topic and subtopic info
    topic = get_value('Topic', 'Unknown')
    subtopic = get_value('Subtopic', '')
    topic_info = f"📚 {topic}"
    if subtopic and subtopic not in ['', 'N/A', 'empty']:
        topic_info += f" → {subtopic}"
    st.markdown(f"*{topic_info}*")
    
    st.markdown("---")
    
    # Question text with enhanced LaTeX rendering
    question_text_raw = get_value('Question_Text', '')
    question_text = render_latex_in_text(question_text_raw)
    st.markdown(f"**Question:** {question_text}")
    
    # Handle different question types
    if get_value('Type') == 'multiple_choice':
        st.markdown("**Choices:**")
        choices = ['A', 'B', 'C', 'D']
        correct_answer_raw = get_value('Correct_Answer', '')
        
        # Clean up the correct answer
        correct_answer_text = str(correct_answer_raw).strip()
        
        # Get all choice texts
        choice_texts = {}
        for choice_letter in choices:
            choice_text = get_value(f'Choice_{choice_letter}', '')
            if choice_text and str(choice_text).strip():
                choice_texts[choice_letter] = str(choice_text).strip()
        
        # Determine correct answer letter using robust matching
        correct_letter = determine_correct_answer_letter(correct_answer_text, choice_texts)
        
        # Display choices with correct highlighting
        for choice_letter in choices:
            if choice_letter in choice_texts:
                choice_text_clean = choice_texts[choice_letter]
                choice_text_rendered = render_latex_in_text(choice_text_clean)
                
                # Simple, reliable correct answer detection
                is_correct = (choice_letter == correct_letter)
                
                if is_correct:
                    st.markdown(f"• **{choice_letter}:** {choice_text_rendered} ✅ **← Correct Answer**")
                else:
                    st.markdown(f"• **{choice_letter}:** {choice_text_rendered}")
    
    elif get_value('Type') == 'numerical':
        correct_answer = render_latex_in_text(str(get_value('Correct_Answer', '')))
        st.markdown(f"**Correct Answer:** {correct_answer} ✅")
        tolerance = get_value('Tolerance', 0)
        if tolerance and float(tolerance) > 0:
            st.markdown(f"**Tolerance:** ±{tolerance}")
    
    elif get_value('Type') == 'true_false':
        correct_answer = str(get_value('Correct_Answer', '')).strip()
        st.markdown(f"**Correct Answer:** {correct_answer} ✅")
    
    elif get_value('Type') == 'fill_in_blank':
        correct_answer = render_latex_in_text(str(get_value('Correct_Answer', '')))
        st.markdown(f"**Correct Answer:** {correct_answer} ✅")
    
    # Feedback with enhanced rendering
    correct_feedback = get_value('Correct_Feedback', '') or get_value('feedback_correct', '')
    incorrect_feedback = get_value('Incorrect_Feedback', '') or get_value('feedback_incorrect', '')
    
    if correct_feedback or incorrect_feedback:
        with st.expander("💡 View Feedback"):
            if correct_feedback:
                correct_feedback = render_latex_in_text(str(correct_feedback))
                st.markdown(f"**Correct:** {correct_feedback}")
            
            if incorrect_feedback:
                incorrect_feedback = render_latex_in_text(str(incorrect_feedback))
                st.markdown(f"**Incorrect:** {incorrect_feedback}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def simple_browse_questions_tab(filtered_df):
    """Simplified browse questions tab"""
    st.markdown(f"### 📋 Browse Questions ({len(filtered_df)} results)")
    
    if len(filtered_df) > 0:
        # Pagination
        items_per_page = st.selectbox("Questions per page", [10, 20, 50], index=1)
        total_pages = (len(filtered_df) - 1) // items_per_page + 1
        
        if total_pages > 1:
            # Initialize page in session state
            if 'current_page' not in st.session_state:
                st.session_state['current_page'] = 1
            
            # Page navigation
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⬅️ Previous") and st.session_state['current_page'] > 1:
                    st.session_state['current_page'] -= 1
                    st.rerun()
            
            with col2:
                if st.button("⏪ First"):
                    st.session_state['current_page'] = 1
                    st.rerun()
            
            with col3:
                page = st.selectbox("Page", range(1, total_pages + 1), 
                                  index=st.session_state['current_page'] - 1)
                if page != st.session_state['current_page']:
                    st.session_state['current_page'] = page
                    st.rerun()
            
            with col4:
                if st.button("⏩ Last"):
                    st.session_state['current_page'] = total_pages
                    st.rerun()
            
            with col5:
                if st.button("Next ➡️") and st.session_state['current_page'] < total_pages:
                    st.session_state['current_page'] += 1
                    st.rerun()
            
            # Show page info
            st.info(f"Page {st.session_state['current_page']} of {total_pages} ({len(filtered_df)} total questions)")
            
            # Calculate indices
            start_idx = (st.session_state['current_page'] - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_df = filtered_df.iloc[start_idx:end_idx]
        else:
            page_df = filtered_df
        
        st.markdown("---")
        
        # Display questions
        for idx, (_, question) in enumerate(page_df.iterrows()):
            st.markdown(f"### Question {idx + 1}")
            display_question_preview(question)
            st.markdown("---")
    
    else:
        st.warning("🔍 No questions match the current filters.")

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

def main():
    """Main Streamlit application with modular architecture"""
    
    # Initialize session state
    if SESSION_MANAGER_AVAILABLE:
        initialize_session_state()
    
    # Header
    st.markdown("""
    # 📊 Question Database Manager
    
    **Web-based interface for managing educational question databases and generating Canvas-ready QTI packages**
    
    ---
    """)

    # Enhanced Upload Interface with Session Management - ALWAYS visible
    if SESSION_MANAGER_AVAILABLE:
        has_database = smart_upload_interface()
    else:
        st.error("❌ Session management not available. Please check module imports.")
        has_database = False
    
    # Main interface (only show if database is loaded)
    if has_database and 'df' in st.session_state:
        df = st.session_state['df']
        metadata = st.session_state['metadata']
        original_questions = st.session_state['original_questions']
        
        # Apply filters
        filtered_df = apply_filters(df)
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Browse Questions", "📥 Export"])
        
        with tab1:
            display_database_summary(df, metadata)
            st.markdown("---")
            create_summary_charts(df)
        
        with tab2:
            simple_browse_questions_tab(filtered_df)
        
        with tab3:
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
        # No database loaded - show helpful information
        st.markdown("---")
        st.markdown("## 🚀 Getting Started")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📋 What You Can Do:
            
            1. **📤 Upload** JSON question databases
            2. **📝 Browse** questions with live LaTeX preview
            3. **🎯 Filter** by topic, difficulty, and type
            4. **📦 Export** to Canvas-ready QTI packages
            5. **📊 Analyze** question distributions and statistics
            """)
        
        with col2:
            st.markdown("""
            ### 🎓 Perfect for Instructors:
            
            - **Course Planning** with mathematical notation
            - **LaTeX Support** for engineering formulas
            - **Multiple Question Types** (MC, numerical, T/F)
            - **Topic Organization** with subtopics
            - **Canvas Integration** via QTI export
            """)
        
        # Show sample file format
        with st.expander("📄 Sample JSON Format", expanded=False):
            sample_json = {
                "questions": [
                    {
                        "title": "Circuit Analysis",
                        "type": "multiple_choice",
                        "question_text": "What is the impedance of a circuit with R = 100 Ω and L = 50 mH at f = 1000 Hz?",
                        "choices": [
                            "100 + j314 Ω",
                            "100 + j50 Ω", 
                            "314 + j100 Ω",
                            "50 + j100 Ω"
                        ],
                        "correct_answer": "A",
                        "points": 2,
                        "topic": "Circuit Analysis",
                        "subtopic": "AC Circuits",
                        "difficulty": "Medium",
                        "feedback_correct": "Correct! Z = R + jωL = 100 + j(2π×1000×0.05) = 100 + j314 Ω",
                        "feedback_incorrect": "Remember that impedance Z = R + jωL for an RL circuit."
                    }
                ],
                "metadata": {
                    "subject": "Electrical Engineering",
                    "format_version": "Phase Four",
                    "generation_date": "2024-12-19"
                }
            }
            
            st.json(sample_json, expanded=False)


if __name__ == "__main__":
    main()