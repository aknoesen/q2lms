#!/usr/bin/env python3
"""
Q2LMS Application Configuration
Handles feature detection, imports, and system status management
"""

import streamlit as st
import sys
import os

class AppConfig:
    """Centralized configuration and feature detection for Q2LMS"""
    
    def __init__(self):
        self.feature_status = {}
        # Initialize all feature attributes first
        self.session_manager = None
        self.upload_system = None
        self.question_editor = None
        self.latex_processor = None
        self.export_system = None
        self.ui_components = None
        self.fork_feature = None
        self.output_manager = None
        
        # Then detect features
        self._detect_all_features()
    
    def _detect_all_features(self):
        """Detect all available features and populate status"""
        
        # Add modules directory to Python path
        modules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'modules')
        if modules_path not in sys.path:
            sys.path.insert(0, modules_path)
        
        # Session Management
        try:
            from modules.session_manager import (
                initialize_session_state, clear_session_state, 
                display_enhanced_database_status, has_active_database
            )
            from modules.database_processor import (
                save_question_changes, delete_question, validate_single_question
            )
            self.feature_status['session_manager'] = True
            self.session_manager = {
                'initialize_session_state': initialize_session_state,
                'clear_session_state': clear_session_state,
                'display_enhanced_database_status': display_enhanced_database_status,
                'has_active_database': has_active_database,
                'save_question_changes': save_question_changes,
                'delete_question': delete_question,
                'validate_single_question': validate_single_question
            }
        except ImportError:
            self.feature_status['session_manager'] = False
            self.session_manager = None

        # Upload System
        try:
            from modules.upload_interface_v2 import UploadInterfaceV2
            self.feature_status['upload_system'] = True
            self.upload_system = {'UploadInterfaceV2': UploadInterfaceV2}
        except ImportError:
            try:
                from modules.upload_handler import smart_upload_interface
                self.feature_status['upload_system'] = False
                self.feature_status['basic_upload'] = True
                self.upload_system = {'smart_upload_interface': smart_upload_interface}
            except ImportError:
                self.feature_status['upload_system'] = False
                self.feature_status['basic_upload'] = False
                self.upload_system = None

        # Question Editor
        try:
            from modules.question_editor import side_by_side_question_editor
            self.feature_status['question_editor'] = True
            self.question_editor = {'side_by_side_question_editor': side_by_side_question_editor}
        except ImportError:
            self.feature_status['question_editor'] = False
            self.question_editor = None

        # LaTeX Processor
        try:
            from modules.latex_processor import LaTeXProcessor, clean_text
            self.feature_status['latex_processor'] = True
            self.latex_processor = {'LaTeXProcessor': LaTeXProcessor, 'clean_text': clean_text}
        except ImportError:
            self.feature_status['latex_processor'] = False
            self.latex_processor = None

        # Export System
        try:
            from modules.exporter import integrate_with_existing_ui
            self.feature_status['export_system'] = True
            self.export_system = {'integrate_with_existing_ui': integrate_with_existing_ui}
        except ImportError:
            self.feature_status['export_system'] = False
            self.export_system = None

        # UI Components
        try:
            from modules.utils import render_latex_in_text, determine_correct_answer_letter
            from modules.ui_components import display_database_summary, create_summary_charts, apply_filters
            from modules.simple_browse import simple_browse_questions_tab
            self.feature_status['ui_components'] = True
            self.ui_components = {
                'render_latex_in_text': render_latex_in_text,
                'determine_correct_answer_letter': determine_correct_answer_letter,
                'display_database_summary': display_database_summary,
                'create_summary_charts': create_summary_charts,
                'apply_filters': apply_filters,
                'simple_browse_questions_tab': simple_browse_questions_tab
            }
        except ImportError:
            self.feature_status['ui_components'] = False
            self.ui_components = None

        # Import output manager for clean operations
        try:
            from modules.output_manager import get_output_manager
            self.feature_status['output_manager'] = True
            self.output_manager = {'get_output_manager': get_output_manager}
        except ImportError:
            self.feature_status['output_manager'] = False
            self.output_manager = None
            from modules.operation_mode_manager import OperationModeManager, get_operation_mode_manager
            from modules.interface_select_questions import SelectQuestionsInterface
            from modules.interface_delete_questions import DeleteQuestionsInterface
            from modules.question_flag_manager import QuestionFlagManager
            self.feature_status['fork_feature'] = True
            self.fork_feature = {
                'OperationModeManager': OperationModeManager,
                'get_operation_mode_manager': get_operation_mode_manager,
                'SelectQuestionsInterface': SelectQuestionsInterface,
                'DeleteQuestionsInterface': DeleteQuestionsInterface,
                'QuestionFlagManager': QuestionFlagManager
            }
        except ImportError:
            self.feature_status['fork_feature'] = False
            self.fork_feature = None

    def is_available(self, feature_name):
        """Check if a feature is available"""
        return self.feature_status.get(feature_name, False)
    
    def get_feature(self, feature_name):
        """Get feature components if available"""
        feature_map = {
            'session_manager': self.session_manager,
            'upload_system': self.upload_system,
            'question_editor': self.question_editor,
            'latex_processor': self.latex_processor,
            'export_system': self.export_system,
            'ui_components': self.ui_components,
            'fork_feature': self.fork_feature,
            'output_manager': self.output_manager
        }
        return feature_map.get(feature_name)
    
    def render_sidebar_header(self):
        """Render clean sidebar header with logo only"""
        with st.sidebar:
            # Add logo at top of sidebar
            st.image("https://raw.githubusercontent.com/aknoesen/q2lms/main/assets/q2lms_icon.svg", width=240)
            st.markdown("---")
    
    def get_system_health(self):
        """Get overall system health status"""
        critical_systems = [
            self.is_available('session_manager'),
            self.is_available('ui_components')
        ]
        
        essential_systems = [
            self.is_available('upload_system') or self.is_available('basic_upload'),
            self.is_available('export_system')
        ]
        
        if all(critical_systems) and all(essential_systems):
            return "excellent", "✅ All systems operational - Full functionality available!"
        elif all(critical_systems):
            return "good", "⚠️ Core systems operational - Some features may be limited"
        else:
            return "poor", "❌ Critical systems offline - Functionality severely limited"
    
    def apply_custom_css(self):
        """Apply Q2LMS custom CSS styling"""
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .q2lms-brand {
            color: #1f77b4; /* Blue to match the Q2 elements in icon */
            font-weight: 800;
            font-size: 3rem;
            text-align: center;
            margin-bottom: 1rem;
            }
            
            .brand-tagline {
                color: #6b7280;
                text-align: center;
                font-size: 1.1rem;
                font-weight: 500;
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
            
            /* Upload interface container styling */
            .upload-container {
                background: linear-gradient(135deg, #e3f2fd, #f0f8ff);
                padding: 2rem;
                border-radius: 1rem;
                margin: 1rem 0;
                border: 2px solid #2196f3;
            }
            
            /* Export section styling */
            .export-container {
                background: linear-gradient(135deg, #f0f8ff, #e8f5e8);
                padding: 2rem;
                border-radius: 1rem;
                margin: 1rem 0;
                border: 2px solid #28a745;
            }
            
            .export-badge {
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 1rem;
                font-size: 0.9rem;
                font-weight: bold;
                display: inline-block;
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
            
            /* Q2LMS feature highlights */
            .feature-card {
                background: linear-gradient(135deg, #ffffff, #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            
            .feature-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            }
        </style>
        """, unsafe_allow_html=True)
    
    def apply_mathjax_config(self):
        """Apply MathJax configuration for LaTeX rendering"""
        st.markdown("""
        <script>
        window.MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']]
          }
        };
        </script>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """, unsafe_allow_html=True)

# Global instance
_app_config = None

def get_app_config():
    """Get the global app configuration instance"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config