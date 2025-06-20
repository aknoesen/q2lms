# Upload Interface Architecture Design
## Version 2.0 - Clean System Architecture

---

## 🏛️ **Overall System Architecture**

### **Module Structure**
```
question-database-manager/
├── modules/
│   ├── upload_interface_v2.py      # 🆕 New main upload interface
│   ├── file_processor.py           # 🆕 File validation & parsing
│   ├── database_merger.py          # 🆕 Append & merge operations
│   ├── upload_state_manager.py     # 🆕 State management for uploads
│   ├── upload_handler.py           # 📦 Keep as backup/reference
│   ├── session_manager.py          # ✅ Existing - integrate with
│   ├── database_processor.py       # ✅ Existing - enhance
│   └── question_editor.py          # ✅ Existing - integrate with
├── streamlit_app.py                # 🔧 Update imports
└── utilities/                      # ✅ Existing backend utilities
```

### **Responsibility Separation**
- **upload_interface_v2.py**: UI presentation layer only
- **file_processor.py**: File I/O, validation, format detection
- **database_merger.py**: Business logic for combining databases
- **upload_state_manager.py**: State transitions and session management

---

## 🎭 **State Management Architecture**

### **State Definitions**
```python
class UploadState(Enum):
    NO_DATABASE = "no_database"
    DATABASE_LOADED = "database_loaded"
    PROCESSING_FILES = "processing_files"
    PREVIEW_MERGE = "preview_merge"
    ERROR_STATE = "error_state"
    SUCCESS_STATE = "success_state"
```

### **State Transitions**
```
NO_DATABASE
    ├── Upload Single File → PROCESSING_FILES → DATABASE_LOADED
    ├── Upload Multiple Files → PROCESSING_FILES → PREVIEW_MERGE → DATABASE_LOADED
    └── Invalid File → ERROR_STATE → NO_DATABASE

DATABASE_LOADED
    ├── Replace → PROCESSING_FILES → DATABASE_LOADED
    ├── Append → PROCESSING_FILES → PREVIEW_MERGE → DATABASE_LOADED
    ├── Clear → NO_DATABASE
    └── Error → ERROR_STATE → DATABASE_LOADED (rollback)
```

### **Session State Schema**
```python
st.session_state = {
    # Core database state
    'upload_state': UploadState.NO_DATABASE,
    'df': None,  # Current database DataFrame
    'original_questions': [],
    'metadata': {},
    'current_filename': '',
    
    # Upload operation state
    'uploaded_files': [],
    'processing_results': {},
    'preview_data': {},
    'last_operation': '',
    
    # History and rollback
    'database_history': [],
    'can_rollback': False,
    
    # UI state
    'show_advanced_options': False,
    'selected_operation': None,
    'error_message': '',
    'success_message': ''
}
```

---

## 🖥️ **Interface Architecture**

### **Component Hierarchy**
```
UploadInterface
├── StatusHeader
│   ├── DatabaseStatusIndicator
│   ├── QuickStats
│   └── ActionButtons
├── UploadSection (State-Dependent)
│   ├── NoDataUploader (when NO_DATABASE)
│   ├── ReplaceUploader (when DATABASE_LOADED)
│   ├── AppendUploader (when DATABASE_LOADED)
│   └── MultiFileUploader (any state)
├── ProcessingSection
│   ├── FileValidationResults
│   ├── PreviewArea
│   └── OptionsPanel
└── ActionsSection
    ├── PrimaryActions
    ├── SecondaryActions
    └── RollbackOptions
```

### **Dynamic UI Logic**
```python
def render_upload_interface():
    current_state = get_upload_state()
    
    # Always show status
    render_status_header(current_state)
    
    # State-dependent upload section
    if current_state == UploadState.NO_DATABASE:
        render_fresh_start_interface()
    elif current_state == UploadState.DATABASE_LOADED:
        render_database_management_interface()
    elif current_state == UploadState.PROCESSING_FILES:
        render_processing_interface()
    elif current_state == UploadState.PREVIEW_MERGE:
        render_preview_interface()
    elif current_state == UploadState.ERROR_STATE:
        render_error_interface()
```

---

## 🔧 **File Processing Architecture**

### **Processing Pipeline**
```
File Upload → Validation → Parsing → Format Detection → Processing → Storage
```

### **FileProcessor Class Design**
```python
class FileProcessor:
    def __init__(self):
        self.validators = [
            JSONSyntaxValidator(),
            QuestionStructureValidator(), 
            LaTeXValidator(),
            MetadataValidator()
        ]
    
    def process_file(self, uploaded_file) -> ProcessingResult:
        """Main processing pipeline"""
        
    def validate_json_syntax(self, content: str) -> ValidationResult:
        """Basic JSON validation"""
        
    def detect_format_version(self, data: dict) -> str:
        """Detect Phase 3/4/Legacy format"""
        
    def extract_questions(self, data: dict) -> List[dict]:
        """Extract questions regardless of format"""
        
    def validate_question_structure(self, questions: List[dict]) -> ValidationResult:
        """Validate required fields and structure"""
```

### **Validation Chain Architecture**
```python
class ValidationChain:
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator: BaseValidator):
        self.validators.append(validator)
    
    def validate(self, data) -> ValidationResult:
        results = []
        for validator in self.validators:
            result = validator.validate(data)
            results.append(result)
            if result.is_critical_error():
                break
        return ValidationResult.combine(results)
```

---

## 🔄 **Database Merger Architecture**

### **Merge Strategies**
```python
class MergeStrategy(Enum):
    APPEND_ALL = "append_all"           # Add all questions
    SKIP_DUPLICATES = "skip_duplicates" # Skip duplicate questions
    REPLACE_DUPLICATES = "replace_duplicates" # Replace existing with new
    RENAME_DUPLICATES = "rename_duplicates"   # Rename conflicting questions
```

### **DatabaseMerger Class Design**
```python
class DatabaseMerger:
    def __init__(self, strategy: MergeStrategy = MergeStrategy.SKIP_DUPLICATES):
        self.strategy = strategy
        self.conflict_resolver = ConflictResolver()
    
    def merge_databases(self, current_df: pd.DataFrame, 
                       new_questions: List[dict]) -> MergeResult:
        """Main merge operation"""
        
    def detect_duplicates(self, existing: pd.DataFrame, 
                         new: List[dict]) -> List[Conflict]:
        """Find duplicate questions"""
        
    def resolve_conflicts(self, conflicts: List[Conflict]) -> ResolutionPlan:
        """Generate conflict resolution plan"""
        
    def apply_merge(self, plan: ResolutionPlan) -> pd.DataFrame:
        """Execute the merge operation"""
```

### **Conflict Resolution System**
```python
class Conflict:
    def __init__(self, existing_question: dict, new_question: dict, 
                 conflict_type: ConflictType):
        self.existing = existing_question
        self.new = new_question
        self.type = conflict_type
        self.resolution = None

class ConflictResolver:
    def suggest_resolution(self, conflict: Conflict) -> Resolution:
        """AI-powered conflict resolution suggestions"""
        
    def apply_resolution(self, conflict: Conflict, 
                        resolution: Resolution) -> dict:
        """Apply chosen resolution"""
```

---

## 📊 **Data Flow Architecture**

### **Upload Flow**
```
User Selects File(s)
    ↓
FileProcessor.process_file()
    ↓
ValidationChain.validate()
    ↓ (if valid)
FormatDetector.detect_version()
    ↓
QuestionExtractor.extract()
    ↓
Store in session_state['processing_results']
    ↓
Update UI state to PROCESSING_FILES
    ↓
User reviews results & confirms
    ↓
DatabaseMerger.merge() (if appending)
    ↓
Update session_state['df']
    ↓
Update UI state to DATABASE_LOADED
```

### **Error Flow**
```
Validation Fails
    ↓
Store error in session_state['error_message']
    ↓
Update UI state to ERROR_STATE
    ↓
Show error details & recovery options
    ↓
User fixes issue or cancels
    ↓
Return to previous state
```

---

## 🔌 **Integration Architecture**

### **Existing Module Integration**
```python
# Integration points with existing modules
from modules.session_manager import (
    initialize_session_state,
    clear_session_state,
    save_database_to_history
)

from modules.database_processor import (
    validate_single_question,
    process_latex_content
)

from modules.question_editor import (
    side_by_side_question_editor  # Use after upload
)
```

### **Backward Compatibility**
- Keep existing `upload_handler.py` as backup
- Maintain same session state structure where possible
- Ensure existing question editor still works
- Preserve export functionality

---

## 🎨 **UI Component Architecture**

### **StatusHeader Component**
```python
def render_status_header():
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        render_database_status_indicator()
    
    with col2:
        render_quick_stats()
    
    with col3:
        render_action_buttons()
```

### **State-Specific Uploaders**
```python
def render_fresh_start_interface():
    """Clean interface for first upload"""
    st.markdown("### 📤 Upload Your First Database")
    
    tab1, tab2 = st.tabs(["Single File", "Multiple Files"])
    
    with tab1:
        render_single_file_uploader(key="fresh_single")
    
    with tab2:
        render_multi_file_uploader(key="fresh_multi")

def render_database_management_interface():
    """Interface when database exists"""
    st.markdown("### 🗃️ Database Management")
    
    tab1, tab2 = st.tabs(["Replace Database", "Append Questions"])
    
    with tab1:
        render_replace_interface()
    
    with tab2:
        render_append_interface()
```

---

## 🔐 **Error Handling Architecture**

### **Error Hierarchy**
```python
class UploadError(Exception):
    """Base class for upload errors"""
    pass

class ValidationError(UploadError):
    """File validation failed"""
    pass

class FormatError(UploadError):
    """Unsupported file format"""
    pass

class MergeError(UploadError):
    """Database merge operation failed"""
    pass

class StateError(UploadError):
    """Invalid state transition"""
    pass
```

### **Error Recovery System**
```python
class ErrorRecovery:
    def __init__(self):
        self.recovery_strategies = {
            ValidationError: self.handle_validation_error,
            FormatError: self.handle_format_error,
            MergeError: self.handle_merge_error,
            StateError: self.handle_state_error
        }
    
    def recover_from_error(self, error: UploadError) -> RecoveryPlan:
        strategy = self.recovery_strategies.get(type(error))
        return strategy(error) if strategy else self.default_recovery(error)
```

---

## 🧪 **Testing Architecture**

### **Test Structure**
```
tests/
├── test_file_processor.py      # File processing unit tests
├── test_database_merger.py     # Merge logic unit tests
├── test_upload_interface.py    # UI integration tests
├── test_state_management.py    # State transition tests
├── fixtures/
│   ├── valid_phase4.json
│   ├── valid_phase3.json
│   ├── invalid_syntax.json
│   └── large_database.json
└── integration/
    └── test_full_workflow.py   # End-to-end tests
```

### **Test Coverage Requirements**
- **File Processing**: All validation scenarios
- **State Management**: All state transitions
- **Merge Operations**: All conflict resolution strategies
- **Error Handling**: All error types and recovery
- **UI Integration**: All user workflows

---

## 📈 **Performance Architecture**

### **Memory Management**
```python
class MemoryManager:
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory = max_memory_mb * 1024 * 1024
        
    def check_memory_usage(self) -> bool:
        """Check if current memory usage is acceptable"""
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage"""
        
    def cleanup_temporary_data(self):
        """Clean up temporary processing data"""
```

### **Processing Optimization**
- **Lazy Loading**: Load file contents only when needed
- **Chunk Processing**: Handle large files in chunks
- **Background Processing**: Use threading for long operations
- **Progress Tracking**: Show progress for slow operations

---

## 🚀 **Implementation Strategy**

### **Phase 2A: Core Architecture (Week 1)**
1. Create new module files with basic structure
2. Implement state management system
3. Build file processor with validation
4. Create basic UI components

### **Phase 2B: Integration (Week 2)**
1. Integrate with existing session management
2. Connect to database processor
3. Build merge functionality
4. Implement error handling

### **Phase 2C: Polish (Week 3)**
1. Advanced features (multi-file, conflict resolution)
2. Performance optimization
3. Comprehensive testing
4. User experience refinement

---

## ✅ **Success Criteria for Phase 2**

### **Architecture Completeness**
- [ ] All 4 core workflows have clear implementation paths
- [ ] State management system is well-defined
- [ ] Integration points with existing code are identified
- [ ] Error handling covers all failure modes

### **Technical Soundness**
- [ ] Memory management strategy for large files
- [ ] Performance optimization plans
- [ ] Testing strategy covers all components
- [ ] Backward compatibility maintained

### **Implementation Readiness**
- [ ] Module structure is clear and logical
- [ ] Component interfaces are well-defined
- [ ] Data flow is documented
- [ ] Implementation can begin immediately

---

**🎯 Phase 2 Complete: Architecture Design Ready for Implementation**