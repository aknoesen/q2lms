# Q2LMS Developer Documentation

## Table of Contents
1. [Overview](#overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Architecture and Design](#architecture-and-design)
4. [Code Organization](#code-organization)
5. [Core Components](#core-components)
6. [Development Workflows](#development-workflows)
7. [Testing Framework](#testing-framework)
8. [Contributing Guidelines](#contributing-guidelines)
9. [Extension and Customization](#extension-and-customization)
10. [API Development](#api-development)
11. [Performance Considerations](#performance-considerations)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Q2LMS is built as a modular Streamlit application designed for educational question database management and LMS integration. The architecture emphasizes maintainability, extensibility, and performance while providing a clean separation of concerns between UI components, business logic, and data processing.

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python 3.8+
- **Data Processing**: Pandas, JSON handling
- **Export Formats**: QTI XML generation, JSON serialization, CSV export
- **Mathematical Rendering**: LaTeX integration
- **File Processing**: Multi-format upload and conversion utilities

### Design Principles
- **Modularity**: Clear separation between UI, business logic, and utilities
- **Extensibility**: Plugin-style architecture for new question types and export formats
- **Performance**: Efficient handling of large question databases
- **Maintainability**: Clean code structure with comprehensive documentation
- **User Experience**: Streamlined workflows optimized for educational use cases

---

## Development Environment Setup

### Prerequisites
```bash
# System requirements
Python 3.8 or higher
Git for version control
Modern text editor or IDE (VS Code, PyCharm recommended)
```

### Local Development Setup

**1. Repository Setup**
```bash
# Clone the repository
git clone https://github.com/aknoesen/q2lms.git
cd q2lms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**2. Development Dependencies**
```bash
# Install additional development tools
pip install -r requirements-dev.txt  # If available

# Recommended development packages
pip install pytest pytest-cov black flake8 mypy
```

**3. IDE Configuration**
```bash
# VS Code settings (recommended)
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"]
}
```

**4. Run Development Server**
```bash
# Start the application
streamlit run streamlit_app.py

# Development mode with auto-reload
streamlit run streamlit_app.py --server.runOnSave true
```

### Environment Variables
```bash
# Optional configuration
export Q2LMS_DEBUG=true
export Q2LMS_LOG_LEVEL=DEBUG
export Q2LMS_DATA_PATH=./data
```

---

## Architecture and Design

### High-Level Architecture

```
Q2LMS Application Architecture

┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │   Upload    │ │  Question   │ │   Export    │ │Analytics││
│  │ Interface   │ │   Editor    │ │   Center    │ │Dashboard││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │   Upload    │ │  Question   │ │   Export    │ │Analytics││
│  │  Processor  │ │  Manager    │ │  Generator  │ │Engine  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data and Utilities Layer                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │    JSON     │ │    LaTeX    │ │    File     │ │Validation││
│  │   Handler   │ │  Processor  │ │   Manager   │ │ Utils  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

**Question Creation Flow**:
1. User input via Streamlit interface
2. Data validation and sanitization
3. LaTeX processing and optimization
4. Question object creation and storage
5. Database update and session management

**Export Processing Flow**:
1. Question selection and filtering
2. Format-specific preprocessing
3. Template application and rendering
4. Package generation and validation
5. Download preparation and delivery

### Session Management
Q2LMS uses Streamlit's session state for managing:
- Active question database
- User preferences and settings
- Upload progress and status
- Export configurations
- Temporary data storage

---

## Code Organization

### Directory Structure
```
q2lms/
├── streamlit_app.py              # Main application entry point
├── modules/                      # Core functionality modules
│   ├── upload_interface_v2.py    # File upload and processing
│   ├── question_editor.py        # Question editing interface
│   ├── export/                   # Export system modules
│   │   ├── qti_generator.py      # Canvas QTI package generation
│   │   ├── json_exporter.py      # Native JSON export
│   │   ├── csv_exporter.py       # CSV data export
│   │   └── export_base.py        # Base export functionality
│   ├── analytics/                # Analytics and reporting
│   │   ├── dashboard.py          # Analytics dashboard
│   │   └── metrics.py            # Performance metrics
│   └── ui_components/            # Reusable UI components
│       ├── question_display.py   # Question rendering
│       ├── latex_preview.py      # LaTeX preview widget
│       └── file_upload.py        # Upload interface components
├── utilities/                    # Helper functions and utilities
│   ├── json_handler.py           # JSON processing utilities
│   ├── latex_processor.py        # LaTeX processing and validation
│   ├── file_manager.py           # File operation utilities
│   ├── validation.py             # Data validation functions
│   └── config.py                 # Configuration management
├── examples/                     # Sample data and templates
│   ├── sample_questions.json     # Example question database
│   ├── templates/                # Export templates
│   └── test_data/                # Test datasets
├── tests/                        # Test suite
│   ├── test_upload.py            # Upload functionality tests
│   ├── test_export.py            # Export system tests
│   ├── test_questions.py         # Question management tests
│   └── fixtures/                 # Test data fixtures
├── docs/                         # Documentation
│   ├── API.md                    # API reference
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── USERGUIDE.md              # User documentation
│   └── DEVELOPER.md              # This document
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── README.md                     # Project overview
└── LICENSE                       # MIT License
```

### Import Conventions
```python
# Standard library imports
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Third-party imports
import streamlit as st
import pandas as pd

# Local imports
from utilities.json_handler import JsonHandler
from modules.export.qti_generator import QTIGenerator
```

---

## Core Components

### 1. Question Data Model

**Question Structure**:
```python
class Question:
    """
    Core question data model
    
    Attributes:
        id (str): Unique question identifier
        type (str): Question type (multiple_choice, true_false, short_answer, essay)
        text (str): Question content with LaTeX support
        answers (List[Answer]): List of answer options
        metadata (Dict): Additional question metadata
        created_at (datetime): Creation timestamp
        modified_at (datetime): Last modification timestamp
    """
    
    def __init__(self, question_data: Dict):
        self.id = question_data.get('id', self._generate_id())
        self.type = question_data.get('type', 'multiple_choice')
        self.text = question_data.get('text', '')
        self.answers = [Answer(ans) for ans in question_data.get('answers', [])]
        self.metadata = question_data.get('metadata', {})
        self.created_at = question_data.get('created_at')
        self.modified_at = question_data.get('modified_at')
    
    def to_dict(self) -> Dict:
        """Convert question to dictionary format"""
        return {
            'id': self.id,
            'type': self.type,
            'text': self.text,
            'answers': [ans.to_dict() for ans in self.answers],
            'metadata': self.metadata,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }
    
    def validate(self) -> List[str]:
        """Validate question data and return list of errors"""
        errors = []
        if not self.text.strip():
            errors.append("Question text cannot be empty")
        if not self.answers:
            errors.append("Question must have at least one answer")
        return errors
```

### 2. Upload Processing System

**Upload Handler Architecture**:
```python
class UploadProcessor:
    """
    Handles file upload and processing for multiple formats
    """
    
    def __init__(self):
        self.supported_formats = ['.json', '.csv', '.zip']
        self.processors = {
            '.json': self._process_json,
            '.csv': self._process_csv,
            '.zip': self._process_qti_zip
        }
    
    def process_upload(self, uploaded_file) -> Dict:
        """
        Process uploaded file and return question data
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Dict containing processed questions and metadata
        """
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise UnsupportedFormatError(f"Format {file_extension} not supported")
        
        processor = self.processors[file_extension]
        return processor(uploaded_file)
    
    def _process_json(self, file) -> Dict:
        """Process JSON question file"""
        try:
            data = json.load(file)
            questions = [Question(q) for q in data.get('questions', [])]
            return {
                'questions': questions,
                'metadata': data.get('metadata', {}),
                'format': 'json'
            }
        except json.JSONDecodeError as e:
            raise ProcessingError(f"Invalid JSON format: {e}")
```

### 3. Export System Architecture

**Base Export Interface**:
```python
from abc import ABC, abstractmethod

class ExportBase(ABC):
    """
    Abstract base class for all export formats
    """
    
    @abstractmethod
    def export(self, questions: List[Question], options: Dict) -> bytes:
        """
        Export questions to target format
        
        Args:
            questions: List of Question objects
            options: Export configuration options
            
        Returns:
            Exported data as bytes
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Return appropriate file extension for this format"""
        pass
    
    @abstractmethod
    def validate_questions(self, questions: List[Question]) -> List[str]:
        """Validate questions for this export format"""
        pass

class QTIExporter(ExportBase):
    """Canvas QTI package exporter"""
    
    def export(self, questions: List[Question], options: Dict) -> bytes:
        """Generate QTI package"""
        qti_xml = self._generate_qti_xml(questions, options)
        manifest = self._generate_manifest(questions)
        
        # Create ZIP package
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('assessment.xml', qti_xml)
            zip_file.writestr('imsmanifest.xml', manifest)
        
        return zip_buffer.getvalue()
```

### 4. LaTeX Processing Engine

**LaTeX Handler**:
```python
class LaTeXProcessor:
    """
    Handles LaTeX processing and optimization for web display
    """
    
    def __init__(self):
        self.math_patterns = [
            (r'\$\$(.+?)\$\$', r'\\[\1\\]'),  # Display math
            (r'\$(.+?)\$', r'\\(\1\\)')       # Inline math
        ]
    
    def process_text(self, text: str) -> str:
        """
        Process text containing LaTeX expressions
        
        Args:
            text: Raw text with LaTeX notation
            
        Returns:
            Processed text optimized for web display
        """
        processed = text
        
        # Apply mathematical notation conversions
        for pattern, replacement in self.math_patterns:
            processed = re.sub(pattern, replacement, processed, flags=re.DOTALL)
        
        # Optimize common LaTeX commands
        processed = self._optimize_commands(processed)
        
        # Validate LaTeX syntax
        errors = self._validate_latex(processed)
        if errors:
            raise LaTeXError(f"LaTeX validation failed: {errors}")
        
        return processed
    
    def _validate_latex(self, text: str) -> List[str]:
        """Validate LaTeX syntax and return errors"""
        errors = []
        
        # Check for unmatched braces
        brace_count = text.count('{') - text.count('}')
        if brace_count != 0:
            errors.append(f"Unmatched braces: {brace_count}")
        
        # Check for unmatched math delimiters
        inline_count = text.count('\\(') - text.count('\\)')
        if inline_count != 0:
            errors.append(f"Unmatched inline math delimiters: {inline_count}")
        
        return errors
```

---

## Development Workflows

### Feature Development Process

**1. Branch Strategy**
```bash
# Create feature branch
git checkout -b feature/new-export-format

# Development workflow
git add .
git commit -m "feat: Add new export format support"
git push origin feature/new-export-format

# Create pull request for review
```

**2. Code Quality Checks**
```bash
# Run linting
flake8 modules/ utilities/ tests/

# Format code
black modules/ utilities/ tests/

# Type checking
mypy modules/ utilities/

# Run tests
pytest tests/ -v --cov=modules --cov=utilities
```

**3. Development Testing**
```bash
# Unit tests
pytest tests/test_specific_module.py -v

# Integration tests
pytest tests/test_integration.py -v

# End-to-end testing
streamlit run streamlit_app.py
# Manual testing of UI workflows
```

### Adding New Question Types

**Step 1: Define Question Type**
```python
# In utilities/question_types.py
class ShortAnswerQuestion(Question):
    """Short answer question implementation"""
    
    def __init__(self, question_data: Dict):
        super().__init__(question_data)
        self.case_sensitive = question_data.get('case_sensitive', False)
        self.acceptable_answers = question_data.get('acceptable_answers', [])
    
    def validate(self) -> List[str]:
        """Validate short answer specific requirements"""
        errors = super().validate()
        if not self.acceptable_answers:
            errors.append("Short answer questions must have acceptable answers")
        return errors
```

**Step 2: Update UI Components**
```python
# In modules/question_editor.py
def render_short_answer_editor(question: ShortAnswerQuestion):
    """Render UI for short answer question editing"""
    
    with st.container():
        question.text = st.text_area("Question Text", value=question.text)
        
        st.subheader("Acceptable Answers")
        for i, answer in enumerate(question.acceptable_answers):
            cols = st.columns([4, 1])
            with cols[0]:
                question.acceptable_answers[i] = st.text_input(f"Answer {i+1}", value=answer)
            with cols[1]:
                if st.button("Remove", key=f"remove_{i}"):
                    question.acceptable_answers.pop(i)
                    st.rerun()
        
        if st.button("Add Answer"):
            question.acceptable_answers.append("")
            st.rerun()
```

**Step 3: Update Export Handlers**
```python
# In modules/export/qti_generator.py
def _generate_short_answer_qti(self, question: ShortAnswerQuestion) -> str:
    """Generate QTI XML for short answer questions"""
    
    template = """
    <assessmentItem identifier="{id}" title="{title}">
        <responseDeclaration identifier="RESPONSE" cardinality="single" baseType="string">
            {acceptable_answers}
        </responseDeclaration>
        <itemBody>
            <p>{question_text}</p>
            <extendedTextInteraction responseIdentifier="RESPONSE"/>
        </itemBody>
    </assessmentItem>
    """
    
    acceptable_answers_xml = "\n".join([
        f'<correctResponse><value>{answer}</value></correctResponse>'
        for answer in question.acceptable_answers
    ])
    
    return template.format(
        id=question.id,
        title=question.text[:50],
        question_text=question.text,
        acceptable_answers=acceptable_answers_xml
    )
```

### Adding New Export Formats

**Step 1: Create Export Class**
```python
# In modules/export/new_format_exporter.py
class NewFormatExporter(ExportBase):
    """Exporter for new target format"""
    
    def export(self, questions: List[Question], options: Dict) -> bytes:
        """Export to new format"""
        # Implementation specific to new format
        pass
    
    def get_file_extension(self) -> str:
        return ".newformat"
    
    def validate_questions(self, questions: List[Question]) -> List[str]:
        """Validate questions for new format requirements"""
        errors = []
        for question in questions:
            # Format-specific validation
            pass
        return errors
```

**Step 2: Register Export Format**
```python
# In modules/export/__init__.py
from .new_format_exporter import NewFormatExporter

AVAILABLE_EXPORTERS = {
    'qti': QTIExporter,
    'json': JSONExporter,
    'csv': CSVExporter,
    'newformat': NewFormatExporter  # Add new exporter
}
```

---

## Testing Framework

### Test Structure
```
tests/
├── conftest.py                   # Pytest configuration and fixtures
├── test_upload.py                # Upload system tests
├── test_export.py                # Export system tests
├── test_questions.py             # Question management tests
├── test_latex.py                 # LaTeX processing tests
├── test_integration.py           # Integration tests
├── fixtures/                     # Test data
│   ├── sample_questions.json     # Sample question data
│   ├── invalid_json.json         # Invalid data for error testing
│   └── qti_package.zip           # Sample QTI package
└── utils/                        # Test utilities
    └── test_helpers.py            # Common test functions
```

### Example Test Implementation
```python
# tests/test_questions.py
import pytest
from modules.question_manager import QuestionManager
from utilities.question_types import Question

class TestQuestionManager:
    """Test suite for question management functionality"""
    
    @pytest.fixture
    def question_manager(self):
        """Create QuestionManager instance for testing"""
        return QuestionManager()
    
    @pytest.fixture
    def sample_question(self):
        """Create sample question for testing"""
        return Question({
            'id': 'test-001',
            'type': 'multiple_choice',
            'text': 'What is 2 + 2?',
            'answers': [
                {'text': '3', 'correct': False},
                {'text': '4', 'correct': True},
                {'text': '5', 'correct': False}
            ]
        })
    
    def test_add_question(self, question_manager, sample_question):
        """Test adding a question to the database"""
        question_manager.add_question(sample_question)
        
        assert len(question_manager.questions) == 1
        assert question_manager.get_question('test-001') == sample_question
    
    def test_question_validation(self, sample_question):
        """Test question validation"""
        # Valid question should pass
        errors = sample_question.validate()
        assert len(errors) == 0
        
        # Invalid question should fail
        sample_question.text = ""
        errors = sample_question.validate()
        assert "Question text cannot be empty" in errors
    
    @pytest.mark.parametrize("question_type,expected_fields", [
        ("multiple_choice", ["answers"]),
        ("true_false", ["correct_answer"]),
        ("short_answer", ["acceptable_answers"]),
    ])
    def test_question_type_requirements(self, question_type, expected_fields):
        """Test that different question types have required fields"""
        question_data = {'type': question_type, 'text': 'Test question'}
        question = Question(question_data)
        
        for field in expected_fields:
            assert hasattr(question, field)
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov=utilities --cov-report=html

# Run specific test file
pytest tests/test_questions.py -v

# Run tests matching pattern
pytest -k "test_question" -v

# Run tests with specific markers
pytest -m "integration" -v
```

---

## Contributing Guidelines

### Code Style Standards

**Python Style Guide**:
- Follow PEP 8 conventions
- Use Black for code formatting (line length: 88)
- Use type hints for function signatures
- Document all public functions and classes
- Use meaningful variable and function names

**Example Code Style**:
```python
from typing import Dict, List, Optional

def process_questions(
    questions: List[Dict], 
    options: Optional[Dict] = None
) -> List[Question]:
    """
    Process raw question data into Question objects.
    
    Args:
        questions: List of question dictionaries
        options: Optional processing configuration
        
    Returns:
        List of validated Question objects
        
    Raises:
        ValidationError: If question data is invalid
    """
    if options is None:
        options = {}
    
    processed_questions = []
    for question_data in questions:
        question = Question(question_data)
        
        # Validate question
        errors = question.validate()
        if errors:
            raise ValidationError(f"Invalid question {question.id}: {errors}")
        
        processed_questions.append(question)
    
    return processed_questions
```

### Documentation Standards

**Docstring Format**:
```python
def export_questions(
    questions: List[Question], 
    format_type: str, 
    options: Dict
) -> bytes:
    """
    Export questions to specified format.
    
    This function handles the export of question databases to various
    formats including QTI packages, JSON, and CSV files.
    
    Args:
        questions: List of Question objects to export
        format_type: Target export format ('qti', 'json', 'csv')
        options: Export configuration dictionary containing:
            - include_metadata (bool): Include question metadata
            - randomize_answers (bool): Randomize answer order
            - package_name (str): Name for export package
    
    Returns:
        Exported data as bytes ready for download
    
    Raises:
        UnsupportedFormatError: If format_type is not supported
        ExportError: If export process fails
    
    Example:
        >>> questions = [Question(data) for data in question_list]
        >>> options = {'include_metadata': True, 'package_name': 'quiz1'}
        >>> exported_data = export_questions(questions, 'qti', options)
    """
```

### Pull Request Process

**1. Pre-submission Checklist**:
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New features include tests
- [ ] Documentation updated
- [ ] Commit messages follow convention

**2. Commit Message Format**:
```
type(scope): brief description

Detailed explanation of changes if needed

- List specific changes
- Reference issue numbers: Fixes #123
- Include breaking changes: BREAKING CHANGE: details
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**3. Review Process**:
- Automated checks must pass
- Code review by maintainer required
- Integration tests in CI/CD pipeline
- Documentation review for user-facing changes

---

## Extension and Customization

### Plugin Architecture

**Creating Custom Question Types**:
```python
# custom_plugins/my_question_type.py
from utilities.question_types import Question
from typing import Dict, List

class CustomQuestionType(Question):
    """Custom question type implementation"""
    
    question_type = "custom_type"
    
    def __init__(self, question_data: Dict):
        super().__init__(question_data)
        self.custom_field = question_data.get('custom_field', '')
    
    def validate(self) -> List[str]:
        """Custom validation logic"""
        errors = super().validate()
        
        # Add custom validation
        if not self.custom_field:
            errors.append("Custom field is required")
        
        return errors
    
    def render_editor(self):
        """Custom UI rendering"""
        import streamlit as st
        
        self.text = st.text_area("Question Text", value=self.text)
        self.custom_field = st.text_input("Custom Field", value=self.custom_field)
```

**Registering Custom Types**:
```python
# In your application initialization
from custom_plugins.my_question_type import CustomQuestionType
from modules.question_manager import QuestionManager

# Register custom question type
QuestionManager.register_question_type(CustomQuestionType)
```

### Configuration Management

**Custom Configuration**:
```python
# utilities/config.py
import os
from typing import Dict, Any

class Config:
    """Application configuration management"""
    
    def __init__(self):
        self.settings = self._load_default_settings()
        self._load_environment_overrides()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default configuration settings"""
        return {
            'max_upload_size': 50 * 1024 * 1024,  # 50MB
            'supported_formats': ['.json', '.csv', '.zip'],
            'latex_timeout': 30,  # seconds
            'export_batch_size': 100,
            'debug_mode': False,
            'custom_plugins_dir': './custom_plugins'
        }
    
    def _load_environment_overrides(self):
        """Override settings from environment variables"""
        env_mappings = {
            'Q2LMS_MAX_UPLOAD_SIZE': ('max_upload_size', int),
            'Q2LMS_DEBUG': ('debug_mode', bool),
            'Q2LMS_PLUGINS_DIR': ('custom_plugins_dir', str)
        }
        
        for env_var, (setting_key, type_converter) in env_mappings.items():
            if env_var in os.environ:
                self.settings[setting_key] = type_converter(os.environ[env_var])
```

### API Extensions

**Custom API Endpoints**:
```python
# extensions/api_extensions.py
from typing import Dict, List
from modules.question_manager import QuestionManager
from utilities.json_handler import JsonHandler

class APIExtensions:
    """Extended API functionality"""
    
    def __init__(self, question_manager: QuestionManager):
        self.question_manager = question_manager
        self.json_handler = JsonHandler()
    
    def bulk_import_questions(self, file_paths: List[str]) -> Dict:
        """
        Import questions from multiple files
        
        Args:
            file_paths: List of file paths to import
            
        Returns:
            Import summary with statistics
        """
        import_stats = {
            'total_files': len(file_paths),
            'successful_imports': 0,
            'failed_imports': 0,
            'total_questions': 0,
            'errors': []
        }
        
        for file_path in file_paths:
            try:
                questions_data = self.json_handler.load_file(file_path)
                questions = [Question(q) for q in questions_data['questions']]
                
                # Validate and add questions
                for question in questions:
                    errors = question.validate()
                    if not errors:
                        self.question_manager.add_question(question)
                        import_stats['total_questions'] += 1
                    else:
                        import_stats['errors'].append(f"Question {question.id}: {errors}")
                
                import_stats['successful_imports'] += 1
                
            except Exception as e:
                import_stats['failed_imports'] += 1
                import_stats['errors'].append(f"File {file_path}: {str(e)}")
        
        return import_stats
```

---

## API Development

### Internal API Structure

**Core API Classes**:
```python
# modules/api/question_api.py
from typing import Dict, List, Optional
from utilities.question_types import Question

class QuestionAPI:
    """Internal API for question operations"""
    
    def __init__(self, question_manager):
        self.question_manager = question_manager
    
    def create_question(self, question_data: Dict) -> str:
        """
        Create new question
        
        Args:
            question_data: Question definition dictionary
            
        Returns:
            Created question ID
        """
        question = Question(question_data)
        errors = question.validate()
        
        if errors:
            raise ValueError(f"Question validation failed: {errors}")
        
        return self.question_manager.add_question(question)
    
    def update_question(self, question_id: str, updates: Dict) -> bool:
        """
        Update existing question
        
        Args:
            question_id: ID of question to update
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        question = self.question_manager.get_question(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(question, field):
                setattr(question, field, value)
        
        # Validate updated question
        errors = question.validate()
        if errors:
            raise ValueError(f"Updated question validation failed: {errors}")
        
        return self.question_manager.update_question(question)
    
    def delete_question(self, question_id: str) -> bool:
        """Delete question by ID"""
        return self.question_manager.delete_question(question_id)
    
    def search_questions(self, query: str, filters: Optional[Dict] = None) -> List[Question]:
        """
        Search questions with optional filters
        
        Args:
            query: Search text
            filters: Optional filters (type, difficulty, author, etc.)
            
        Returns:
            List of matching questions
        """
        return self.question_manager.search(query, filters or {})
    
    def get_question_statistics(self) -> Dict:
        """Get database statistics"""
        questions = self.question_manager.get_all_questions()
        
        stats = {
            'total_questions': len(questions),
            'by_type': {},
            'by_difficulty': {},
            'creation_timeline': {}
        }
        
        for question in questions:
            # Count by type
            q_type = question.type
            stats['by_type'][q_type] = stats['by_type'].get(q_type, 0) + 1
            
            # Count by difficulty
            difficulty = question.metadata.get('difficulty', 'unknown')
            stats['by_difficulty'][difficulty] = stats['by_difficulty'].get(difficulty, 0) + 1
        
        return stats
```

### REST API Interface (Optional)

**FastAPI Integration**:
```python
# api/rest_endpoints.py (if implementing REST API)
from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List, Dict, Optional
from pydantic import BaseModel
from modules.api.question_api import QuestionAPI

app = FastAPI(title="Q2LMS API", version="1.0.0")

class QuestionCreate(BaseModel):
    type: str
    text: str
    answers: List[Dict]
    metadata: Optional[Dict] = {}

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    answers: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None

@app.post("/questions/", response_model=Dict)
async def create_question(question: QuestionCreate):
    """Create a new question"""
    try:
        question_id = question_api.create_question(question.dict())
        return {"id": question_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/questions/{question_id}")
async def get_question(question_id: str):
    """Get question by ID"""
    question = question_api.question_manager.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question.to_dict()

@app.put("/questions/{question_id}")
async def update_question(question_id: str, updates: QuestionUpdate):
    """Update existing question"""
    try:
        success = question_api.update_question(question_id, updates.dict(exclude_unset=True))
        if success:
            return {"status": "updated"}
        else:
            raise HTTPException(status_code=400, detail="Update failed")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/questions/{question_id}")
async def delete_question(question_id: str):
    """Delete question"""
    success = question_api.delete_question(question_id)
    if success:
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="Question not found")
```

---

## Performance Considerations

### Memory Management

**Large Dataset Handling**:
```python
# utilities/performance.py
import gc
from typing import Iterator, List
from modules.question_manager import Question

class BatchProcessor:
    """Handle large datasets efficiently"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    def process_questions_in_batches(
        self, 
        questions: List[Question], 
        processor_func
    ) -> Iterator:
        """
        Process questions in batches to manage memory usage
        
        Args:
            questions: List of questions to process
            processor_func: Function to apply to each batch
            
        Yields:
            Results from each batch
        """
        for i in range(0, len(questions), self.batch_size):
            batch = questions[i:i + self.batch_size]
            
            try:
                result = processor_func(batch)
                yield result
            except Exception as e:
                print(f"Error processing batch {i//self.batch_size}: {e}")
                continue
            finally:
                # Force garbage collection after each batch
                gc.collect()

class LazyQuestionLoader:
    """Load questions on-demand to reduce memory usage"""
    
    def __init__(self, data_source: str):
        self.data_source = data_source
        self._question_cache = {}
        self._question_index = self._build_index()
    
    def _build_index(self) -> Dict[str, int]:
        """Build index of question IDs to file positions"""
        # Implementation depends on data source format
        pass
    
    def get_question(self, question_id: str) -> Question:
        """Load question on-demand"""
        if question_id in self._question_cache:
            return self._question_cache[question_id]
        
        # Load from data source
        question_data = self._load_question_from_source(question_id)
        question = Question(question_data)
        
        # Cache with LRU eviction
        if len(self._question_cache) > 1000:  # Max cache size
            oldest_id = next(iter(self._question_cache))
            del self._question_cache[oldest_id]
        
        self._question_cache[question_id] = question
        return question
```

### Caching Strategies

**Session State Optimization**:
```python
# utilities/cache_manager.py
import streamlit as st
from typing import Any, Dict, Optional
from functools import wraps
import hashlib
import pickle

class CacheManager:
    """Manage Streamlit session state caching"""
    
    @staticmethod
    def cache_result(key: str, ttl: int = 3600):
        """
        Decorator to cache function results in session state
        
        Args:
            key: Cache key prefix
            ttl: Time to live in seconds
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_key = f"{key}_{CacheManager._hash_args(args, kwargs)}"
                
                # Check if cached result exists and is valid
                if cache_key in st.session_state:
                    cached_data = st.session_state[cache_key]
                    if CacheManager._is_cache_valid(cached_data, ttl):
                        return cached_data['result']
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                st.session_state[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def _hash_args(args, kwargs) -> str:
        """Generate hash from function arguments"""
        combined = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(combined.encode()).hexdigest()
    
    @staticmethod
    def _is_cache_valid(cached_data: Dict, ttl: int) -> bool:
        """Check if cached data is still valid"""
        import time
        return (time.time() - cached_data['timestamp']) < ttl

# Usage example
@CacheManager.cache_result("question_search", ttl=1800)
def search_questions_cached(query: str, filters: Dict) -> List[Question]:
    """Cached question search function"""
    return expensive_search_operation(query, filters)
```

### Database Optimization

**Efficient Data Structures**:
```python
# utilities/data_structures.py
from typing import Dict, List, Set
import bisect
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QuestionIndex:
    """Optimized question indexing for fast searches"""
    
    def __init__(self):
        self.by_id: Dict[str, Question] = {}
        self.by_type: Dict[str, Set[str]] = {}
        self.by_difficulty: Dict[str, Set[str]] = {}
        self.by_creation_date: List[tuple] = []  # (timestamp, question_id)
        self.text_index: Dict[str, Set[str]] = {}  # Simple text indexing
    
    def add_question(self, question: Question):
        """Add question to all indexes"""
        self.by_id[question.id] = question
        
        # Type index
        if question.type not in self.by_type:
            self.by_type[question.type] = set()
        self.by_type[question.type].add(question.id)
        
        # Difficulty index
        difficulty = question.metadata.get('difficulty', 'unknown')
        if difficulty not in self.by_difficulty:
            self.by_difficulty[difficulty] = set()
        self.by_difficulty[difficulty].add(question.id)
        
        # Date index (sorted for range queries)
        created_at = question.created_at or datetime.now()
        bisect.insort(self.by_creation_date, (created_at.timestamp(), question.id))
        
        # Text index (simple word-based)
        words = question.text.lower().split()
        for word in words:
            if word not in self.text_index:
                self.text_index[word] = set()
            self.text_index[word].add(question.id)
    
    def search(self, query: str, filters: Dict = None) -> Set[str]:
        """Fast question search using indexes"""
        result_ids = set()
        
        if query:
            # Text search
            query_words = query.lower().split()
            for word in query_words:
                if word in self.text_index:
                    if not result_ids:
                        result_ids = self.text_index[word].copy()
                    else:
                        result_ids &= self.text_index[word]
        else:
            # No text query, start with all questions
            result_ids = set(self.by_id.keys())
        
        # Apply filters
        if filters:
            if 'type' in filters:
                type_ids = self.by_type.get(filters['type'], set())
                result_ids &= type_ids
            
            if 'difficulty' in filters:
                diff_ids = self.by_difficulty.get(filters['difficulty'], set())
                result_ids &= diff_ids
        
        return result_ids
```

---

## Troubleshooting

### Common Development Issues

**1. Streamlit Session State Issues**
```python
# Problem: Session state not persisting between reruns
# Solution: Proper session state initialization

def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'questions': [],
        'current_question': None,
        'upload_status': None,
        'export_settings': {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Call at the beginning of your Streamlit app
if __name__ == "__main__":
    initialize_session_state()
```

**2. LaTeX Rendering Problems**
```python
# Problem: LaTeX not rendering correctly
# Solution: Proper escaping and validation

def debug_latex_rendering(text: str) -> Dict:
    """Debug LaTeX rendering issues"""
    import re
    
    debug_info = {
        'original_text': text,
        'math_expressions': [],
        'potential_issues': []
    }
    
    # Find all math expressions
    math_patterns = [
        (r'\$\$(.+?)\$\, 'display_math'),
        (r'\$(.+?)\, 'inline_math'),
        (r'\\begin\{(.+?)\}(.+?)\\end\{\1\}', 'environment')
    ]
    
    for pattern, math_type in math_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        debug_info['math_expressions'].extend([
            {'type': math_type, 'content': match} for match in matches
        ])
    
    # Check for common issues
    if text.count('{') != text.count('}'):
        debug_info['potential_issues'].append('Unmatched braces')
    
    if text.count(') % 2 != 0:
        debug_info['potential_issues'].append('Unmatched dollar signs')
    
    return debug_info
```

**3. File Upload Problems**
```python
# Problem: File upload failing silently
# Solution: Comprehensive error handling

def debug_file_upload(uploaded_file) -> Dict:
    """Debug file upload issues"""
    debug_info = {
        'filename': uploaded_file.name if uploaded_file else 'None',
        'file_size': 0,
        'file_type': 'Unknown',
        'is_valid': False,
        'errors': []
    }
    
    try:
        if uploaded_file is None:
            debug_info['errors'].append('No file uploaded')
            return debug_info
        
        # Check file size
        debug_info['file_size'] = uploaded_file.size
        if uploaded_file.size == 0:
            debug_info['errors'].append('File is empty')
        
        # Check file type
        debug_info['file_type'] = uploaded_file.type
        
        # Try to read file content
        content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        if len(content) == 0:
            debug_info['errors'].append('File content is empty')
        
        # Validate JSON if applicable
        if uploaded_file.name.endswith('.json'):
            try:
                import json
                json.loads(content.decode('utf-8'))
                debug_info['is_valid'] = True
            except json.JSONDecodeError as e:
                debug_info['errors'].append(f'Invalid JSON: {e}')
        
    except Exception as e:
        debug_info['errors'].append(f'Unexpected error: {e}')
    
    return debug_info
```

### Performance Debugging

**Memory Usage Monitoring**:
```python
# utilities/performance_monitor.py
import psutil
import time
from typing import Dict, List
from functools import wraps

class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = []
        self.process = psutil.Process()
    
    def measure_performance(self, operation_name: str):
        """Decorator to measure function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                    
                    metric = {
                        'operation': operation_name,
                        'duration': end_time - start_time,
                        'memory_start': start_memory,
                        'memory_end': end_memory,
                        'memory_delta': end_memory - start_memory,
                        'success': success,
                        'error': error,
                        'timestamp': time.time()
                    }
                    
                    self.metrics.append(metric)
                
                return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        if not self.metrics:
            return {'message': 'No performance data available'}
        
        operations = {}
        for metric in self.metrics:
            op_name = metric['operation']
            if op_name not in operations:
                operations[op_name] = []
            operations[op_name].append(metric)
        
        report = {}
        for op_name, op_metrics in operations.items():
            durations = [m['duration'] for m in op_metrics if m['success']]
            memory_deltas = [m['memory_delta'] for m in op_metrics if m['success']]
            
            report[op_name] = {
                'call_count': len(op_metrics),
                'success_rate': sum(1 for m in op_metrics if m['success']) / len(op_metrics),
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'avg_memory_delta': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
                'max_memory_delta': max(memory_deltas) if memory_deltas else 0
            }
        
        return report

# Usage example
monitor = PerformanceMonitor()

@monitor.measure_performance("question_export")
def export_questions(questions, format_type):
    # Export implementation
    pass
```

### Debugging Utilities

**Debug Configuration**:
```python
# utilities/debug_utils.py
import logging
import streamlit as st
from typing import Any, Dict

class DebugUtils:
    """Debugging utilities for development"""
    
    @staticmethod
    def setup_logging(level: str = "INFO"):
        """Setup application logging"""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('q2lms_debug.log'),
                logging.StreamHandler()
            ]
        )
    
    @staticmethod
    def debug_session_state():
        """Display current session state for debugging"""
        if st.checkbox("Show Debug Info"):
            st.subheader("Session State Debug")
            
            for key, value in st.session_state.items():
                with st.expander(f"Session Key: {key}"):
                    st.write(f"Type: {type(value)}")
                    st.write(f"Value: {value}")
    
    @staticmethod
    def log_function_call(func_name: str, args: tuple, kwargs: Dict):
        """Log function calls for debugging"""
        logger = logging.getLogger(__name__)
        logger.debug(f"Function: {func_name}")
        logger.debug(f"Args: {args}")
        logger.debug(f"Kwargs: {kwargs}")
    
    @staticmethod
    def validate_question_data(question_data: Dict) -> Dict:
        """Validate and debug question data structure"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'structure_analysis': {}
        }
        
        required_fields = ['id', 'type', 'text']
        for field in required_fields:
            if field not in question_data:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Analyze structure
        validation_result['structure_analysis'] = {
            'field_count': len(question_data),
            'has_answers': 'answers' in question_data,
            'has_metadata': 'metadata' in question_data,
            'answer_count': len(question_data.get('answers', []))
        }
        
        return validation_result
```

---

## Conclusion

This Developer Documentation provides comprehensive guidance for contributing to and extending Q2LMS. The modular architecture, clear coding standards, and extensive testing framework ensure that the codebase remains maintainable and extensible as the project grows.

### Key Development Practices
- **Modular Design**: Clear separation of concerns between UI, business logic, and utilities
- **Comprehensive Testing**: Unit tests, integration tests, and performance monitoring
- **Code Quality**: Consistent style, type hints, and documentation standards
- **Extensibility**: Plugin architecture for custom question types and export formats
- **Performance**: Efficient handling of large datasets and memory management

### Next Steps for Developers
1. **Setup**: Follow the development environment setup instructions
2. **Explore**: Review the codebase structure and core components
3. **Contribute**: Use the established workflows for feature development
4. **Extend**: Leverage the plugin architecture for custom functionality
5. **Test**: Ensure all contributions include appropriate tests
6. **Document**: Update documentation for any new features or changes

### Resources
- **Repository**: https://github.com/aknoesen/q2lms
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for community support
- **Documentation**: Complete guides in the `/docs` directory

For questions or support during development, consult the project's GitHub repository and community forums.

---

*This developer documentation is maintained as part of the Q2LMS project. For the most current version, visit the project repository.*