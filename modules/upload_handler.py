#!/usr/bin/env python3
"""
Upload Handler Module for Question Database Manager
Handles file uploads, format detection, and processing workflows
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List

# Import session manager
from .session_manager import (
    clear_session_state, save_database_to_history, 
    display_enhanced_database_status, initialize_session_state
)

def detect_database_format_and_type(json_content: str, filename: str) -> Tuple[Optional[str], str, int, Dict]:
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

def enhanced_file_upload_widget():
    """Enhanced file upload with better state management"""
    
    # File upload with unique key that changes when we clear state
    upload_key = f"file_upload_{st.session_state.get('upload_session', 0)}"
    
    uploaded_file = st.file_uploader(
        "📄 Upload Question Database (JSON)",
        type=['json'],
        help="Upload a JSON question database file",
        key=upload_key
    )
    
    # Handle file upload
    if uploaded_file is not None:
        # Check if this is a new file (different from what's currently loaded)
        current_filename = st.session_state.get('filename', '')
        
        if uploaded_file.name != current_filename:
            # New file detected
            content = uploaded_file.read().decode('utf-8')
            
            # Detect format
            format_version, db_type, question_count, metadata = detect_database_format_and_type(content, uploaded_file.name)
            
            if format_version is None:
                st.error(f"❌ Invalid file format: {db_type}")
                return None
            
            # Show file info
            with st.expander("📊 File Analysis", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Questions", question_count)
                with col2:
                    st.metric("Format", format_version)
                with col3:
                    size_mb = len(content) / 1024 / 1024
                    st.metric("Size", f"{size_mb:.2f} MB")
            
            # Processing options
            col1, col2 = st.columns(2)
            with col1:
                auto_latex = st.checkbox("🧮 Auto-process LaTeX", value=True)
                validate_questions = st.checkbox("✅ Validate questions", value=True)
            with col2:
                assign_new_ids = st.checkbox("🔄 Assign new IDs", value=False)
                save_previous = st.checkbox("💾 Save current to history", value=True)
            
            # Process button
            if st.button("🚀 Load Database", type="primary"):
                # Save current database to history if requested and exists
                if save_previous and 'df' in st.session_state:
                    save_database_to_history()
                
                # Clear current state
                clear_session_state()
                
                # Import and process new database
                from .database_processor import process_single_database
                
                result = process_single_database(content, {
                    'filename': uploaded_file.name,
                    'auto_latex': auto_latex,
                    'validate_questions': validate_questions,
                    'assign_new_ids': assign_new_ids,
                    'format_version': format_version,
                    'metadata': metadata
                })
                
                if result is not None:
                    # Set loaded timestamp
                    st.session_state['loaded_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Increment upload session to reset file uploader
                    st.session_state['upload_session'] = st.session_state.get('upload_session', 0) + 1
                    
                    st.success("🎉 Database loaded successfully!")
                    st.rerun()
                
                return result
        
        else:
            st.info("📊 This file is already loaded. Use 'Load New Database' above to replace it.")
    
    return None

def handle_database_replacement():
    """Handle replacing the current database with a new one"""
    
    st.markdown("#### 🔄 Replace Current Database")
    
    uploaded_file = st.file_uploader(
        "📄 Upload New Question Database (JSON)",
        type=['json'],
        help="This will completely replace your current database",
        key="replacement_upload"
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
        with st.expander("📊 New File Analysis", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Format", format_version)
            with col2:
                st.metric("Questions", question_count)
            with col3:
                size_mb = len(content) / 1024 / 1024
                st.metric("Size", f"{size_mb:.2f} MB")
        
        # Processing options
        st.markdown("#### ⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_latex = st.checkbox("🧮 Auto-process LaTeX", value=True, help="Automatically clean LaTeX notation")
            validate_questions = st.checkbox("✅ Validate questions", value=True, help="Check for required fields and consistency")
        
        with col2:
            assign_new_ids = st.checkbox("🔄 Assign new IDs", value=False, help="Generate new question IDs")
        
        # Replacement confirmation
        st.markdown("#### ⚠️ Confirm Replacement")
        st.warning("This action will permanently replace your current database in this session.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Replace Database", type="primary"):
                # Clear current session state
                clear_session_state()
                
                # Import and process new database
                from .database_processor import process_single_database
                
                # Process new database
                result = process_single_database(content, {
                    'filename': uploaded_file.name,
                    'auto_latex': auto_latex,
                    'validate_questions': validate_questions,
                    'assign_new_ids': assign_new_ids,
                    'format_version': format_version,
                    'metadata': metadata
                })
                
                if result is not None:
                    st.success("🎉 Database successfully replaced!")
                    st.rerun()
                
                return result
        
        with col2:
            if st.button("❌ Cancel Replacement"):
                st.info("❌ Replacement cancelled. Keeping current database.")
    
    return None

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
        
        # Process button
        if st.button("🚀 Process Database", type="primary"):
            # Clear any existing session state first
            clear_session_state()
            
            # Import and process database
            from .database_processor import process_single_database
            
            result = process_single_database(content, {
                'filename': uploaded_file.name,
                'auto_latex': auto_latex,
                'validate_questions': validate_questions,
                'assign_new_ids': assign_new_ids,
                'format_version': format_version,
                'metadata': metadata
            })
            
            if result is not None:
                st.rerun()
            
            return result
    
    return None

def handle_append_upload():
    """Handle appending to existing database"""
    
    st.markdown("### ➕ Append to Current Database")
    
    if 'df' not in st.session_state:
        st.error("⚠️ No existing database loaded. Please load a database first.")
        return None
    
    # Show current database info
    current_df = st.session_state['df']
    current_filename = st.session_state.get('filename', 'Unknown')
    st.info(f"📊 Current database: **{current_filename}** with {len(current_df)} questions")
    
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
                ["Skip duplicates", "Add with new IDs", "Replace existing"]
            )
            
            renumber_ids = st.checkbox("🔄 Renumber all IDs sequentially", value=False)
        
        with col2:
            merge_metadata = st.checkbox("📋 Merge metadata", value=True)
            preserve_order = st.checkbox("📑 Preserve question order", value=True)
        
        if st.button("➕ Append to Database", type="primary"):
            # Import append processor
            from .database_processor import process_append_operation
            
            return process_append_operation(content, {
                'filename': uploaded_file.name,
                'handle_duplicates': handle_duplicates,
                'renumber_ids': renumber_ids,
                'merge_metadata': merge_metadata,
                'preserve_order': preserve_order,
                'current_df': current_df
            })
    
    return None

def smart_upload_interface() -> bool:
    """Smart upload interface that handles all file management scenarios"""
    
    st.markdown("## 📁 Database Upload & Management")
    
    # Always show current status first
    has_database = display_enhanced_database_status()
    
    # Upload section
    # Upload section with tabs
    st.markdown("---")
    st.markdown("### 📤 Upload Database File")

    # Create tabs for different upload modes
    upload_tab1, upload_tab2 = st.tabs(["🔄 Replace Database", "➕ Append Questions"])

    with upload_tab1:
        if has_database:
            st.info("💡 **Current database loaded.** Upload a new file to replace it.")
        else:
            st.info("💡 **No database loaded.** Upload a JSON file to get started.")
        
        # Enhanced file upload widget
        handle_single_upload()

    with upload_tab2:
        # Call your existing append function
        handle_append_upload()
    
    if has_database:
        st.info("💡 **Current database loaded.** Upload a new file to replace it, or use history to restore previous databases.")
    else:
        st.info("💡 **No database loaded.** Upload a JSON file to get started.")
    
    # Enhanced file upload widget
    enhanced_file_upload_widget()
    
    # Advanced options in expandable section
    with st.expander("🔧 Advanced Options", expanded=False):
        st.markdown("#### 📚 Batch Operations")
        st.info("Process multiple files at once")
        
        if st.button("📂 Open Batch Upload"):
            st.session_state['show_batch_upload'] = True
        
        # Show batch upload if requested
        if st.session_state.get('show_batch_upload', False):
            from .batch_processor import handle_batch_upload
            handle_batch_upload()
            
            if st.button("❌ Close Batch Upload"):
                st.session_state['show_batch_upload'] = False
                st.rerun()
    
    return has_database