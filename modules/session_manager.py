#!/usr/bin/env python3
"""
Session Management Module for Question Database Manager
Handles session state, database history, and lifecycle management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any

def initialize_session_state():
    """Initialize session state with default values"""
    if 'database_history' not in st.session_state:
        st.session_state['database_history'] = []
    
    if 'current_database_id' not in st.session_state:
        st.session_state['current_database_id'] = None
    
    if 'upload_session' not in st.session_state:
        st.session_state['upload_session'] = 0

def clear_session_state():
    """Clear all database-related session state"""
    keys_to_clear = [
        'df', 'metadata', 'original_questions', 'cleanup_reports', 
        'filename', 'processing_options', 'batch_processed_files',
        'quiz_questions', 'current_page', 'last_page', 'loaded_at'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any edit-related session states
    edit_keys = [key for key in st.session_state.keys() if 'edit_' in key]
    for key in edit_keys:
        del st.session_state[key]
    
    # Clear any toggle states
    toggle_keys = [key for key in st.session_state.keys() if 'toggle_' in key]
    for key in toggle_keys:
        del st.session_state[key]
    
    # Clear any confirmation states
    confirm_keys = [key for key in st.session_state.keys() if 'confirm_' in key]
    for key in confirm_keys:
        del st.session_state[key]

def get_database_summary() -> Optional[Dict[str, Any]]:
    """Get summary of current database for display"""
    if 'df' not in st.session_state:
        return None
    
    df = st.session_state['df']
    return {
        'filename': st.session_state.get('filename', 'Unknown'),
        'total_questions': len(df),
        'topics': df['Topic'].nunique(),
        'total_points': df['Points'].sum(),
        'difficulty_distribution': df['Difficulty'].value_counts().to_dict(),
        'type_distribution': df['Type'].value_counts().to_dict(),
        'loaded_at': st.session_state.get('loaded_at', 'Unknown')
    }

def save_database_to_history():
    """Save current database to history before replacing"""
    if 'df' not in st.session_state:
        return False
    
    try:
        # Create history entry
        history_entry = {
            'id': len(st.session_state.get('database_history', [])),
            'filename': st.session_state.get('filename', 'Unknown'),
            'df': st.session_state['df'].copy(),
            'metadata': st.session_state.get('metadata', {}),
            'original_questions': st.session_state.get('original_questions', []).copy() if st.session_state.get('original_questions') else [],
            'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'summary': get_database_summary()
        }
        
        # Add to history (keep only last 5 for memory management)
        if 'database_history' not in st.session_state:
            st.session_state['database_history'] = []
        
        st.session_state['database_history'].append(history_entry)
        
        # Keep only last 5 databases
        if len(st.session_state['database_history']) > 5:
            st.session_state['database_history'] = st.session_state['database_history'][-5:]
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error saving to history: {str(e)}")
        return False

def restore_database_from_history(history_id: int) -> bool:
    """Restore a database from history"""
    if 'database_history' not in st.session_state:
        return False
    
    try:
        for entry in st.session_state['database_history']:
            if entry['id'] == history_id:
                # Restore the database
                st.session_state['df'] = entry['df'].copy()
                st.session_state['metadata'] = entry['metadata']
                st.session_state['original_questions'] = entry['original_questions'].copy()
                st.session_state['filename'] = entry['filename']
                st.session_state['loaded_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state['current_database_id'] = history_id
                
                return True
        
        return False
        
    except Exception as e:
        st.error(f"❌ Error restoring from history: {str(e)}")
        return False

def display_database_history():
    """Display database history with restore options"""
    if 'database_history' not in st.session_state or not st.session_state['database_history']:
        return
    
    st.markdown("### 📚 Recent Database History")
    st.info("💡 You can restore any of your recent databases")
    
    for entry in reversed(st.session_state['database_history']):  # Show most recent first
        with st.expander(f"📄 {entry['filename']} - {entry['saved_at']}", expanded=False):
            if entry['summary']:
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Questions:** {entry['summary']['total_questions']}")
                    st.write(f"**Topics:** {entry['summary']['topics']}")
                    st.write(f"**Total Points:** {entry['summary']['total_points']:.0f}")
                
                with col2:
                    st.write("**Difficulty Distribution:**")
                    for diff, count in entry['summary']['difficulty_distribution'].items():
                        st.write(f"  • {diff}: {count}")
                
                with col3:
                    if st.button(f"🔄 Restore", key=f"restore_{entry['id']}", help="Restore this database"):
                        if restore_database_from_history(entry['id']):
                            st.success("✅ Database restored!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to restore database")

def display_current_database_status() -> bool:
    """Display current database status and management options"""
    if 'df' in st.session_state:
        df = st.session_state['df']
        filename = st.session_state.get('filename', 'Unknown')
        loaded_at = st.session_state.get('loaded_at', 'Unknown')
        
        # Database status card
        st.markdown("""
        <div style="background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1976d2; margin: 1rem 0;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        
        with col1:
            st.markdown(f"**📊 Current Database:** `{filename}`")
            st.markdown(f"**📅 Loaded:** {loaded_at}")
            st.markdown(f"**📊 Data:** {len(df)} questions | {df['Topic'].nunique()} topics | {df['Points'].sum():.0f} total points")
        
        with col2:
            st.markdown("**Status:**")
            st.success("✅ Loaded")
        
        with col3:
            st.markdown("**Actions:**")
            if st.button("🔄 Refresh", help="Refresh current database display"):
                st.rerun()
        
        with col4:
            st.markdown("**Clear Database:**")
            if st.button("🗑️ Clear & Load New", type="secondary", help="Clear current database to load a new one"):
                save_database_to_history()
                clear_session_state()
                st.success("✅ Database cleared! You can now load a new file.")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        return True
    return False

def display_enhanced_database_status() -> bool:
    """Enhanced database status with history management"""
    initialize_session_state()
    
    if 'df' in st.session_state:
        df = st.session_state['df']
        filename = st.session_state.get('filename', 'Unknown')
        loaded_at = st.session_state.get('loaded_at', 'Unknown')
        
        # Main database status card
        st.markdown("""
        <div style="background-color: #e8f5e8; padding: 1.5rem; border-radius: 0.75rem; border-left: 5px solid #4caf50; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Active Database")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**📁 File:** `{filename}`")
            st.markdown(f"**📅 Loaded:** {loaded_at}")
            st.markdown(f"**📊 Data:** {len(df)} questions | {df['Topic'].nunique()} topics | {df['Points'].sum():.0f} total points")
        
        with col2:
            st.markdown("**🔧 Quick Actions:**")
            if st.button("🔄 Refresh Display", help="Refresh current view"):
                st.rerun()
            
            if st.button("💾 Save to History", help="Save current state to history"):
                if save_database_to_history():
                    st.success("✅ Saved to history!")
        
        with col3:
            st.markdown("**🗑️ Database Management:**")
            if st.button("🔄 Load New Database", type="secondary", help="Save current and load new"):
                save_database_to_history()
                clear_session_state()
                st.success("✅ Ready for new database!")
                st.rerun()
            
            if st.button("🗑️ Clear All", help="Clear everything"):
                clear_session_state()
                st.success("✅ All data cleared!")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show database history
        display_database_history()
        
        return True
    else:
        # No database loaded
        st.markdown("""
        <div style="background-color: #fff3e0; padding: 1.5rem; border-radius: 0.75rem; border-left: 5px solid #ff9800; margin: 1rem 0;">
        """, unsafe_allow_html=True)
        
        st.markdown("### 📂 No Database Loaded")
        st.markdown("Upload a JSON question database file to get started.")
        
        # Show history if available
        if 'database_history' in st.session_state and st.session_state['database_history']:
            st.markdown("**Or restore from recent history:**")
            display_database_history()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        return False

def has_active_database() -> bool:
    """Check if there's an active database loaded"""
    return 'df' in st.session_state and st.session_state['df'] is not None

def get_current_database_info() -> Dict[str, Any]:
    """Get information about the current database"""
    if not has_active_database():
        return {}
    
    df = st.session_state['df']
    return {
        'filename': st.session_state.get('filename', 'Unknown'),
        'question_count': len(df),
        'topics': df['Topic'].nunique(),
        'total_points': df['Points'].sum(),
        'loaded_at': st.session_state.get('loaded_at', 'Unknown')
    }