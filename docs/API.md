# Q2LMS API Documentation
## Developer Reference Guide

### Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Session Management](#session-management)
4. [Upload System](#upload-system)
5. [Database Processing](#database-processing)
6. [Question Editor](#question-editor)
7. [Export System](#export-system)
8. [LaTeX Processing](#latex-processing)
9. [UI Components](#ui-components)
10. [Integration Patterns](#integration-patterns)
11. [Extension Guide](#extension-guide)
12. [Testing Framework](#testing-framework)

---

## Architecture Overview

Q2LMS follows a modular architecture designed for maintainability, extensibility, and robust operation in educational environments.

### System Design

```
streamlit_app.py (Main Controller)
    ├── modules/session_manager.py (State Management)
    ├── modules/upload_interface_v2.py (File Processing)
    ├── modules/database_processor.py (Data Validation)
    ├── modules/question_editor.py (Content Editing)
    ├── modules/export/ (QTI Generation)
    │   ├── qti_generator.py
    │   ├── canvas_adapter.py
    │   └── latex_converter.py
    ├── modules/ui_components.py (Interface Elements)
    └── utilities/ (Helper Functions)
```

### Core Dependencies

```python
# Required packages
streamlit >= 1.20.0
pandas >= 1.5.0
plotly >= 5.0.0

# Optional enhancements
numpy >= 1.21.0
python-dateutil >= 2.8.0
```

### Data Flow Architecture

```
JSON Input → FileProcessor → ConflictResolver → 
DatabaseMerger → SessionManager → UIComponents → 
QTIExporter → Canvas-Ready Output
```

---

## Core Modules

### streamlit_app.py

**Purpose**: Main application controller and UI orchestration
**Location**: `/streamlit_app.py`

#### Key Functions

```python
def main():
    """
    Main application entry point
    Orchestrates tab navigation and module loading
    """
    # Initialize session state
    initialize_session_state()
    
    # Render upload interface
    has_database = render_upload_interface()
    
    # Conditional tab rendering based on database state
    if has_database:
        render_main_tabs()

def render_upload_interface() -> bool:
    """
    Render upload interface with system availability checks
    
    Returns:
        bool: True if database successfully loaded
    """
    if UPLOAD_SYSTEM_AVAILABLE:
        upload_interface = UploadInterfaceV2()
        upload_interface.render_complete_interface()
    else:
        fallback_upload_handler()

def render_main_tabs():
    """
    Render main application tabs (Overview, Browse, Edit, Export)
    Handles conditional feature availability
    """
```

#### Module Integration

```python
# Import pattern with graceful degradation
try:
    from modules.session_manager import initialize_session_state
    SESSION_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"Session management unavailable: {e}")
    SESSION_MANAGER_AVAILABLE = False

# Feature flags for conditional functionality
FEATURE_FLAGS = {
    'advanced_upload': UPLOAD_SYSTEM_AVAILABLE,
    'question_editor': QUESTION_EDITOR_AVAILABLE,
    'export_system': EXPORT_SYSTEM_AVAILABLE,
    'latex_processor': LATEX_PROCESSOR_AVAILABLE
}
```

#### Configuration

```python
# Page configuration
st.set_page_config(
    page_title="Q2LMS - Question Database Manager",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customization
CUSTOM_CSS = """
<style>
.q2lms-brand { color: #1f77b4; font-weight: 800; }
.upload-container { background: linear-gradient(135deg, #e3f2fd, #f0f8ff); }
.export-container { background: linear-gradient(135deg, #f0f8ff, #e8f5e8); }
</style>
"""
```

---

## Session