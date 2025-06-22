Q2LMS API Documentation
Developer Reference Guide
Table of Contents

Architecture Overview
Core Modules
Session Management
Upload System
Database Processing
Question Editor
Export System
LaTeX Processing
UI Components
Integration Patterns
Extension Guide
Testing Framework


Architecture Overview
Q2LMS follows a modular architecture designed for maintainability, extensibility, and robust operation in educational environments.
System Design
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
Core Dependencies
```python
Required packages
streamlit >= 1.20.0
pandas >= 1.5.0
plotly >= 5.0.0
Optional enhancements
numpy >= 1.21.0
python-dateutil >= 2.8.0
```
Data Flow Architecture
JSON Input → FileProcessor → ConflictResolver → 
DatabaseMerger → SessionManager → UIComponents → 
QTIExporter → Canvas-Ready Output

Core Modules
streamlit_app.py
Purpose: Main application controller and UI orchestration
Location: /streamlit_app.py
Key Functions
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
Module Integration
```python
Import pattern with graceful degradation
try:
    from modules.session_manager import initialize_session_state
    SESSION_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"Session management unavailable: {e}")
    SESSION_MANAGER_AVAILABLE = False
Feature flags for conditional functionality
FEATURE_FLAGS = {
    'advanced_upload': UPLOAD_SYSTEM_AVAILABLE,
    'question_editor': QUESTION_EDITOR_AVAILABLE,
    'export_system': EXPORT_SYSTEM_AVAILABLE,
    'latex_processor': LATEX_PROCESSOR_AVAILABLE
}
```
Configuration
```python
Page configuration
st.set_page_config(
    page_title="Q2LMS - Question Database Manager",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)
CSS customization
CUSTOM_CSS = """

"""
```

Session Management
modules/session_manager.py
Purpose: Centralized session state management with database history and lifecycle control
Location: /modules/session_manager.py
Core Functions
```python
def initialize_session_state():
    """
    Initialize session state with default values
    Sets up database history tracking and upload session management
    """
    if 'database_history' not in st.session_state:
        st.session_state['database_history'] = []
if 'current_database_id' not in st.session_state:
    st.session_state['current_database_id'] = None

if 'upload_session' not in st.session_state:
    st.session_state['upload_session'] = 0

def clear_session_state():
    """
    Clear all database-related session state
    Preserves UI state while clearing data
    """
    keys_to_clear = [
        'df', 'metadata', 'original_questions', 'cleanup_reports', 
        'filename', 'processing_options', 'batch_processed_files',
        'quiz_questions', 'current_page', 'last_page', 'loaded_at'
    ]
for key in keys_to_clear:
    if key in st.session_state:
        del st.session_state[key]

def save_database_to_history() -> bool:
    """
    Save current database state to history before operations
Returns:
    bool: Success status of save operation
"""
try:
    history_entry = {
        'id': len(st.session_state.get('database_history', [])),
        'filename': st.session_state.get('filename', 'Unknown'),
        'df': st.session_state['df'].copy(),
        'metadata': st.session_state.get('metadata', {}),
        'original_questions': st.session_state.get('original_questions', []).copy(),
        'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'summary': get_database_summary()
    }

    st.session_state['database_history'].append(history_entry)

    # Keep only last 5 for memory management
    if len(st.session_state['database_history']) > 5:
        st.session_state['database_history'] = st.session_state['database_history'][-5:]

    return True

except Exception as e:
    st.error(f"Error deleting question: {str(e)}")
    return False

```

Question Editor
modules/question_editor.py
Purpose: Interactive question editing interface with live preview capabilities
Location: /modules/question_editor.py
Side-by-Side Editor
```python
def side_by_side_question_editor(filtered_df: pd.DataFrame):
    """
    Render side-by-side question editor with live preview
Args:
    filtered_df: Filtered DataFrame of questions to edit
"""
if filtered_df.empty:
    st.info("No questions available for editing")
    return

st.markdown("### 📝 Question Editor")
st.markdown("Select a question to edit with live preview")

# Question selection
question_options = [f"Q{i+1}: {row['Title']}" for i, row in filtered_df.iterrows()]
selected_index = st.selectbox("Select Question", range(len(question_options)), 
                             format_func=lambda x: question_options[x])

if selected_index is not None:
    render_editor_interface(filtered_df, selected_index)

def render_editor_interface(df: pd.DataFrame, question_index: int):
    """
    Render the main editor interface with edit and preview panels
Args:
    df: Question DataFrame
    question_index: Index of question being edited
"""
question = df.iloc[question_index]

# Create two-column layout
edit_col, preview_col = st.columns([1, 1])

with edit_col:
    st.markdown("#### ✏️ Edit Panel")
    changes = render_edit_panel(question, question_index)

with preview_col:
    st.markdown("#### 👁️ Preview Panel")
    render_preview_panel(question, changes)

# Save/Cancel buttons
col1, col2, col3 = st.columns([1, 1, 3])

with col1:
    if st.button("💾 Save Changes", key=f"save_{question_index}"):
        if save_question_changes(question_index, changes):
            st.rerun()

with col2:
    if st.button("🔄 Reset", key=f"reset_{question_index}"):
        # Clear edit session state
        _clear_edit_session_state(question_index)
        st.rerun()

def render_edit_panel(question: pd.Series, question_index: int) -> Dict[str, Any]:
    """
    Render editing controls for question fields
Args:
    question: Question data as pandas Series
    question_index: Index for session state keys

Returns:
    dict: Current values from edit controls
"""
# Initialize session state for this question
session_key_prefix = f"edit_{question_index}"

# Basic information
st.markdown("**Basic Information**")

title = st.text_input(
    "Title",
    value=question.get('Title', ''),
    key=f"{session_key_prefix}_title"
)

question_type = st.selectbox(
    "Type",
    ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank'],
    index=['multiple_choice', 'numerical', 'true_false', 'fill_in_blank'].index(
        question.get('Type', 'multiple_choice')
    ),
    key=f"{session_key_prefix}_type"
)

col1, col2 = st.columns(2)
with col1:
    difficulty = st.selectbox(
        "Difficulty",
        ['Easy', 'Medium', 'Hard'],
        index=['Easy', 'Medium', 'Hard'].index(question.get('Difficulty', 'Easy')),
        key=f"{session_key_prefix}_difficulty"
    )

with col2:
    points = st.number_input(
        "Points",
        min_value=0.1,
        value=float(question.get('Points', 1)),
        step=0.1,
        key=f"{session_key_prefix}_points"
    )

# Topic information
st.markdown("**Topic Information**")

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input(
        "Topic",
        value=question.get('Topic', ''),
        key=f"{session_key_prefix}_topic"
    )

with col2:
    subtopic = st.text_input(
        "Subtopic",
        value=question.get('Subtopic', ''),
        key=f"{session_key_prefix}_subtopic"
    )

# Question content
st.markdown("**Question Content**")

question_text = st.text_area(
    "Question Text",
    value=question.get('Question_Text', ''),
    height=100,
    help="Use $...$ for inline math and $...$ for display math",
    key=f"{session_key_prefix}_question_text"
)

# Type-specific fields
if question_type == 'multiple_choice':
    choices = render_multiple_choice_editor(question, session_key_prefix)
    correct_answer = st.selectbox(
        "Correct Answer",
        ['A', 'B', 'C', 'D'],
        index=['A', 'B', 'C', 'D'].index(question.get('Correct_Answer', 'A')),
        key=f"{session_key_prefix}_correct"
    )
    tolerance = 0.05  # Not used for MC

elif question_type == 'numerical':
    choices = ['', '', '', '']  # Not used for numerical
    correct_answer = st.text_input(
        "Correct Answer",
        value=str(question.get('Correct_Answer', '')),
        help="Enter numeric value",
        key=f"{session_key_prefix}_correct"
    )
    tolerance = st.number_input(
        "Tolerance",
        min_value=0.0,
        value=float(question.get('Tolerance', 0.05)),
        step=0.01,
        help="Acceptable range (±)",
        key=f"{session_key_prefix}_tolerance"
    )

else:  # true_false or fill_in_blank
    choices = ['', '', '', '']
    correct_answer = st.text_input(
        "Correct Answer",
        value=str(question.get('Correct_Answer', '')),
        key=f"{session_key_prefix}_correct"
    )
    tolerance = 0.05

# Feedback
st.markdown("**Feedback**")

correct_feedback = st.text_area(
    "Correct Feedback",
    value=question.get('Correct_Feedback', ''),
    height=80,
    key=f"{session_key_prefix}_correct_feedback"
)

incorrect_feedback = st.text_area(
    "Incorrect Feedback",
    value=question.get('Incorrect_Feedback', ''),
    height=80,
    key=f"{session_key_prefix}_incorrect_feedback"
)

# Return all current values
return {
    'title': title,
    'question_type': question_type,
    'difficulty': difficulty,
    'points': points,
    'topic': topic,
    'subtopic': subtopic,
    'question_text': question_text,
    'choice_a': choices[0],
    'choice_b': choices[1],
    'choice_c': choices[2],
    'choice_d': choices[3],
    'correct_answer': correct_answer,
    'tolerance': tolerance,
    'correct_feedback': correct_feedback,
    'incorrect_feedback': incorrect_feedback
}

def render_multiple_choice_editor(question: pd.Series, session_key_prefix: str) -> List[str]:
    """
    Render multiple choice specific editing controls
Args:
    question: Question data
    session_key_prefix: Prefix for session state keys

Returns:
    list: Current choice values [A, B, C, D]
"""
st.markdown("**Answer Choices**")

choices = []
for letter in ['A', 'B', 'C', 'D']:
    choice_value = st.text_input(
        f"Choice {letter}",
        value=question.get(f'Choice_{letter}', ''),
        key=f"{session_key_prefix}_choice_{letter.lower()}"
    )
    choices.append(choice_value)

return choices

def render_preview_panel(question: pd.Series, changes: Dict[str, Any]):
    """
    Render live preview of question with current changes
Args:
    question: Original question data
    changes: Current changes from edit panel
"""
# Merge original question with changes
preview_data = question.to_dict()
preview_data.update(changes)

# Question header
st.markdown(f"**{preview_data['title']}**")
st.markdown(f"*{preview_data['question_type'].title()} | {preview_data['difficulty']} | {preview_data['points']} pts*")

if preview_data['topic']:
    st.markdown(f"*Topic: {preview_data['topic']}*")
    if preview_data['subtopic']:
        st.markdown(f"*Subtopic: {preview_data['subtopic']}*")

st.markdown("---")

# Question text with LaTeX rendering
if preview_data['question_text']:
    try:
        st.markdown(render_latex_in_text(preview_data['question_text']))
    except Exception:
        st.markdown(preview_data['question_text'])  # Fallback to plain text

# Type-specific preview
if preview_data['question_type'] == 'multiple_choice':
    st.markdown("**Choices:**")
    choices = [
        preview_data['choice_a'],
        preview_data['choice_b'],
        preview_data['choice_c'],
        preview_data['choice_d']
    ]

    for i, choice in enumerate(choices):
        if choice.strip():
            letter = ['A', 'B', 'C', 'D'][i]
            is_correct = (letter == preview_data['correct_answer'])

            if is_correct:
                st.markdown(f"**{letter}. {render_latex_in_text(choice)}** ✅")
            else:
                st.markdown(f"{letter}. {render_latex_in_text(choice)}")

elif preview_data['question_type'] == 'numerical':
    st.markdown(f"**Correct Answer:** {preview_data['correct_answer']}")
    if preview_data['tolerance'] > 0:
        st.markdown(f"**Tolerance:** ±{preview_data['tolerance']}")

else:
    st.markdown(f"**Correct Answer:** {preview_data['correct_answer']}")

# Feedback preview
if preview_data['correct_feedback']:
    st.markdown("**Correct Feedback:**")
    st.info(render_latex_in_text(preview_data['correct_feedback']))

if preview_data['incorrect_feedback']:
    st.markdown("**Incorrect Feedback:**")
    st.warning(render_latex_in_text(preview_data['incorrect_feedback']))

def _clear_edit_session_state(question_index: int):
    """
    Clear session state for a specific question being edited
Args:
    question_index: Index of question to clear state for
"""
session_key_prefix = f"edit_{question_index}"

keys_to_remove = [key for key in st.session_state.keys() 
                 if key.startswith(session_key_prefix)]

for key in keys_to_remove:
    del st.session_state[key]

```

Export System
modules/export/qti_generator.py
Purpose: Generate QTI-compliant packages for LMS import
Location: /modules/export/qti_generator.py
QTI Package Generation
```python
class QTIGenerator:
    """
    Generates IMS QTI 2.1 compliant packages for LMS import
    Optimized for Canvas LMS with mathematical notation support
    """
def __init__(self):
    self.canvas_adapter = CanvasAdapter()
    self.latex_converter = LaTeXConverter()

def generate_qti_package(self, questions: List[Dict], 
                       package_name: str = "Q2LMS_Export") -> Tuple[bool, str, Optional[bytes]]:
    """
    Generate complete QTI package as ZIP file

    Args:
        questions: List of question dictionaries
        package_name: Name for the QTI package

    Returns:
        Tuple of (success, message, zip_data)
    """
    try:
        # Validate input
        if not questions:
            return False, "No questions provided", None

        # Process questions for Canvas compatibility
        processed_questions = self._process_questions_for_canvas(questions)

        # Generate QTI XML structure
        manifest_xml = self._generate_manifest(package_name, processed_questions)
        assessment_xml = self._generate_assessment(processed_questions)

        # Create ZIP package
        zip_data = self._create_zip_package(manifest_xml, assessment_xml, package_name)

        return True, f"Successfully generated QTI package with {len(questions)} questions", zip_data

    except Exception as e:
        return False, f"Error generating QTI package: {str(e)}", None

def _process_questions_for_canvas(self, questions: List[Dict]) -> List[Dict]:
    """
    Process questions for Canvas LMS compatibility

    Args:
        questions: Original question list

    Returns:
        List[Dict]: Canvas-optimized questions
    """
    processed = []

    for question in questions:
        processed_question = question.copy()

        # Convert LaTeX notation for Canvas
        processed_question = self.latex_converter.convert_for_canvas(processed_question)

        # Apply Canvas-specific adaptations
        processed_question = self.canvas_adapter.adapt_question(processed_question)

        processed.append(processed_question)

    return processed

def _generate_manifest(self, package_name: str, questions: List[Dict]) -> str:
    """
    Generate IMS QTI manifest XML

    Args:
        package_name: Package identifier
        questions: Processed questions

    Returns:
        str: Manifest XML content
    """
    manifest_template = """<?xml version="1.0" encoding="UTF-8"?>


<metadata>
    <schema>IMS QTI</schema>
    <schemaversion>2.1</schemaversion>
    <imsmd:lom>
        <imsmd:general>
            <imsmd:title>
                <imsmd:string>{package_name}</imsmd:string>
            </imsmd:title>
            <imsmd:description>
                <imsmd:string>Q2LMS Generated Assessment Package</imsmd:string>
            </imsmd:description>
        </imsmd:general>
    </imsmd:lom>
</metadata>

<organizations />

<resources>
    <resource identifier="assessment_resource" type="imsqti_assessment_xmlv2p1" href="assessment.xml">
        <file href="assessment.xml"/>
    </resource>

{item_resources}
    
"""
    # Generate item resources
    item_resources = []
    for i, question in enumerate(questions):
        question_id = question.get('id', f"item_{i+1}")
        item_resources.append(
            f'        <resource identifier="{question_id}" type="imsqti_item_xmlv2p1" href="{question_id}.xml">\n'
            f'            <file href="{question_id}.xml"/>\n'
            f'        </resource>'
        )

    return manifest_template.format(
        package_id=package_name.replace(' ', '_'),
        package_name=package_name,
        item_resources='\n'.join(item_resources)
    )

def _generate_assessment(self, questions: List[Dict]) -> str:
    """
    Generate assessment XML with question references

    Args:
        questions: Processed questions

    Returns:
        str: Assessment XML content
    """
    assessment_template = """<?xml version="1.0" encoding="UTF-8"?>


<testPart identifier="testPart1" navigationMode="nonlinear" submissionMode="individual">
    <assessmentSection identifier="section1" title="Questions" visible="true">

{assessment_items}
        

<outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float"/>

"""
    # Generate assessment items
    assessment_items = []
    for i, question in enumerate(questions):
        question_id = question.get('id', f"item_{i+1}")
        points = question.get('points', 1)

        assessment_items.append(
            f'            <assessmentItemRef identifier="{question_id}" href="{question_id}.xml">\n'
            f'                <weight identifier="SCORE" value="{points}"/>\n'
            f'            </assessmentItemRef>'
        )

    return assessment_template.format(
        assessment_items='\n'.join(assessment_items)
    )

def _create_zip_package(self, manifest_xml: str, assessment_xml: str, 
                       package_name: str) -> bytes:
    """
    Create ZIP package with all QTI files

    Args:
        manifest_xml: Manifest content
        assessment_xml: Assessment content
        package_name: Package name for filename

    Returns:
        bytes: ZIP file data
    """
    import zipfile
    import io

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add manifest
        zf.writestr('imsmanifest.xml', manifest_xml)

        # Add assessment
        zf.writestr('assessment.xml', assessment_xml)

        # Add individual question items
        # Note: In a full implementation, each question would be a separate XML file
        # For this example, we're creating a simplified structure

    return zip_buffer.getvalue()

class LaTeXConverter:
    """
    Handles LaTeX notation conversion for Canvas compatibility
    """
def convert_for_canvas(self, question: Dict) -> Dict:
    """
    Convert LaTeX delimiters for Canvas MathJax compatibility

    Args:
        question: Question dictionary with LaTeX content

    Returns:
        Dict: Question with Canvas-compatible LaTeX
    """
    converted_question = question.copy()

    # Fields that may contain LaTeX
    latex_fields = [
        'question_text', 'feedback_correct', 'feedback_incorrect',
        'choices'  # Special handling for choices array
    ]

    for field in latex_fields:
        if field in converted_question:
            if field == 'choices' and isinstance(converted_question[field], list):
                # Convert each choice
                converted_question[field] = [
                    self._convert_latex_delimiters(choice) 
                    for choice in converted_question[field]
                ]
            else:
                converted_question[field] = self._convert_latex_delimiters(
                    converted_question[field]
                )

    return converted_question

def _convert_latex_delimiters(self, text: str) -> str:
    """
    Convert LaTeX delimiters from $ format to Canvas format

    Args:
        text: Text potentially containing LaTeX

    Returns:
        str: Text with Canvas-compatible delimiters
    """
    if not isinstance(text, str):
        return text

    import re

    # Convert inline math: $...$ → \(...\)
    # But preserve display math: $...$ (unchanged)

    # First, protect display math by temporarily replacing it
    display_math_pattern = r'\$\$(.*?)\$\
except Exception as e:
    st.error(f"Error saving to history: {str(e)}")
    return False

```
Session State Schema
```python
Primary database state
SESSION_STATE_SCHEMA = {
    # Core database
    'df': pd.DataFrame,                    # Current questions as DataFrame
    'original_questions': List[dict],      # Raw JSON question data
    'metadata': dict,                      # Database metadata
    'filename': str,                       # Current filename
    'loaded_at': str,                      # Load timestamp
# History management
'database_history': List[dict],        # Previous database states
'current_database_id': Optional[int],  # Active database identifier

# Upload state
'upload_state': {
    'files_uploaded': bool,
    'preview_generated': bool,
    'merge_completed': bool,
    'current_preview': 'MergePreviewData',
    'final_database': List[dict],
    'error_message': str
},

# Processing state
'processing_options': dict,            # Last processing configuration
'cleanup_reports': List[dict],         # LaTeX cleanup results
'batch_processed_files': List[str],    # Multi-file processing tracking

# UI state
'current_page': int,                   # Pagination state
'last_page': int,                      # Last accessed page
'selected_filters': dict,              # Active filter configuration

}
```
Database History Management
```python
def display_database_history():
    """
    Display database history with restore options
    Provides rollback functionality for users
    """
    if not st.session_state.get('database_history'):
        return
st.markdown("### 📚 Recent Database History")

for entry in reversed(st.session_state['database_history']):
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
                if st.button(f"🔄 Restore", key=f"restore_{entry['id']}"):
                    if restore_database_from_history(entry['id']):
                        st.success("✅ Database restored!")
                        st.rerun()

def restore_database_from_history(history_id: int) -> bool:
    """
    Restore database from history by ID
Args:
    history_id: Unique identifier for history entry

Returns:
    bool: Success status of restore operation
"""

```

Upload System
modules/upload_interface_v2.py
Purpose: Advanced file upload system with multi-file merge capabilities and conflict resolution
Location: /modules/upload_interface_v2.py
UploadInterfaceV2 Class
```python
class UploadInterfaceV2:
    """
    Phase 3D Upload Interface
    Handles single and multi-file uploads with intelligent conflict resolution
    """
def __init__(self):
    self.file_processor = FileProcessor()
    self.state_manager = UploadStateManager()
    self.merger = DatabaseMerger()

def render_complete_interface(self):
    """
    Render complete upload interface with state management
    Handles all upload scenarios and user interactions
    """
    # Check current state and render appropriate interface
    current_state = self.state_manager.get_current_state()

    if current_state == UploadState.INITIAL:
        self.render_upload_section()
    elif current_state == UploadState.FILES_UPLOADED:
        self.render_processing_section()
    elif current_state == UploadState.PREVIEW_READY:
        self.render_preview_section()
    elif current_state == UploadState.MERGE_COMPLETED:
        self.render_results_section()

def render_upload_section(self):
    """
    Render file upload interface
    Supports single and multiple file selection
    """
    st.markdown("### 📁 Upload Question Database Files")

    uploaded_files = st.file_uploader(
        "Choose JSON files",
        type=['json'],
        accept_multiple_files=True,
        help="Upload one or more JSON question database files"
    )

    if uploaded_files:
        self._handle_file_upload(uploaded_files)

def _handle_file_upload(self, uploaded_files: List):
    """
    Process uploaded files through the file processor

    Args:
        uploaded_files: List of Streamlit uploaded file objects
    """
    processing_results = []

    for uploaded_file in uploaded_files:
        # Read file content
        content = uploaded_file.read().decode('utf-8')

        # Process through FileProcessor
        result = self.file_processor.process_file(
            content=content,
            filename=uploaded_file.name,
            options={'validate': True, 'cleanup_latex': True}
        )

        processing_results.append(result)

    # Store results and update state
    self.state_manager.store_processing_results(processing_results)
    self.state_manager.transition_to(UploadState.FILES_UPLOADED)

```
File Processing Pipeline
```python
class FileProcessor:
    """
    Handles individual file processing with validation and cleanup
    """
def process_file(self, content: str, filename: str, options: Dict) -> Dict:
    """
    Process single file through validation and cleanup pipeline

    Args:
        content: Raw JSON file content
        filename: Original filename
        options: Processing configuration

    Returns:
        dict: Processing results with questions and metadata
    """
    try:
        # Parse JSON content
        raw_data = json.loads(content)

        # Extract questions and metadata
        if isinstance(raw_data, dict) and 'questions' in raw_data:
            questions = raw_data['questions']
            metadata = raw_data.get('metadata', {})
        elif isinstance(raw_data, list):
            questions = raw_data
            metadata = {'format': 'legacy_array'}
        else:
            raise ValueError("Unexpected JSON structure")

        # Validate questions
        validation_results = self._validate_questions(questions)

        # Apply LaTeX cleanup if requested
        if options.get('cleanup_latex', False):
            questions, cleanup_report = self._cleanup_latex(questions)
        else:
            cleanup_report = None

        return {
            'success': True,
            'filename': filename,
            'questions': questions,
            'metadata': metadata,
            'validation_results': validation_results,
            'cleanup_report': cleanup_report,
            'question_count': len(questions)
        }

    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e),
            'questions': [],
            'metadata': {},
            'question_count': 0
        }

def _validate_questions(self, questions: List[Dict]) -> Dict:
    """
    Validate question structure and required fields

    Args:
        questions: List of question dictionaries

    Returns:
        dict: Validation results with errors and warnings
    """
    errors = []
    warnings = []

    required_fields = ['question_text', 'correct_answer', 'type']

    for i, question in enumerate(questions):
        # Check required fields
        missing_fields = [field for field in required_fields if not question.get(field)]
        if missing_fields:
            errors.append(f"Question {i+1}: Missing fields {missing_fields}")

        # Validate question type
        valid_types = ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank']
        if question.get('type') not in valid_types:
            errors.append(f"Question {i+1}: Invalid type '{question.get('type')}'")

        # Type-specific validation
        if question.get('type') == 'multiple_choice':
            choices = question.get('choices', [])
            if len(choices) < 2:
                warnings.append(f"Question {i+1}: Less than 2 choices for multiple choice")

    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0,
        'question_count': len(questions)
    }

```
Conflict Resolution System
```python
class DatabaseMerger:
    """
    Handles merging multiple question databases with conflict resolution
    """
def __init__(self, strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES):
    self.strategy = strategy
    self.conflict_detector = ConflictDetector()
    self.conflict_resolver = ConflictResolver()

def generate_preview(self, existing_df: pd.DataFrame, 
                    new_questions: List[Dict], 
                    auto_renumber: bool = True) -> MergePreview:
    """
    Generate merge preview with conflict analysis

    Args:
        existing_df: Current database DataFrame
        new_questions: Questions to be merged
        auto_renumber: Whether to automatically renumber conflicting IDs

    Returns:
        MergePreview: Detailed preview of merge operation
    """
    # Ensure questions have IDs
    new_questions = self._ensure_questions_have_ids(new_questions)

    # Check if auto-renumbering should be applied
    if auto_renumber and self._should_apply_auto_renumbering(existing_df, new_questions):
        final_questions = self.auto_renumber_questions(existing_df, new_questions)
        auto_renumbered = True
    else:
        final_questions = new_questions
        auto_renumbered = False

    # Detect conflicts with final questions
    conflicts = self.conflict_detector.detect_conflicts(existing_df, final_questions)

    # Calculate statistics
    existing_count = len(existing_df) if existing_df is not None else 0
    new_count = len(new_questions)
    final_count = self._estimate_final_count(existing_count, new_count, conflicts)

    return MergePreview(
        strategy=self.strategy,
        existing_count=existing_count,
        new_count=new_count,
        final_count=final_count,
        conflicts=conflicts,
        auto_renumbered=auto_renumbered,
        merge_summary=self._generate_merge_summary(conflicts, auto_renumbered),
        warnings=self._generate_warnings(conflicts)
    )

def auto_renumber_questions(self, existing_df: pd.DataFrame, 
                           new_questions: List[Dict]) -> List[Dict]:
    """
    Automatically renumber questions to avoid ID conflicts

    Args:
        existing_df: Current database
        new_questions: Questions to renumber

    Returns:
        List[Dict]: Questions with new IDs assigned
    """
    if existing_df is None or len(existing_df) == 0:
        return new_questions

    # Find next available ID
    next_id = self._get_next_available_id(existing_df)

    # Renumber questions
    renumbered_questions = []
    for i, question in enumerate(new_questions):
        new_question = question.copy()
        new_id = next_id + i

        # Update all possible ID fields
        for id_field in ['id', 'question_id', 'ID', 'Question_ID']:
            if id_field in new_question:
                new_question[id_field] = str(new_id)

        # Add ID if none exists
        if not any(field in new_question for field in ['id', 'question_id']):
            new_question['id'] = str(new_id)

        renumbered_questions.append(new_question)

    return renumbered_questions

```
Merge Strategies
```python
class MergeStrategy(Enum):
    """Enumeration of available merge strategies"""
    APPEND_ALL = "append_all"
    SKIP_DUPLICATES = "skip_duplicates"
    REPLACE_DUPLICATES = "replace_duplicates"
    RENAME_DUPLICATES = "rename_duplicates"
class ConflictType(Enum):
    """Types of conflicts that can be detected"""
    QUESTION_ID = "question_id"
    CONTENT_DUPLICATE = "content_duplicate"
    METADATA_CONFLICT = "metadata_conflict"
    LATEX_CONFLICT = "latex_conflict"
@dataclass
class MergePreview:
    """Data structure for merge preview information"""
    strategy: MergeStrategy
    existing_count: int
    new_count: int
    final_count: int
    conflicts: List[Conflict]
    auto_renumbered: bool
    merge_summary: Dict[str, Any]
    warnings: List[str]
def get_conflict_summary(self) -> Dict[str, int]:
    """Generate summary of conflicts by type"""
    summary = {}
    for conflict in self.conflicts:
        key = f"{conflict.type}_{conflict.severity}"
        summary[key] = summary.get(key, 0) + 1
    return summary

```

Database Processing
modules/database_processor.py
Purpose: Core database processing, validation, and transformation functions
Location: /modules/database_processor.py
Core Processing Functions
```python
def load_database_from_json(json_content: str) -> Tuple[Optional[pd.DataFrame], Dict, List, List]:
    """
    Load and process JSON database content with automatic LaTeX processing
Args:
    json_content: Raw JSON string content

Returns:
    Tuple containing:
    - pd.DataFrame: Processed questions as DataFrame
    - dict: Metadata from original JSON
    - list: Original questions list
    - list: Cleanup reports from processing
"""
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
        raise ValueError("Unexpected JSON structure")

    # Convert to standardized DataFrame format
    df = _convert_questions_to_dataframe(questions)

    return df, metadata, questions, []

except json.JSONDecodeError as e:
    st.error(f"Invalid JSON: {e}")
    return None, None, None, None
except Exception as e:
    st.error(f"Error processing database: {e}")
    return None, None, None, None

def _convert_questions_to_dataframe(questions: List[Dict]) -> pd.DataFrame:
    """
    Convert questions list to standardized DataFrame format
Args:
    questions: List of question dictionaries

Returns:
    pd.DataFrame: Standardized question DataFrame
"""
rows = []

for i, q in enumerate(questions):
    # Generate question ID
    question_id = q.get('id', q.get('question_id', f"Q_{i+1:05d}"))

    # Extract and normalize fields
    question_type = q.get('type', 'multiple_choice')
    title = q.get('title', f"Question {i+1}")
    question_text = q.get('question_text', '')

    # Handle choices for multiple choice questions
    choices = q.get('choices', [])
    if not isinstance(choices, list):
        choices = []

    # Ensure exactly 4 choices (pad with empty strings)
    while len(choices) < 4:
        choices.append('')

    # Process correct answer
    original_correct_answer = q.get('correct_answer', '')
    if question_type == 'multiple_choice':
        correct_answer = _find_correct_letter(original_correct_answer, choices[:4])
    else:
        correct_answer = str(original_correct_answer)

    # Extract metadata with defaults
    points = _safe_float(q.get('points', 1))
    tolerance = _safe_float(q.get('tolerance', 0.05))
    topic = q.get('topic', 'General')
    subtopic = q.get('subtopic', '')
    difficulty = q.get('difficulty', 'Easy')

    # Handle feedback
    feedback_correct = q.get('feedback_correct', '')
    feedback_incorrect = q.get('feedback_incorrect', '')

    # Create standardized row
    row = {
        'ID': question_id,
        'Type': question_type,
        'Title': title,
        'Question_Text': question_text,
        'Choice_A': choices[0] if len(choices) > 0 else '',
        'Choice_B': choices[1] if len(choices) > 1 else '',
        'Choice_C': choices[2] if len(choices) > 2 else '',
        'Choice_D': choices[3] if len(choices) > 3 else '',
        'Correct_Answer': correct_answer,
        'Points': points,
        'Tolerance': tolerance,
        'Feedback': feedback_correct,
        'Correct_Feedback': feedback_correct,
        'Incorrect_Feedback': feedback_incorrect,
        'Topic': topic,
        'Subtopic': subtopic,
        'Difficulty': difficulty
    }

    rows.append(row)

return pd.DataFrame(rows)

def _find_correct_letter(correct_text: str, choices: List[str]) -> str:
    """
    Convert correct answer text to letter designation (A, B, C, D)
Args:
    correct_text: Text of correct answer
    choices: List of available choices

Returns:
    str: Letter designation (A-D)
"""
if not correct_text:
    return 'A'

correct_clean = str(correct_text).strip().lower()

# Check if already a letter
if correct_clean.upper() in ['A', 'B', 'C', 'D']:
    return correct_clean.upper()

# Match against choices
for i, choice in enumerate(choices):
    if choice and str(choice).strip().lower() == correct_clean:
        return ['A', 'B', 'C', 'D'][i]

return 'A'  # Fallback

def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback
Args:
    value: Value to convert
    default: Default value if conversion fails

Returns:
    float: Converted value or default
"""
try:
    return float(value) if value is not None else default
except (ValueError, TypeError):
    return default

```
Validation System
```python
def validate_question_database(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive validation of question database
Args:
    df: Question database DataFrame

Returns:
    dict: Validation results with errors, warnings, and status
"""
errors = []
warnings = []

required_fields = ['ID', 'Type', 'Question_Text', 'Correct_Answer']

for idx, row in df.iterrows():
    # Check required fields
    for field in required_fields:
        if pd.isna(row[field]) or str(row[field]).strip() == '':
            errors.append(f"Question {row['ID']}: Missing {field}")

    # Type-specific validation
    if row['Type'] == 'multiple_choice':
        choices = [row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
        non_empty_choices = [c for c in choices if str(c).strip()]

        if len(non_empty_choices) < 2:
            warnings.append(f"Question {row['ID']}: Insufficient choices for multiple choice")

        if row['Correct_Answer'] not in ['A', 'B', 'C', 'D']:
            errors.append(f"Question {row['ID']}: Invalid correct answer for multiple choice")

    elif row['Type'] == 'numerical':
        try:
            float(row['Correct_Answer'])
        except (ValueError, TypeError):
            errors.append(f"Question {row['ID']}: Correct answer must be numeric for numerical type")

    # Validate points
    try:
        points = float(row.get('Points', 0))
        if points <= 0:
            warnings.append(f"Question {row['ID']}: Points should be positive")
    except (ValueError, TypeError):
        errors.append(f"Question {row['ID']}: Points must be numeric")

    # Check for LaTeX syntax issues
    question_text = str(row.get('Question_Text', ''))
    if ' in question_text:
        dollar_count = question_text.count(')
        if dollar_count % 2 != 0:
            warnings.append(f"Question {row['ID']}: Unmatched LaTeX delimiters")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0,
    'question_count': len(df),
    'validation_summary': {
        'total_questions': len(df),
        'error_count': len(errors),
        'warning_count': len(warnings),
        'success_rate': (len(df) - len(errors)) / len(df) if len(df) > 0 else 0
    }
}

def validate_single_question(question_row: Dict) -> Dict[str, Any]:
    """
    Validate individual question for editing operations
Args:
    question_row: Single question data (dict or Series)

Returns:
    dict: Validation results for single question
"""
errors = []
warnings = []

# Convert Series to dict if needed
if hasattr(question_row, 'to_dict'):
    question_data = question_row.to_dict()
else:
    question_data = question_row

# Check required fields
required_fields = ['Title', 'Type', 'Question_Text', 'Correct_Answer']
for field in required_fields:
    value = question_data.get(field, '')
    if not value or str(value).strip() == '' or str(value).lower() == 'nan':
        errors.append(f"Missing {field}")

# Type-specific validation
question_type = question_data.get('Type', '')
if question_type == 'multiple_choice':
    choices = [question_data.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
    valid_choices = [c for c in choices if str(c).strip()]

    if len(valid_choices) < 2:
        warnings.append("Fewer than 2 choices for multiple choice")

    correct_answer = question_data.get('Correct_Answer', '')
    if correct_answer not in ['A', 'B', 'C', 'D']:
        errors.append("Correct answer must be A, B, C, or D for multiple choice")

elif question_type == 'numerical':
    try:
        float(question_data.get('Correct_Answer', ''))
    except (ValueError, TypeError):
        errors.append("Correct answer must be numeric for numerical questions")

# Validate points
try:
    points = float(question_data.get('Points', 0))
    if points <= 0:
        warnings.append("Points should be positive")
except (ValueError, TypeError):
    errors.append("Points must be numeric")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0
}

```
Question Editing Operations
```python
def save_question_changes(question_index: int, changes: Dict[str, Any]) -> bool:
    """
    Save changes to both DataFrame and original_questions
Args:
    question_index: Index of question to update
    changes: Dictionary of field changes

Returns:
    bool: Success status of save operation
"""
try:
    # Get current data
    df = st.session_state['df'].copy()
    original_questions = st.session_state['original_questions'].copy()

    # Validate index bounds
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Update DataFrame
    update_fields = [
        'Title', 'Type', 'Difficulty', 'Points', 'Topic', 'Subtopic',
        'Question_Text', 'Choice_A', 'Choice_B', 'Choice_C', 'Choice_D',
        'Correct_Answer', 'Tolerance', 'Correct_Feedback', 'Incorrect_Feedback'
    ]

    for field in update_fields:
        if field.lower() in changes:
            df.loc[question_index, field] = changes[field.lower()]

    # Update feedback field (for compatibility)
    df.loc[question_index, 'Feedback'] = changes.get('correct_feedback', '')

    # Update original_questions for QTI export compatibility
    if question_index < len(original_questions):
        q = original_questions[question_index]

        # Map changes to original format
        field_mapping = {
            'title': 'title',
            'question_type': 'type',
            'difficulty': 'difficulty',
            'points': 'points',
            'topic': 'topic',
            'subtopic': 'subtopic',
            'question_text': 'question_text',
            'correct_answer': 'correct_answer',
            'tolerance': 'tolerance',
            'correct_feedback': 'feedback_correct',
            'incorrect_feedback': 'feedback_incorrect'
        }

        for change_key, orig_key in field_mapping.items():
            if change_key in changes:
                q[orig_key] = changes[change_key]

        # Update choices for multiple choice
        if changes.get('question_type') == 'multiple_choice':
            q['choices'] = [
                changes.get('choice_a', ''),
                changes.get('choice_b', ''),
                changes.get('choice_c', ''),
                changes.get('choice_d', '')
            ]

    # Validate changes
    validation_results = validate_single_question(df.iloc[question_index])

    # Update session state
    st.session_state['df'] = df
    st.session_state['original_questions'] = original_questions

    # Provide feedback
    if validation_results['is_valid']:
        st.success("✅ Question updated successfully!")
    else:
        st.warning("⚠️ Question saved but has validation issues:")
        for error in validation_results['errors']:
            st.write(f"• {error}")

    return True

except Exception as e:
    st.error(f"Error saving changes: {str(e)}")
    return False

def delete_question(question_index: int) -> bool:
    """
    Delete question from both DataFrame and original_questions
Args:
    question_index: Index of question to delete

Returns:
    bool: Success status of delete operation
"""
try:
    # Get current data
    df = st.session_state['df']
    original_questions = st.session_state['original_questions']

    # Validate index
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Remove from DataFrame and reset index
    df_updated = df.drop(df.index[question_index]).reset_index(drop=True)

    # Remove from original_questions
    original_questions_updated = original_questions.copy()
    original_questions_updated.pop(question_index)

    # Regenerate sequential IDs
    df_updated['ID'] = [f"Q_{i+1:05d}" for i in range(len(df_updated))]

    # Update session state
    st.session_state['df'] = df_updated
    st.session_state['original_questions'] = original_questions_updated

    # Clear related session state
    keys_to_remove = [key for key in st.session_state.keys() 
                     if key.endswith(f"_{question_index}")]
    for key in keys_to_remove:
        del st.session_state[key]

    return True
    display_matches = re.findall(display_math_pattern, text, re.DOTALL)

    # Replace display math with placeholders
    protected_text = text
    for i, match in enumerate(display_matches):
        placeholder = f"__DISPLAY_MATH_{i}__"
        protected_text = protected_text.replace(f"${match}$", placeholder, 1)

    # Convert inline math: $...$ → \(...\)
    inline_math_pattern = r'\$([^$]+?)\
except Exception as e:
    st.error(f"Error saving to history: {str(e)}")
    return False

```
Session State Schema
```python
Primary database state
SESSION_STATE_SCHEMA = {
    # Core database
    'df': pd.DataFrame,                    # Current questions as DataFrame
    'original_questions': List[dict],      # Raw JSON question data
    'metadata': dict,                      # Database metadata
    'filename': str,                       # Current filename
    'loaded_at': str,                      # Load timestamp
# History management
'database_history': List[dict],        # Previous database states
'current_database_id': Optional[int],  # Active database identifier

# Upload state
'upload_state': {
    'files_uploaded': bool,
    'preview_generated': bool,
    'merge_completed': bool,
    'current_preview': 'MergePreviewData',
    'final_database': List[dict],
    'error_message': str
},

# Processing state
'processing_options': dict,            # Last processing configuration
'cleanup_reports': List[dict],         # LaTeX cleanup results
'batch_processed_files': List[str],    # Multi-file processing tracking

# UI state
'current_page': int,                   # Pagination state
'last_page': int,                      # Last accessed page
'selected_filters': dict,              # Active filter configuration

}
```
Database History Management
```python
def display_database_history():
    """
    Display database history with restore options
    Provides rollback functionality for users
    """
    if not st.session_state.get('database_history'):
        return
st.markdown("### 📚 Recent Database History")

for entry in reversed(st.session_state['database_history']):
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
                if st.button(f"🔄 Restore", key=f"restore_{entry['id']}"):
                    if restore_database_from_history(entry['id']):
                        st.success("✅ Database restored!")
                        st.rerun()

def restore_database_from_history(history_id: int) -> bool:
    """
    Restore database from history by ID
Args:
    history_id: Unique identifier for history entry

Returns:
    bool: Success status of restore operation
"""

```

Upload System
modules/upload_interface_v2.py
Purpose: Advanced file upload system with multi-file merge capabilities and conflict resolution
Location: /modules/upload_interface_v2.py
UploadInterfaceV2 Class
```python
class UploadInterfaceV2:
    """
    Phase 3D Upload Interface
    Handles single and multi-file uploads with intelligent conflict resolution
    """
def __init__(self):
    self.file_processor = FileProcessor()
    self.state_manager = UploadStateManager()
    self.merger = DatabaseMerger()

def render_complete_interface(self):
    """
    Render complete upload interface with state management
    Handles all upload scenarios and user interactions
    """
    # Check current state and render appropriate interface
    current_state = self.state_manager.get_current_state()

    if current_state == UploadState.INITIAL:
        self.render_upload_section()
    elif current_state == UploadState.FILES_UPLOADED:
        self.render_processing_section()
    elif current_state == UploadState.PREVIEW_READY:
        self.render_preview_section()
    elif current_state == UploadState.MERGE_COMPLETED:
        self.render_results_section()

def render_upload_section(self):
    """
    Render file upload interface
    Supports single and multiple file selection
    """
    st.markdown("### 📁 Upload Question Database Files")

    uploaded_files = st.file_uploader(
        "Choose JSON files",
        type=['json'],
        accept_multiple_files=True,
        help="Upload one or more JSON question database files"
    )

    if uploaded_files:
        self._handle_file_upload(uploaded_files)

def _handle_file_upload(self, uploaded_files: List):
    """
    Process uploaded files through the file processor

    Args:
        uploaded_files: List of Streamlit uploaded file objects
    """
    processing_results = []

    for uploaded_file in uploaded_files:
        # Read file content
        content = uploaded_file.read().decode('utf-8')

        # Process through FileProcessor
        result = self.file_processor.process_file(
            content=content,
            filename=uploaded_file.name,
            options={'validate': True, 'cleanup_latex': True}
        )

        processing_results.append(result)

    # Store results and update state
    self.state_manager.store_processing_results(processing_results)
    self.state_manager.transition_to(UploadState.FILES_UPLOADED)

```
File Processing Pipeline
```python
class FileProcessor:
    """
    Handles individual file processing with validation and cleanup
    """
def process_file(self, content: str, filename: str, options: Dict) -> Dict:
    """
    Process single file through validation and cleanup pipeline

    Args:
        content: Raw JSON file content
        filename: Original filename
        options: Processing configuration

    Returns:
        dict: Processing results with questions and metadata
    """
    try:
        # Parse JSON content
        raw_data = json.loads(content)

        # Extract questions and metadata
        if isinstance(raw_data, dict) and 'questions' in raw_data:
            questions = raw_data['questions']
            metadata = raw_data.get('metadata', {})
        elif isinstance(raw_data, list):
            questions = raw_data
            metadata = {'format': 'legacy_array'}
        else:
            raise ValueError("Unexpected JSON structure")

        # Validate questions
        validation_results = self._validate_questions(questions)

        # Apply LaTeX cleanup if requested
        if options.get('cleanup_latex', False):
            questions, cleanup_report = self._cleanup_latex(questions)
        else:
            cleanup_report = None

        return {
            'success': True,
            'filename': filename,
            'questions': questions,
            'metadata': metadata,
            'validation_results': validation_results,
            'cleanup_report': cleanup_report,
            'question_count': len(questions)
        }

    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e),
            'questions': [],
            'metadata': {},
            'question_count': 0
        }

def _validate_questions(self, questions: List[Dict]) -> Dict:
    """
    Validate question structure and required fields

    Args:
        questions: List of question dictionaries

    Returns:
        dict: Validation results with errors and warnings
    """
    errors = []
    warnings = []

    required_fields = ['question_text', 'correct_answer', 'type']

    for i, question in enumerate(questions):
        # Check required fields
        missing_fields = [field for field in required_fields if not question.get(field)]
        if missing_fields:
            errors.append(f"Question {i+1}: Missing fields {missing_fields}")

        # Validate question type
        valid_types = ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank']
        if question.get('type') not in valid_types:
            errors.append(f"Question {i+1}: Invalid type '{question.get('type')}'")

        # Type-specific validation
        if question.get('type') == 'multiple_choice':
            choices = question.get('choices', [])
            if len(choices) < 2:
                warnings.append(f"Question {i+1}: Less than 2 choices for multiple choice")

    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0,
        'question_count': len(questions)
    }

```
Conflict Resolution System
```python
class DatabaseMerger:
    """
    Handles merging multiple question databases with conflict resolution
    """
def __init__(self, strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES):
    self.strategy = strategy
    self.conflict_detector = ConflictDetector()
    self.conflict_resolver = ConflictResolver()

def generate_preview(self, existing_df: pd.DataFrame, 
                    new_questions: List[Dict], 
                    auto_renumber: bool = True) -> MergePreview:
    """
    Generate merge preview with conflict analysis

    Args:
        existing_df: Current database DataFrame
        new_questions: Questions to be merged
        auto_renumber: Whether to automatically renumber conflicting IDs

    Returns:
        MergePreview: Detailed preview of merge operation
    """
    # Ensure questions have IDs
    new_questions = self._ensure_questions_have_ids(new_questions)

    # Check if auto-renumbering should be applied
    if auto_renumber and self._should_apply_auto_renumbering(existing_df, new_questions):
        final_questions = self.auto_renumber_questions(existing_df, new_questions)
        auto_renumbered = True
    else:
        final_questions = new_questions
        auto_renumbered = False

    # Detect conflicts with final questions
    conflicts = self.conflict_detector.detect_conflicts(existing_df, final_questions)

    # Calculate statistics
    existing_count = len(existing_df) if existing_df is not None else 0
    new_count = len(new_questions)
    final_count = self._estimate_final_count(existing_count, new_count, conflicts)

    return MergePreview(
        strategy=self.strategy,
        existing_count=existing_count,
        new_count=new_count,
        final_count=final_count,
        conflicts=conflicts,
        auto_renumbered=auto_renumbered,
        merge_summary=self._generate_merge_summary(conflicts, auto_renumbered),
        warnings=self._generate_warnings(conflicts)
    )

def auto_renumber_questions(self, existing_df: pd.DataFrame, 
                           new_questions: List[Dict]) -> List[Dict]:
    """
    Automatically renumber questions to avoid ID conflicts

    Args:
        existing_df: Current database
        new_questions: Questions to renumber

    Returns:
        List[Dict]: Questions with new IDs assigned
    """
    if existing_df is None or len(existing_df) == 0:
        return new_questions

    # Find next available ID
    next_id = self._get_next_available_id(existing_df)

    # Renumber questions
    renumbered_questions = []
    for i, question in enumerate(new_questions):
        new_question = question.copy()
        new_id = next_id + i

        # Update all possible ID fields
        for id_field in ['id', 'question_id', 'ID', 'Question_ID']:
            if id_field in new_question:
                new_question[id_field] = str(new_id)

        # Add ID if none exists
        if not any(field in new_question for field in ['id', 'question_id']):
            new_question['id'] = str(new_id)

        renumbered_questions.append(new_question)

    return renumbered_questions

```
Merge Strategies
```python
class MergeStrategy(Enum):
    """Enumeration of available merge strategies"""
    APPEND_ALL = "append_all"
    SKIP_DUPLICATES = "skip_duplicates"
    REPLACE_DUPLICATES = "replace_duplicates"
    RENAME_DUPLICATES = "rename_duplicates"
class ConflictType(Enum):
    """Types of conflicts that can be detected"""
    QUESTION_ID = "question_id"
    CONTENT_DUPLICATE = "content_duplicate"
    METADATA_CONFLICT = "metadata_conflict"
    LATEX_CONFLICT = "latex_conflict"
@dataclass
class MergePreview:
    """Data structure for merge preview information"""
    strategy: MergeStrategy
    existing_count: int
    new_count: int
    final_count: int
    conflicts: List[Conflict]
    auto_renumbered: bool
    merge_summary: Dict[str, Any]
    warnings: List[str]
def get_conflict_summary(self) -> Dict[str, int]:
    """Generate summary of conflicts by type"""
    summary = {}
    for conflict in self.conflicts:
        key = f"{conflict.type}_{conflict.severity}"
        summary[key] = summary.get(key, 0) + 1
    return summary

```

Database Processing
modules/database_processor.py
Purpose: Core database processing, validation, and transformation functions
Location: /modules/database_processor.py
Core Processing Functions
```python
def load_database_from_json(json_content: str) -> Tuple[Optional[pd.DataFrame], Dict, List, List]:
    """
    Load and process JSON database content with automatic LaTeX processing
Args:
    json_content: Raw JSON string content

Returns:
    Tuple containing:
    - pd.DataFrame: Processed questions as DataFrame
    - dict: Metadata from original JSON
    - list: Original questions list
    - list: Cleanup reports from processing
"""
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
        raise ValueError("Unexpected JSON structure")

    # Convert to standardized DataFrame format
    df = _convert_questions_to_dataframe(questions)

    return df, metadata, questions, []

except json.JSONDecodeError as e:
    st.error(f"Invalid JSON: {e}")
    return None, None, None, None
except Exception as e:
    st.error(f"Error processing database: {e}")
    return None, None, None, None

def _convert_questions_to_dataframe(questions: List[Dict]) -> pd.DataFrame:
    """
    Convert questions list to standardized DataFrame format
Args:
    questions: List of question dictionaries

Returns:
    pd.DataFrame: Standardized question DataFrame
"""
rows = []

for i, q in enumerate(questions):
    # Generate question ID
    question_id = q.get('id', q.get('question_id', f"Q_{i+1:05d}"))

    # Extract and normalize fields
    question_type = q.get('type', 'multiple_choice')
    title = q.get('title', f"Question {i+1}")
    question_text = q.get('question_text', '')

    # Handle choices for multiple choice questions
    choices = q.get('choices', [])
    if not isinstance(choices, list):
        choices = []

    # Ensure exactly 4 choices (pad with empty strings)
    while len(choices) < 4:
        choices.append('')

    # Process correct answer
    original_correct_answer = q.get('correct_answer', '')
    if question_type == 'multiple_choice':
        correct_answer = _find_correct_letter(original_correct_answer, choices[:4])
    else:
        correct_answer = str(original_correct_answer)

    # Extract metadata with defaults
    points = _safe_float(q.get('points', 1))
    tolerance = _safe_float(q.get('tolerance', 0.05))
    topic = q.get('topic', 'General')
    subtopic = q.get('subtopic', '')
    difficulty = q.get('difficulty', 'Easy')

    # Handle feedback
    feedback_correct = q.get('feedback_correct', '')
    feedback_incorrect = q.get('feedback_incorrect', '')

    # Create standardized row
    row = {
        'ID': question_id,
        'Type': question_type,
        'Title': title,
        'Question_Text': question_text,
        'Choice_A': choices[0] if len(choices) > 0 else '',
        'Choice_B': choices[1] if len(choices) > 1 else '',
        'Choice_C': choices[2] if len(choices) > 2 else '',
        'Choice_D': choices[3] if len(choices) > 3 else '',
        'Correct_Answer': correct_answer,
        'Points': points,
        'Tolerance': tolerance,
        'Feedback': feedback_correct,
        'Correct_Feedback': feedback_correct,
        'Incorrect_Feedback': feedback_incorrect,
        'Topic': topic,
        'Subtopic': subtopic,
        'Difficulty': difficulty
    }

    rows.append(row)

return pd.DataFrame(rows)

def _find_correct_letter(correct_text: str, choices: List[str]) -> str:
    """
    Convert correct answer text to letter designation (A, B, C, D)
Args:
    correct_text: Text of correct answer
    choices: List of available choices

Returns:
    str: Letter designation (A-D)
"""
if not correct_text:
    return 'A'

correct_clean = str(correct_text).strip().lower()

# Check if already a letter
if correct_clean.upper() in ['A', 'B', 'C', 'D']:
    return correct_clean.upper()

# Match against choices
for i, choice in enumerate(choices):
    if choice and str(choice).strip().lower() == correct_clean:
        return ['A', 'B', 'C', 'D'][i]

return 'A'  # Fallback

def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback
Args:
    value: Value to convert
    default: Default value if conversion fails

Returns:
    float: Converted value or default
"""
try:
    return float(value) if value is not None else default
except (ValueError, TypeError):
    return default

```
Validation System
```python
def validate_question_database(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive validation of question database
Args:
    df: Question database DataFrame

Returns:
    dict: Validation results with errors, warnings, and status
"""
errors = []
warnings = []

required_fields = ['ID', 'Type', 'Question_Text', 'Correct_Answer']

for idx, row in df.iterrows():
    # Check required fields
    for field in required_fields:
        if pd.isna(row[field]) or str(row[field]).strip() == '':
            errors.append(f"Question {row['ID']}: Missing {field}")

    # Type-specific validation
    if row['Type'] == 'multiple_choice':
        choices = [row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
        non_empty_choices = [c for c in choices if str(c).strip()]

        if len(non_empty_choices) < 2:
            warnings.append(f"Question {row['ID']}: Insufficient choices for multiple choice")

        if row['Correct_Answer'] not in ['A', 'B', 'C', 'D']:
            errors.append(f"Question {row['ID']}: Invalid correct answer for multiple choice")

    elif row['Type'] == 'numerical':
        try:
            float(row['Correct_Answer'])
        except (ValueError, TypeError):
            errors.append(f"Question {row['ID']}: Correct answer must be numeric for numerical type")

    # Validate points
    try:
        points = float(row.get('Points', 0))
        if points <= 0:
            warnings.append(f"Question {row['ID']}: Points should be positive")
    except (ValueError, TypeError):
        errors.append(f"Question {row['ID']}: Points must be numeric")

    # Check for LaTeX syntax issues
    question_text = str(row.get('Question_Text', ''))
    if ' in question_text:
        dollar_count = question_text.count(')
        if dollar_count % 2 != 0:
            warnings.append(f"Question {row['ID']}: Unmatched LaTeX delimiters")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0,
    'question_count': len(df),
    'validation_summary': {
        'total_questions': len(df),
        'error_count': len(errors),
        'warning_count': len(warnings),
        'success_rate': (len(df) - len(errors)) / len(df) if len(df) > 0 else 0
    }
}

def validate_single_question(question_row: Dict) -> Dict[str, Any]:
    """
    Validate individual question for editing operations
Args:
    question_row: Single question data (dict or Series)

Returns:
    dict: Validation results for single question
"""
errors = []
warnings = []

# Convert Series to dict if needed
if hasattr(question_row, 'to_dict'):
    question_data = question_row.to_dict()
else:
    question_data = question_row

# Check required fields
required_fields = ['Title', 'Type', 'Question_Text', 'Correct_Answer']
for field in required_fields:
    value = question_data.get(field, '')
    if not value or str(value).strip() == '' or str(value).lower() == 'nan':
        errors.append(f"Missing {field}")

# Type-specific validation
question_type = question_data.get('Type', '')
if question_type == 'multiple_choice':
    choices = [question_data.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
    valid_choices = [c for c in choices if str(c).strip()]

    if len(valid_choices) < 2:
        warnings.append("Fewer than 2 choices for multiple choice")

    correct_answer = question_data.get('Correct_Answer', '')
    if correct_answer not in ['A', 'B', 'C', 'D']:
        errors.append("Correct answer must be A, B, C, or D for multiple choice")

elif question_type == 'numerical':
    try:
        float(question_data.get('Correct_Answer', ''))
    except (ValueError, TypeError):
        errors.append("Correct answer must be numeric for numerical questions")

# Validate points
try:
    points = float(question_data.get('Points', 0))
    if points <= 0:
        warnings.append("Points should be positive")
except (ValueError, TypeError):
    errors.append("Points must be numeric")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0
}

```
Question Editing Operations
```python
def save_question_changes(question_index: int, changes: Dict[str, Any]) -> bool:
    """
    Save changes to both DataFrame and original_questions
Args:
    question_index: Index of question to update
    changes: Dictionary of field changes

Returns:
    bool: Success status of save operation
"""
try:
    # Get current data
    df = st.session_state['df'].copy()
    original_questions = st.session_state['original_questions'].copy()

    # Validate index bounds
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Update DataFrame
    update_fields = [
        'Title', 'Type', 'Difficulty', 'Points', 'Topic', 'Subtopic',
        'Question_Text', 'Choice_A', 'Choice_B', 'Choice_C', 'Choice_D',
        'Correct_Answer', 'Tolerance', 'Correct_Feedback', 'Incorrect_Feedback'
    ]

    for field in update_fields:
        if field.lower() in changes:
            df.loc[question_index, field] = changes[field.lower()]

    # Update feedback field (for compatibility)
    df.loc[question_index, 'Feedback'] = changes.get('correct_feedback', '')

    # Update original_questions for QTI export compatibility
    if question_index < len(original_questions):
        q = original_questions[question_index]

        # Map changes to original format
        field_mapping = {
            'title': 'title',
            'question_type': 'type',
            'difficulty': 'difficulty',
            'points': 'points',
            'topic': 'topic',
            'subtopic': 'subtopic',
            'question_text': 'question_text',
            'correct_answer': 'correct_answer',
            'tolerance': 'tolerance',
            'correct_feedback': 'feedback_correct',
            'incorrect_feedback': 'feedback_incorrect'
        }

        for change_key, orig_key in field_mapping.items():
            if change_key in changes:
                q[orig_key] = changes[change_key]

        # Update choices for multiple choice
        if changes.get('question_type') == 'multiple_choice':
            q['choices'] = [
                changes.get('choice_a', ''),
                changes.get('choice_b', ''),
                changes.get('choice_c', ''),
                changes.get('choice_d', '')
            ]

    # Validate changes
    validation_results = validate_single_question(df.iloc[question_index])

    # Update session state
    st.session_state['df'] = df
    st.session_state['original_questions'] = original_questions

    # Provide feedback
    if validation_results['is_valid']:
        st.success("✅ Question updated successfully!")
    else:
        st.warning("⚠️ Question saved but has validation issues:")
        for error in validation_results['errors']:
            st.write(f"• {error}")

    return True

except Exception as e:
    st.error(f"Error saving changes: {str(e)}")
    return False

def delete_question(question_index: int) -> bool:
    """
    Delete question from both DataFrame and original_questions
Args:
    question_index: Index of question to delete

Returns:
    bool: Success status of delete operation
"""
try:
    # Get current data
    df = st.session_state['df']
    original_questions = st.session_state['original_questions']

    # Validate index
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Remove from DataFrame and reset index
    df_updated = df.drop(df.index[question_index]).reset_index(drop=True)

    # Remove from original_questions
    original_questions_updated = original_questions.copy()
    original_questions_updated.pop(question_index)

    # Regenerate sequential IDs
    df_updated['ID'] = [f"Q_{i+1:05d}" for i in range(len(df_updated))]

    # Update session state
    st.session_state['df'] = df_updated
    st.session_state['original_questions'] = original_questions_updated

    # Clear related session state
    keys_to_remove = [key for key in st.session_state.keys() 
                     if key.endswith(f"_{question_index}")]
    for key in keys_to_remove:
        del st.session_state[key]

    return True
    protected_text = re.sub(inline_math_pattern, r'\\(\1\\)', protected_text)

    # Restore display math
    for i, match in enumerate(display_matches):
        placeholder = f"__DISPLAY_MATH_{i}__"
        protected_text = protected_text.replace(placeholder, f"${match}$")

    return protected_text

class CanvasAdapter:
    """
    Canvas-specific adaptations for QTI content
    """
def adapt_question(self, question: Dict) -> Dict:
    """
    Apply Canvas-specific question adaptations

    Args:
        question: Question to adapt

    Returns:
        Dict: Canvas-adapted question
    """
    adapted = question.copy()

    # Ensure required Canvas fields
    if 'points' not in adapted:
        adapted['points'] = 1

    # Validate question type
    valid_types = ['multiple_choice', 'numerical_answer', 'true_false', 'fill_in_multiple_blanks']
    if adapted.get('type') not in valid_types:
        # Map common types to Canvas types
        type_mapping = {
            'numerical': 'numerical_answer',
            'fill_in_blank': 'fill_in_multiple_blanks'
        }
        adapted['type'] = type_mapping.get(adapted.get('type'), 'multiple_choice')

    # Ensure multiple choice questions have proper structure
    if adapted['type'] == 'multiple_choice':
        adapted = self._adapt_multiple_choice(adapted)

    return adapted

def _adapt_multiple_choice(self, question: Dict) -> Dict:
    """
    Adapt multiple choice question for Canvas

    Args:
        question: Multiple choice question

    Returns:
        Dict: Canvas-adapted multiple choice question
    """
    adapted = question.copy()

    # Ensure choices are properly formatted
    if 'choices' in adapted and isinstance(adapted['choices'], list):
        # Remove empty choices
        adapted['choices'] = [choice for choice in adapted['choices'] if choice.strip()]

        # Ensure at least 2 choices
        while len(adapted['choices']) < 2:
            adapted['choices'].append(f"Choice {len(adapted['choices']) + 1}")

    # Validate correct answer format
    if 'correct_answer' in adapted:
        correct = adapted['correct_answer']
        if isinstance(correct, str) and correct.upper() in ['A', 'B', 'C', 'D']:
            # Convert letter to index for Canvas
            letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            adapted['correct_answer_index'] = letter_to_index[correct.upper()]

    return adapted

```

LaTeX Processing
modules/latex_processor.py
Purpose: LaTeX cleanup and processing for educational mathematical content
Location: /modules/latex_processor.py
LaTeX Processing Pipeline
```python
class LaTeXProcessor:
    """
    Comprehensive LaTeX processing for educational content
    Handles cleanup, validation, and optimization
    """
def __init__(self):
    self.unicode_map = self._build_unicode_map()
    self.validation_patterns = self._build_validation_patterns()

def process_questions(self, questions: List[Dict], 
                     cleanup_options: Dict[str, bool] = None) -> Tuple[List[Dict], List[Dict]]:
    """
    Process list of questions for LaTeX cleanup

    Args:
        questions: List of question dictionaries
        cleanup_options: Options for cleanup operations

    Returns:
        Tuple of (processed_questions, cleanup_reports)
    """
    if cleanup_options is None:
        cleanup_options = {
            'convert_unicode': True,
            'fix_delimiters': True,
            'validate_syntax': True,
            'optimize_spacing': True
        }

    processed_questions = []
    cleanup_reports = []

    for i, question in enumerate(questions):
        processed_question, report = self.process_single_question(
            question, cleanup_options
        )

        processed_questions.append(processed_question)

        if report['changes_made']:
            report['question_index'] = i
            cleanup_reports.append(report)

    return processed_questions, cleanup_reports

def process_single_question(self, question: Dict, 
                           cleanup_options: Dict[str, bool]) -> Tuple[Dict, Dict]:
    """
    Process single question for LaTeX cleanup

    Args:
        question: Question dictionary
        cleanup_options: Cleanup configuration

    Returns:
        Tuple of (processed_question, cleanup_report)
    """
    processed = question.copy()
    report = {
        'changes_made': False,
        'operations': [],
        'errors': [],
        'warnings': []
    }

    # Fields that may contain LaTeX
    latex_fields = [
        'question_text', 'feedback_correct', 'feedback_incorrect'
    ]

    # Add choices if they exist
    if 'choices' in processed and isinstance(processed['choices'], list):
        latex_fields.append('choices')

    for field in latex_fields:
        if field in processed:
            if field == 'choices':
                # Process each choice
                original_choices = processed[field].copy()
                processed_choices = []

                for choice in original_choices:
                    processed_choice, field_report = self._process_text_field(
                        choice, cleanup_options
                    )
                    processed_choices.append(processed_choice)

                    if field_report['changes_made']:
                        report['changes_made'] = True
                        report['operations'].extend(field_report['operations'])

                processed[field] = processed_choices

            else:
                # Process single text field
                original_text = processed[field]
                processed_text, field_report = self._process_text_field(
                    original_text, cleanup_options
                )

                processed[field] = processed_text

                if field_report['changes_made']:
                    report['changes_made'] = True
                    report['operations'].extend(field_report['operations'])
                    report['errors'].extend(field_report['errors'])
                    report['warnings'].extend(field_report['warnings'])

    return processed, report

def _process_text_field(self, text: str, 
                       cleanup_options: Dict[str, bool]) -> Tuple[str, Dict]:
    """
    Process individual text field for LaTeX cleanup

    Args:
        text: Text content to process
        cleanup_options: Cleanup configuration

    Returns:
        Tuple of (processed_text, field_report)
    """
    if not isinstance(text, str) or not text.strip():
        return text, {'changes_made': False, 'operations': [], 'errors': [], 'warnings': []}

    processed_text = text
    report = {
        'changes_made': False,
        'operations': [],
        'errors': [],
        'warnings': []
    }

    # Unicode to LaTeX conversion
    if cleanup_options.get('convert_unicode', True):
        converted_text = self._convert_unicode_to_latex(processed_text)
        if converted_text != processed_text:
            report['changes_made'] = True
            report['operations'].append('Unicode symbols converted to LaTeX')
            processed_text = converted_text

    # Fix LaTeX delimiters
    if cleanup_options.get('fix_delimiters', True):
        fixed_text = self._fix_latex_delimiters(processed_text)
        if fixed_text != processed_text:
            report['changes_made'] = True
            report['operations'].append('LaTeX delimiters fixed')
            processed_text = fixed_text

    # Optimize spacing
    if cleanup_options.get('optimize_spacing', True):
        optimized_text = self._optimize_latex_spacing(processed_text)
        if optimized_text != processed_text:
            report['changes_made'] = True
            report['operations'].append('LaTeX spacing optimized')
            processed_text = optimized_text

    # Validate syntax
    if cleanup_options.get('validate_syntax', True):
        validation_results = self._validate_latex_syntax(processed_text)
        if validation_results['errors']:
            report['errors'].extend(validation_results['errors'])
        if validation_results['warnings']:
            report['warnings'].extend(validation_results['warnings'])

    return processed_text, report

def _convert_unicode_to_latex(self, text: str) -> str:
    """
    Convert Unicode mathematical symbols to LaTeX equivalents

    Args:
        text: Text containing Unicode symbols

    Returns:
        str: Text with LaTeX equivalents
    """
    converted = text

    for unicode_char, latex_equiv in self.unicode_map
except Exception as e:
    st.error(f"Error saving to history: {str(e)}")
    return False

```
Session State Schema
```python
Primary database state
SESSION_STATE_SCHEMA = {
    # Core database
    'df': pd.DataFrame,                    # Current questions as DataFrame
    'original_questions': List[dict],      # Raw JSON question data
    'metadata': dict,                      # Database metadata
    'filename': str,                       # Current filename
    'loaded_at': str,                      # Load timestamp
# History management
'database_history': List[dict],        # Previous database states
'current_database_id': Optional[int],  # Active database identifier

# Upload state
'upload_state': {
    'files_uploaded': bool,
    'preview_generated': bool,
    'merge_completed': bool,
    'current_preview': 'MergePreviewData',
    'final_database': List[dict],
    'error_message': str
},

# Processing state
'processing_options': dict,            # Last processing configuration
'cleanup_reports': List[dict],         # LaTeX cleanup results
'batch_processed_files': List[str],    # Multi-file processing tracking

# UI state
'current_page': int,                   # Pagination state
'last_page': int,                      # Last accessed page
'selected_filters': dict,              # Active filter configuration

}
```
Database History Management
```python
def display_database_history():
    """
    Display database history with restore options
    Provides rollback functionality for users
    """
    if not st.session_state.get('database_history'):
        return
st.markdown("### 📚 Recent Database History")

for entry in reversed(st.session_state['database_history']):
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
                if st.button(f"🔄 Restore", key=f"restore_{entry['id']}"):
                    if restore_database_from_history(entry['id']):
                        st.success("✅ Database restored!")
                        st.rerun()

def restore_database_from_history(history_id: int) -> bool:
    """
    Restore database from history by ID
Args:
    history_id: Unique identifier for history entry

Returns:
    bool: Success status of restore operation
"""

```

Upload System
modules/upload_interface_v2.py
Purpose: Advanced file upload system with multi-file merge capabilities and conflict resolution
Location: /modules/upload_interface_v2.py
UploadInterfaceV2 Class
```python
class UploadInterfaceV2:
    """
    Phase 3D Upload Interface
    Handles single and multi-file uploads with intelligent conflict resolution
    """
def __init__(self):
    self.file_processor = FileProcessor()
    self.state_manager = UploadStateManager()
    self.merger = DatabaseMerger()

def render_complete_interface(self):
    """
    Render complete upload interface with state management
    Handles all upload scenarios and user interactions
    """
    # Check current state and render appropriate interface
    current_state = self.state_manager.get_current_state()

    if current_state == UploadState.INITIAL:
        self.render_upload_section()
    elif current_state == UploadState.FILES_UPLOADED:
        self.render_processing_section()
    elif current_state == UploadState.PREVIEW_READY:
        self.render_preview_section()
    elif current_state == UploadState.MERGE_COMPLETED:
        self.render_results_section()

def render_upload_section(self):
    """
    Render file upload interface
    Supports single and multiple file selection
    """
    st.markdown("### 📁 Upload Question Database Files")

    uploaded_files = st.file_uploader(
        "Choose JSON files",
        type=['json'],
        accept_multiple_files=True,
        help="Upload one or more JSON question database files"
    )

    if uploaded_files:
        self._handle_file_upload(uploaded_files)

def _handle_file_upload(self, uploaded_files: List):
    """
    Process uploaded files through the file processor

    Args:
        uploaded_files: List of Streamlit uploaded file objects
    """
    processing_results = []

    for uploaded_file in uploaded_files:
        # Read file content
        content = uploaded_file.read().decode('utf-8')

        # Process through FileProcessor
        result = self.file_processor.process_file(
            content=content,
            filename=uploaded_file.name,
            options={'validate': True, 'cleanup_latex': True}
        )

        processing_results.append(result)

    # Store results and update state
    self.state_manager.store_processing_results(processing_results)
    self.state_manager.transition_to(UploadState.FILES_UPLOADED)

```
File Processing Pipeline
```python
class FileProcessor:
    """
    Handles individual file processing with validation and cleanup
    """
def process_file(self, content: str, filename: str, options: Dict) -> Dict:
    """
    Process single file through validation and cleanup pipeline

    Args:
        content: Raw JSON file content
        filename: Original filename
        options: Processing configuration

    Returns:
        dict: Processing results with questions and metadata
    """
    try:
        # Parse JSON content
        raw_data = json.loads(content)

        # Extract questions and metadata
        if isinstance(raw_data, dict) and 'questions' in raw_data:
            questions = raw_data['questions']
            metadata = raw_data.get('metadata', {})
        elif isinstance(raw_data, list):
            questions = raw_data
            metadata = {'format': 'legacy_array'}
        else:
            raise ValueError("Unexpected JSON structure")

        # Validate questions
        validation_results = self._validate_questions(questions)

        # Apply LaTeX cleanup if requested
        if options.get('cleanup_latex', False):
            questions, cleanup_report = self._cleanup_latex(questions)
        else:
            cleanup_report = None

        return {
            'success': True,
            'filename': filename,
            'questions': questions,
            'metadata': metadata,
            'validation_results': validation_results,
            'cleanup_report': cleanup_report,
            'question_count': len(questions)
        }

    except Exception as e:
        return {
            'success': False,
            'filename': filename,
            'error': str(e),
            'questions': [],
            'metadata': {},
            'question_count': 0
        }

def _validate_questions(self, questions: List[Dict]) -> Dict:
    """
    Validate question structure and required fields

    Args:
        questions: List of question dictionaries

    Returns:
        dict: Validation results with errors and warnings
    """
    errors = []
    warnings = []

    required_fields = ['question_text', 'correct_answer', 'type']

    for i, question in enumerate(questions):
        # Check required fields
        missing_fields = [field for field in required_fields if not question.get(field)]
        if missing_fields:
            errors.append(f"Question {i+1}: Missing fields {missing_fields}")

        # Validate question type
        valid_types = ['multiple_choice', 'numerical', 'true_false', 'fill_in_blank']
        if question.get('type') not in valid_types:
            errors.append(f"Question {i+1}: Invalid type '{question.get('type')}'")

        # Type-specific validation
        if question.get('type') == 'multiple_choice':
            choices = question.get('choices', [])
            if len(choices) < 2:
                warnings.append(f"Question {i+1}: Less than 2 choices for multiple choice")

    return {
        'errors': errors,
        'warnings': warnings,
        'is_valid': len(errors) == 0,
        'question_count': len(questions)
    }

```
Conflict Resolution System
```python
class DatabaseMerger:
    """
    Handles merging multiple question databases with conflict resolution
    """
def __init__(self, strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES):
    self.strategy = strategy
    self.conflict_detector = ConflictDetector()
    self.conflict_resolver = ConflictResolver()

def generate_preview(self, existing_df: pd.DataFrame, 
                    new_questions: List[Dict], 
                    auto_renumber: bool = True) -> MergePreview:
    """
    Generate merge preview with conflict analysis

    Args:
        existing_df: Current database DataFrame
        new_questions: Questions to be merged
        auto_renumber: Whether to automatically renumber conflicting IDs

    Returns:
        MergePreview: Detailed preview of merge operation
    """
    # Ensure questions have IDs
    new_questions = self._ensure_questions_have_ids(new_questions)

    # Check if auto-renumbering should be applied
    if auto_renumber and self._should_apply_auto_renumbering(existing_df, new_questions):
        final_questions = self.auto_renumber_questions(existing_df, new_questions)
        auto_renumbered = True
    else:
        final_questions = new_questions
        auto_renumbered = False

    # Detect conflicts with final questions
    conflicts = self.conflict_detector.detect_conflicts(existing_df, final_questions)

    # Calculate statistics
    existing_count = len(existing_df) if existing_df is not None else 0
    new_count = len(new_questions)
    final_count = self._estimate_final_count(existing_count, new_count, conflicts)

    return MergePreview(
        strategy=self.strategy,
        existing_count=existing_count,
        new_count=new_count,
        final_count=final_count,
        conflicts=conflicts,
        auto_renumbered=auto_renumbered,
        merge_summary=self._generate_merge_summary(conflicts, auto_renumbered),
        warnings=self._generate_warnings(conflicts)
    )

def auto_renumber_questions(self, existing_df: pd.DataFrame, 
                           new_questions: List[Dict]) -> List[Dict]:
    """
    Automatically renumber questions to avoid ID conflicts

    Args:
        existing_df: Current database
        new_questions: Questions to renumber

    Returns:
        List[Dict]: Questions with new IDs assigned
    """
    if existing_df is None or len(existing_df) == 0:
        return new_questions

    # Find next available ID
    next_id = self._get_next_available_id(existing_df)

    # Renumber questions
    renumbered_questions = []
    for i, question in enumerate(new_questions):
        new_question = question.copy()
        new_id = next_id + i

        # Update all possible ID fields
        for id_field in ['id', 'question_id', 'ID', 'Question_ID']:
            if id_field in new_question:
                new_question[id_field] = str(new_id)

        # Add ID if none exists
        if not any(field in new_question for field in ['id', 'question_id']):
            new_question['id'] = str(new_id)

        renumbered_questions.append(new_question)

    return renumbered_questions

```
Merge Strategies
```python
class MergeStrategy(Enum):
    """Enumeration of available merge strategies"""
    APPEND_ALL = "append_all"
    SKIP_DUPLICATES = "skip_duplicates"
    REPLACE_DUPLICATES = "replace_duplicates"
    RENAME_DUPLICATES = "rename_duplicates"
class ConflictType(Enum):
    """Types of conflicts that can be detected"""
    QUESTION_ID = "question_id"
    CONTENT_DUPLICATE = "content_duplicate"
    METADATA_CONFLICT = "metadata_conflict"
    LATEX_CONFLICT = "latex_conflict"
@dataclass
class MergePreview:
    """Data structure for merge preview information"""
    strategy: MergeStrategy
    existing_count: int
    new_count: int
    final_count: int
    conflicts: List[Conflict]
    auto_renumbered: bool
    merge_summary: Dict[str, Any]
    warnings: List[str]
def get_conflict_summary(self) -> Dict[str, int]:
    """Generate summary of conflicts by type"""
    summary = {}
    for conflict in self.conflicts:
        key = f"{conflict.type}_{conflict.severity}"
        summary[key] = summary.get(key, 0) + 1
    return summary

```

Database Processing
modules/database_processor.py
Purpose: Core database processing, validation, and transformation functions
Location: /modules/database_processor.py
Core Processing Functions
```python
def load_database_from_json(json_content: str) -> Tuple[Optional[pd.DataFrame], Dict, List, List]:
    """
    Load and process JSON database content with automatic LaTeX processing
Args:
    json_content: Raw JSON string content

Returns:
    Tuple containing:
    - pd.DataFrame: Processed questions as DataFrame
    - dict: Metadata from original JSON
    - list: Original questions list
    - list: Cleanup reports from processing
"""
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
        raise ValueError("Unexpected JSON structure")

    # Convert to standardized DataFrame format
    df = _convert_questions_to_dataframe(questions)

    return df, metadata, questions, []

except json.JSONDecodeError as e:
    st.error(f"Invalid JSON: {e}")
    return None, None, None, None
except Exception as e:
    st.error(f"Error processing database: {e}")
    return None, None, None, None

def _convert_questions_to_dataframe(questions: List[Dict]) -> pd.DataFrame:
    """
    Convert questions list to standardized DataFrame format
Args:
    questions: List of question dictionaries

Returns:
    pd.DataFrame: Standardized question DataFrame
"""
rows = []

for i, q in enumerate(questions):
    # Generate question ID
    question_id = q.get('id', q.get('question_id', f"Q_{i+1:05d}"))

    # Extract and normalize fields
    question_type = q.get('type', 'multiple_choice')
    title = q.get('title', f"Question {i+1}")
    question_text = q.get('question_text', '')

    # Handle choices for multiple choice questions
    choices = q.get('choices', [])
    if not isinstance(choices, list):
        choices = []

    # Ensure exactly 4 choices (pad with empty strings)
    while len(choices) < 4:
        choices.append('')

    # Process correct answer
    original_correct_answer = q.get('correct_answer', '')
    if question_type == 'multiple_choice':
        correct_answer = _find_correct_letter(original_correct_answer, choices[:4])
    else:
        correct_answer = str(original_correct_answer)

    # Extract metadata with defaults
    points = _safe_float(q.get('points', 1))
    tolerance = _safe_float(q.get('tolerance', 0.05))
    topic = q.get('topic', 'General')
    subtopic = q.get('subtopic', '')
    difficulty = q.get('difficulty', 'Easy')

    # Handle feedback
    feedback_correct = q.get('feedback_correct', '')
    feedback_incorrect = q.get('feedback_incorrect', '')

    # Create standardized row
    row = {
        'ID': question_id,
        'Type': question_type,
        'Title': title,
        'Question_Text': question_text,
        'Choice_A': choices[0] if len(choices) > 0 else '',
        'Choice_B': choices[1] if len(choices) > 1 else '',
        'Choice_C': choices[2] if len(choices) > 2 else '',
        'Choice_D': choices[3] if len(choices) > 3 else '',
        'Correct_Answer': correct_answer,
        'Points': points,
        'Tolerance': tolerance,
        'Feedback': feedback_correct,
        'Correct_Feedback': feedback_correct,
        'Incorrect_Feedback': feedback_incorrect,
        'Topic': topic,
        'Subtopic': subtopic,
        'Difficulty': difficulty
    }

    rows.append(row)

return pd.DataFrame(rows)

def _find_correct_letter(correct_text: str, choices: List[str]) -> str:
    """
    Convert correct answer text to letter designation (A, B, C, D)
Args:
    correct_text: Text of correct answer
    choices: List of available choices

Returns:
    str: Letter designation (A-D)
"""
if not correct_text:
    return 'A'

correct_clean = str(correct_text).strip().lower()

# Check if already a letter
if correct_clean.upper() in ['A', 'B', 'C', 'D']:
    return correct_clean.upper()

# Match against choices
for i, choice in enumerate(choices):
    if choice and str(choice).strip().lower() == correct_clean:
        return ['A', 'B', 'C', 'D'][i]

return 'A'  # Fallback

def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback
Args:
    value: Value to convert
    default: Default value if conversion fails

Returns:
    float: Converted value or default
"""
try:
    return float(value) if value is not None else default
except (ValueError, TypeError):
    return default

```
Validation System
```python
def validate_question_database(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive validation of question database
Args:
    df: Question database DataFrame

Returns:
    dict: Validation results with errors, warnings, and status
"""
errors = []
warnings = []

required_fields = ['ID', 'Type', 'Question_Text', 'Correct_Answer']

for idx, row in df.iterrows():
    # Check required fields
    for field in required_fields:
        if pd.isna(row[field]) or str(row[field]).strip() == '':
            errors.append(f"Question {row['ID']}: Missing {field}")

    # Type-specific validation
    if row['Type'] == 'multiple_choice':
        choices = [row.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
        non_empty_choices = [c for c in choices if str(c).strip()]

        if len(non_empty_choices) < 2:
            warnings.append(f"Question {row['ID']}: Insufficient choices for multiple choice")

        if row['Correct_Answer'] not in ['A', 'B', 'C', 'D']:
            errors.append(f"Question {row['ID']}: Invalid correct answer for multiple choice")

    elif row['Type'] == 'numerical':
        try:
            float(row['Correct_Answer'])
        except (ValueError, TypeError):
            errors.append(f"Question {row['ID']}: Correct answer must be numeric for numerical type")

    # Validate points
    try:
        points = float(row.get('Points', 0))
        if points <= 0:
            warnings.append(f"Question {row['ID']}: Points should be positive")
    except (ValueError, TypeError):
        errors.append(f"Question {row['ID']}: Points must be numeric")

    # Check for LaTeX syntax issues
    question_text = str(row.get('Question_Text', ''))
    if ' in question_text:
        dollar_count = question_text.count(')
        if dollar_count % 2 != 0:
            warnings.append(f"Question {row['ID']}: Unmatched LaTeX delimiters")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0,
    'question_count': len(df),
    'validation_summary': {
        'total_questions': len(df),
        'error_count': len(errors),
        'warning_count': len(warnings),
        'success_rate': (len(df) - len(errors)) / len(df) if len(df) > 0 else 0
    }
}

def validate_single_question(question_row: Dict) -> Dict[str, Any]:
    """
    Validate individual question for editing operations
Args:
    question_row: Single question data (dict or Series)

Returns:
    dict: Validation results for single question
"""
errors = []
warnings = []

# Convert Series to dict if needed
if hasattr(question_row, 'to_dict'):
    question_data = question_row.to_dict()
else:
    question_data = question_row

# Check required fields
required_fields = ['Title', 'Type', 'Question_Text', 'Correct_Answer']
for field in required_fields:
    value = question_data.get(field, '')
    if not value or str(value).strip() == '' or str(value).lower() == 'nan':
        errors.append(f"Missing {field}")

# Type-specific validation
question_type = question_data.get('Type', '')
if question_type == 'multiple_choice':
    choices = [question_data.get(f'Choice_{c}', '') for c in ['A', 'B', 'C', 'D']]
    valid_choices = [c for c in choices if str(c).strip()]

    if len(valid_choices) < 2:
        warnings.append("Fewer than 2 choices for multiple choice")

    correct_answer = question_data.get('Correct_Answer', '')
    if correct_answer not in ['A', 'B', 'C', 'D']:
        errors.append("Correct answer must be A, B, C, or D for multiple choice")

elif question_type == 'numerical':
    try:
        float(question_data.get('Correct_Answer', ''))
    except (ValueError, TypeError):
        errors.append("Correct answer must be numeric for numerical questions")

# Validate points
try:
    points = float(question_data.get('Points', 0))
    if points <= 0:
        warnings.append("Points should be positive")
except (ValueError, TypeError):
    errors.append("Points must be numeric")

return {
    'errors': errors,
    'warnings': warnings,
    'is_valid': len(errors) == 0
}

```
Question Editing Operations
```python
def save_question_changes(question_index: int, changes: Dict[str, Any]) -> bool:
    """
    Save changes to both DataFrame and original_questions
Args:
    question_index: Index of question to update
    changes: Dictionary of field changes

Returns:
    bool: Success status of save operation
"""
try:
    # Get current data
    df = st.session_state['df'].copy()
    original_questions = st.session_state['original_questions'].copy()

    # Validate index bounds
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Update DataFrame
    update_fields = [
        'Title', 'Type', 'Difficulty', 'Points', 'Topic', 'Subtopic',
        'Question_Text', 'Choice_A', 'Choice_B', 'Choice_C', 'Choice_D',
        'Correct_Answer', 'Tolerance', 'Correct_Feedback', 'Incorrect_Feedback'
    ]

    for field in update_fields:
        if field.lower() in changes:
            df.loc[question_index, field] = changes[field.lower()]

    # Update feedback field (for compatibility)
    df.loc[question_index, 'Feedback'] = changes.get('correct_feedback', '')

    # Update original_questions for QTI export compatibility
    if question_index < len(original_questions):
        q = original_questions[question_index]

        # Map changes to original format
        field_mapping = {
            'title': 'title',
            'question_type': 'type',
            'difficulty': 'difficulty',
            'points': 'points',
            'topic': 'topic',
            'subtopic': 'subtopic',
            'question_text': 'question_text',
            'correct_answer': 'correct_answer',
            'tolerance': 'tolerance',
            'correct_feedback': 'feedback_correct',
            'incorrect_feedback': 'feedback_incorrect'
        }

        for change_key, orig_key in field_mapping.items():
            if change_key in changes:
                q[orig_key] = changes[change_key]

        # Update choices for multiple choice
        if changes.get('question_type') == 'multiple_choice':
            q['choices'] = [
                changes.get('choice_a', ''),
                changes.get('choice_b', ''),
                changes.get('choice_c', ''),
                changes.get('choice_d', '')
            ]

    # Validate changes
    validation_results = validate_single_question(df.iloc[question_index])

    # Update session state
    st.session_state['df'] = df
    st.session_state['original_questions'] = original_questions

    # Provide feedback
    if validation_results['is_valid']:
        st.success("✅ Question updated successfully!")
    else:
        st.warning("⚠️ Question saved but has validation issues:")
        for error in validation_results['errors']:
            st.write(f"• {error}")

    return True

except Exception as e:
    st.error(f"Error saving changes: {str(e)}")
    return False

def delete_question(question_index: int) -> bool:
    """
    Delete question from both DataFrame and original_questions
Args:
    question_index: Index of question to delete

Returns:
    bool: Success status of delete operation
"""
try:
    # Get current data
    df = st.session_state['df']
    original_questions = st.session_state['original_questions']

    # Validate index
    if question_index >= len(df) or question_index >= len(original_questions):
        st.error("Invalid question index")
        return False

    # Remove from DataFrame and reset index
    df_updated = df.drop(df.index[question_index]).reset_index(drop=True)

    # Remove from original_questions
    original_questions_updated = original_questions.copy()
    original_questions_updated.pop(question_index)

    # Regenerate sequential IDs
    df_updated['ID'] = [f"Q_{i+1:05d}" for i in range(len(df_updated))]

    # Update session state
    st.session_state['df'] = df_updated
    st.session_state['original_questions'] = original_questions_updated

    # Clear related session state
    keys_to_remove = [key for key in st.session_state.keys() 
                     if key.endswith(f"_{question_index}")]
    for key in keys_to_remove:
        del st.session_state[key]

    return True
API.md - JSON Export Integration Updates
Sections to Add/Update
1. Export System Section - Add JSON Export Module
Add after existing export system documentation:
```markdown
JSON Export Module
modules/exporter.py - Enhanced with JSON Support
New JSON Export Methods:
```python
def _render_json_export(self, df: pd.DataFrame, original_questions: List[Dict[str, Any]]):
    """
    Render JSON export interface with complete configuration options
Args:
    df: Filtered DataFrame containing questions to export
    original_questions: Original question data with LaTeX preserved
"""

def _export_json(self, df: pd.DataFrame, 
                original_questions: List[Dict[str, Any]], 
                filename: str,
                include_metadata: bool = True,
                format_style: str = "Pretty (indented)",
                preserve_ids: bool = True) -> None:
    """
    Export filtered questions to JSON format with comprehensive options
Args:
    df: Filtered DataFrame
    original_questions: Original question data  
    filename: Output filename
    include_metadata: Whether to include metadata section
    format_style: JSON formatting style ("Compact" or "Pretty (indented)")
    preserve_ids: Whether to preserve original IDs
"""

def _create_export_metadata(self, df: pd.DataFrame, 
                           questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create comprehensive metadata section for JSON export
Returns:
    Dictionary containing export statistics, analytics, and metadata
"""

```
JSON Export Configuration
```python
Export type selection enhancement
export_type = st.radio(
    "Choose Export Format:",
    [
        "📊 CSV Export", 
        "📦 QTI Package for Canvas",
        "📄 JSON Database (Native Format)"  # NEW OPTION
    ],
    key="export_type_selection"
)
```
JSON Export Options Interface
```python
JSON-specific configuration options
with st.expander("⚙️ JSON Export Options"):
    include_metadata = st.checkbox(
        "Include metadata section",
        value=True,
        help="Include course/instructor metadata in the JSON file"
    )
format_style = st.selectbox(
    "JSON formatting:",
    ["Compact", "Pretty (indented)"],
    index=1,
    help="Choose formatting style for the JSON output"
)

preserve_ids = st.checkbox(
    "Preserve original question IDs",
    value=True,
    help="Keep original question ID numbering from source"
)


2. Data Flow Architecture - Update with JSON Export
Add to existing data flow section:
```markdown
Enhanced Data Flow with JSON Export
JSON Input → FileProcessor → ConflictResolver → 
DatabaseMerger → SessionManager → UIComponents → 
Multi-Format Exporter → (QTI/JSON/CSV) Output
                  ↑
            JSON Re-import Loop
JSON Export Pipeline
DataFrame Filter → Original Data Sync → JSON Structure Creation → 
Metadata Generation → Format Selection → File Generation → Download
Round-Trip JSON Workflow
Original JSON → Q2LMS Processing → Edit/Filter → JSON Export → 
Version Control → Collaboration → JSON Re-import → Q2LMS
```
3. Module Integration - Update Import Patterns
Add to existing module integration section:
```python
Enhanced import pattern with JSON export support
try:
    from modules.exporter import (
        QuestionExporter, 
        integrate_with_existing_ui,
        export_to_csv,           # Legacy
        export_to_json,          # NEW
        create_qti_package       # Legacy
    )
    EXPORT_SYSTEM_AVAILABLE = True
    JSON_EXPORT_AVAILABLE = True
except ImportError as e:
    st.error(f"Export system unavailable: {e}")
    EXPORT_SYSTEM_AVAILABLE = False
    JSON_EXPORT_AVAILABLE = False
Feature flags update
FEATURE_FLAGS = {
    'advanced_upload': UPLOAD_SYSTEM_AVAILABLE,
    'question_editor': QUESTION_EDITOR_AVAILABLE,
    'export_system': EXPORT_SYSTEM_AVAILABLE,
    'json_export': JSON_EXPORT_AVAILABLE,        # NEW FLAG
    'latex_processor': LATEX_PROCESSOR_AVAILABLE
}
```
4. API Endpoints Section - Add JSON Export Endpoints
Add new section:
```markdown
JSON Export API Endpoints
Export Question Database
```python
def export_questions_json(df: pd.DataFrame, 
                         original_questions: List[Dict[str, Any]],
                         export_config: Dict[str, Any]) -> bytes:
    """
    API endpoint for JSON export functionality
Args:
    df: Filtered question DataFrame
    original_questions: Original question data with LaTeX
    export_config: Export configuration options
        - include_metadata: bool
        - format_style: str ("compact" | "pretty")
        - preserve_ids: bool
        - filename: str

Returns:
    JSON data as bytes for download

Raises:
    ValueError: If export configuration is invalid
    ProcessingError: If question processing fails
"""

```
Metadata Generation API
```python
def generate_export_metadata(questions: List[Dict[str, Any]], 
                           df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive metadata for JSON export
Args:
    questions: Processed question data
    df: Source DataFrame

Returns:
    Metadata dictionary containing:
    - export_statistics
    - question_analytics
    - latex_analysis
    - topic_distribution
    - difficulty_metrics
"""

```
Validation API
```python
def validate_json_export_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate JSON export configuration
Args:
    config: Export configuration dictionary

Returns:
    Tuple of (is_valid, error_messages)
"""


5. Integration Patterns - Add JSON Export Pattern
Add to existing integration patterns:
```markdown
JSON Export Integration Pattern
Standard JSON Export Workflow
```python
In main application
if selected_tab == "Export":
    # Check if JSON export is available
    if FEATURE_FLAGS['json_export']:
        # Render enhanced export interface with JSON option
        from modules.exporter import integrate_with_existing_ui
        integrate_with_existing_ui(st.session_state.df, 
                                 st.session_state.original_questions)
    else:
        # Fallback to legacy export options
        st.warning("JSON export not available - using legacy export")
        legacy_export_interface()
```
Direct JSON Export Usage
```python
Direct usage for custom workflows
from modules.exporter import QuestionExporter
exporter = QuestionExporter()
json_data = exporter._export_json(
    df=filtered_questions_df,
    original_questions=original_question_data,
    filename="course_questions.json",
    include_metadata=True,
    format_style="Pretty (indented)",
    preserve_ids=True
)
```
Batch JSON Export
```python
Export multiple filtered sets
topics = ['Calculus', 'Linear Algebra', 'Numerical Methods']
for topic in topics:
    topic_df = df[df['Topic'] == topic]
    topic_questions = filter_original_questions(original_questions, topic_df)
exporter._export_json(
    df=topic_df,
    original_questions=topic_questions,
    filename=f"{topic.lower().replace(' ', '_')}_questions.json"
)


6. Error Handling - Add JSON Export Error Handling
Add to existing error handling section:
```python
JSON Export Error Handling
class JSONExportError(Exception):
    """Custom exception for JSON export failures"""
    pass
def handle_json_export_errors(func):
    """Decorator for JSON export error handling"""
    def wrapper(args, kwargs):
        try:
            return func(args, **kwargs)
        except JSONExportError as e:
            st.error(f"JSON Export Error: {str(e)}")
            logger.error(f"JSON export failed: {str(e)}", exc_info=True)
        except ValueError as e:
            st.error(f"Invalid export configuration: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error during JSON export: {str(e)}")
            logger.exception("Unexpected JSON export error")
    return wrapper
Usage
@handle_json_export_errors
def export_json_with_error_handling(df, original_questions, config):
    """JSON export with comprehensive error handling"""
    # Export logic here
    pass
```
Summary of API Changes
New Functions Added:

_render_json_export() - JSON export UI
_export_json() - Core JSON export functionality  
_create_export_metadata() - Metadata generation
export_to_json() - Legacy compatibility function

Enhanced Functions:

render_export_interface() - Now includes JSON option
integrate_with_existing_ui() - Enhanced with JSON support

New Configuration Options:

JSON export formatting (compact/pretty)
Metadata inclusion toggle
ID preservation options
Custom filename validation

API Compatibility:

✅ Backward Compatible - All existing API functions unchanged
✅ Progressive Enhancement - New features available when enabled
✅ Graceful Degradation - Fallback to existing functionality if JSON export unavailable
