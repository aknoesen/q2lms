# Phase 3D: Upload Interface UI - Complete Design Specification
## Building on Proven Backend Foundation (Phases 3A/3B/3C)

---

## 🎯 **Design Overview**

**Goal**: Create clean, state-driven UI layer that integrates seamlessly with all completed backend phases to provide intuitive upload workflows.

**Backend Foundation Available**:
- ✅ **Phase 3A**: FileProcessor with validation pipeline
- ✅ **Phase 3B**: UploadStateManager with 6 states and transitions  
- ✅ **Phase 3C**: DatabaseMerger with 4 strategies and conflict resolution
- ✅ **All Integration Points**: Session state, APIs, error handling proven

---

## 🏗️ **UI Architecture Design**

### **State-Driven Interface Pattern**
```python
# Core UI pattern - adapts to current upload state
def render_upload_interface_v2():
    current_state = get_upload_state()
    
    # Always render status header
    render_status_header(current_state)
    
    # State-specific main interface
    interface_map = {
        UploadState.NO_DATABASE: render_fresh_start_interface,
        UploadState.DATABASE_LOADED: render_database_management_interface,
        UploadState.PROCESSING_FILES: render_processing_interface,
        UploadState.PREVIEW_MERGE: render_merge_preview_interface,  # Key new interface
        UploadState.ERROR_STATE: render_error_recovery_interface,
        UploadState.SUCCESS_STATE: render_success_interface
    }
    
    interface_renderer = interface_map.get(current_state)
    if interface_renderer:
        interface_renderer()
```

### **Component Hierarchy**
```
UploadInterfaceV2
├── StatusHeader
│   ├── StateIndicator (🟡 No DB, 🟢 Loaded, 🔄 Processing, etc.)
│   ├── DatabaseSummary (question count, topics, filename)
│   └── QuickActions (Export, Clear, Rollback)
├── MainInterface (State-Dependent)
│   ├── FreshStartInterface (NO_DATABASE)
│   ├── DatabaseManagementInterface (DATABASE_LOADED)
│   ├── ProcessingInterface (PROCESSING_FILES)
│   ├── MergePreviewInterface (PREVIEW_MERGE) ← Key new component
│   ├── ErrorRecoveryInterface (ERROR_STATE)
│   └── SuccessInterface (SUCCESS_STATE)
└── SharedComponents
    ├── FileUploadWidget (with unique keys per state)
    ├── ValidationResultsDisplay
    ├── ProgressIndicator
    └── ActionButtonGroup
```

---

## 🎨 **Interface Specifications by State**

### **1. Fresh Start Interface (NO_DATABASE)**
**Purpose**: Clean first-time user experience
```python
def render_fresh_start_interface():
    st.markdown("### 📤 Upload Your First Question Database")
    st.info("No database currently loaded. Upload a JSON file to begin.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Single File Upload")
        uploaded_file = st.file_uploader(
            "Choose JSON file",
            type=['json'],
            key="fresh_single_upload",
            help="Upload a single question database file"
        )
        if uploaded_file:
            handle_fresh_upload(uploaded_file)
    
    with col2:
        st.markdown("#### Multiple Files (Auto-Merge)")
        uploaded_files = st.file_uploader(
            "Choose JSON files",
            type=['json'],
            accept_multiple_files=True,
            key="fresh_multi_upload",
            help="Upload multiple files to merge automatically"
        )
        if uploaded_files:
            handle_fresh_multi_upload(uploaded_files)
```

### **2. Database Management Interface (DATABASE_LOADED)**
**Purpose**: Operations on existing database
```python
def render_database_management_interface():
    st.markdown("### 🗃️ Database Operations")
    
    # Show current database summary
    render_database_summary()
    
    # Operation tabs
    tab1, tab2, tab3 = st.tabs(["📝 Append Questions", "🔄 Replace Database", "📁 Merge Files"])
    
    with tab1:
        render_append_interface()
    
    with tab2:
        render_replace_interface()
    
    with tab3:
        render_multi_merge_interface()
```

### **3. Merge Preview Interface (PREVIEW_MERGE) - Key New Component**
**Purpose**: Show conflicts and get user confirmation for merge operations
```python
def render_merge_preview_interface():
    st.markdown("### 🔍 Merge Preview & Conflict Resolution")
    
    preview_data = st.session_state.get('preview_data', {})
    
    # Statistics dashboard
    render_merge_statistics(preview_data)
    
    # Strategy selection
    render_strategy_selection(preview_data)
    
    # Conflict details (expandable)
    render_conflict_details(preview_data)
    
    # Action buttons
    render_merge_actions(preview_data)
```

---

## 🔧 **Core Component Designs**

### **Status Header Component**
```python
def render_status_header(current_state: UploadState):
    """Always-visible status information"""
    
    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
    
    with col1:
        # State indicator with emoji and color
        state_info = {
            UploadState.NO_DATABASE: ("🟡", "No Database"),
            UploadState.DATABASE_LOADED: ("🟢", "Database Loaded"),
            UploadState.PROCESSING_FILES: ("🔄", "Processing"),
            UploadState.PREVIEW_MERGE: ("🔍", "Preview Merge"),
            UploadState.ERROR_STATE: ("❌", "Error"),
            UploadState.SUCCESS_STATE: ("✅", "Success")
        }
        emoji, label = state_info.get(current_state, ("❓", "Unknown"))
        st.markdown(f"{emoji} **{label}**")
    
    with col2:
        # Database summary
        if hasattr(st.session_state, 'df') and st.session_state.df is not None:
            count = len(st.session_state.df)
            filename = st.session_state.get('current_filename', 'Unknown')
            st.markdown(f"📊 **{count} questions** in `{filename}`")
        else:
            st.markdown("📊 No database loaded")
    
    with col3:
        # Quick actions
        if current_state == UploadState.DATABASE_LOADED:
            if st.button("📤 Export", key="quick_export"):
                handle_export_action()
    
    with col4:
        # Rollback option
        if st.session_state.get('can_rollback', False):
            if st.button("↩️ Rollback", key="quick_rollback"):
                handle_rollback_action()
```

### **Merge Preview Component (Key New Feature)**
```python
def render_merge_preview_interface():
    """Complete merge preview with conflict resolution"""
    
    st.markdown("### 🔍 Merge Preview & Conflict Resolution")
    
    preview_data = st.session_state.get('preview_data', {})
    if not preview_data:
        st.error("No preview data available")
        return
    
    # Top-level statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Questions", preview_data.get('existing_count', 0))
    with col2:
        st.metric("New Questions", preview_data.get('new_count', 0))
    with col3:
        st.metric("Final Total", preview_data.get('final_count', 0))
    with col4:
        conflicts = preview_data.get('total_conflicts', 0)
        st.metric("Conflicts", conflicts, delta=f"{conflicts} to resolve" if conflicts > 0 else "None")
    
    # Strategy selection
    st.markdown("#### Merge Strategy")
    current_strategy = preview_data.get('merge_strategy', 'skip_duplicates')
    
    strategy_options = {
        'append_all': "Append All - Add all questions (including duplicates)",
        'skip_duplicates': "Skip Duplicates - Skip questions similar to existing ones",
        'replace_duplicates': "Replace Duplicates - Replace existing with new versions", 
        'rename_duplicates': "Rename Duplicates - Rename conflicting questions"
    }
    
    selected_strategy = st.radio(
        "Choose how to handle conflicts:",
        options=list(strategy_options.keys()),
        format_func=lambda x: strategy_options[x],
        index=list(strategy_options.keys()).index(current_strategy),
        key="merge_strategy_selection"
    )
    
    # Update preview if strategy changed
    if selected_strategy != current_strategy:
        update_merge_preview_strategy(selected_strategy)
        st.rerun()
    
    # Conflict details (if any)
    conflicts = preview_data.get('conflict_details', [])
    if conflicts:
        render_conflict_details_section(conflicts)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("✅ Confirm Merge", type="primary", key="confirm_merge"):
            execute_confirmed_merge()
    with col2:
        if st.button("🔄 Change Strategy", key="change_strategy"):
            # Strategy radio above handles this
            pass
    with col3:
        if st.button("❌ Cancel", key="cancel_merge"):
            cancel_merge_operation()

def render_conflict_details_section(conflicts):
    """Expandable conflict details"""
    
    st.markdown("#### Conflict Details")
    
    # Group conflicts by severity
    severity_groups = {}
    for conflict in conflicts:
        severity = conflict.get('severity', 'medium')
        if severity not in severity_groups:
            severity_groups[severity] = []
        severity_groups[severity].append(conflict)
    
    # Show each severity group
    severity_order = ['critical', 'high', 'medium', 'low']
    severity_colors = {
        'critical': '🔴',
        'high': '🟠', 
        'medium': '🟡',
        'low': '🟢'
    }
    
    for severity in severity_order:
        if severity in severity_groups:
            conflicts_group = severity_groups[severity]
            emoji = severity_colors[severity]
            
            with st.expander(f"{emoji} {severity.title()} Severity ({len(conflicts_group)} conflicts)"):
                for i, conflict in enumerate(conflicts_group):
                    st.markdown(f"**Conflict {i+1}**: {conflict.get('description', 'No description')}")
                    st.markdown(f"*Suggestion*: {conflict.get('suggestion', 'No suggestion')}")
                    
                    if 'existing_question' in conflict and 'new_question' in conflict:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Existing:**")
                            st.code(conflict['existing_question'].get('text', 'No text')[:100] + "...")
                        with col2:
                            st.markdown("**New:**")
                            st.code(conflict['new_question'].get('text', 'No text')[:100] + "...")
                    
                    st.markdown("---")
```

---

## 🔄 **Integration with Backend APIs**

### **Phase 3A Integration (File Processing)**
```python
def handle_file_upload(uploaded_file, operation_type="fresh"):
    """Integrate with FileProcessor from Phase 3A"""
    
    try:
        # Use proven Phase 3A API
        from modules.file_processor_module import FileProcessor
        
        processor = FileProcessor()
        processing_result = processor.process_file(uploaded_file)
        
        if processing_result.valid:
            # Store results for next phase
            st.session_state['processing_results'] = {
                'questions': processing_result.questions,
                'format_detected': processing_result.format_detected,
                'metadata': processing_result.metadata,
                'issues': processing_result.issues
            }
            
            # Transition to next state
            from modules.upload_state_manager import transition_upload_state, UploadState
            
            if operation_type == "fresh":
                # Fresh upload - go directly to loaded
                transition_upload_state(UploadState.DATABASE_LOADED, "fresh_upload_complete")
                apply_fresh_database(processing_result)
            else:
                # Append operation - go to preview
                transition_upload_state(UploadState.PROCESSING_FILES, "file_processed")
                prepare_merge_preview(processing_result)
                
        else:
            # Handle validation errors
            handle_processing_errors(processing_result.issues)
            
    except Exception as e:
        handle_upload_error(e)
```

### **Phase 3B Integration (State Management)**
```python
def get_upload_state():
    """Get current state using Phase 3B API"""
    from modules.upload_state_manager import get_current_upload_state
    return get_current_upload_state()

def transition_to_state(new_state, reason="ui_action"):
    """Safe state transition using Phase 3B API"""
    from modules.upload_state_manager import transition_upload_state
    return transition_upload_state(new_state, reason)
```

### **Phase 3C Integration (Database Merger)**
```python
def prepare_merge_preview(processing_result):
    """Create merge preview using Phase 3C API"""
    
    try:
        from modules.database_merger import (
            create_merge_preview, 
            prepare_session_state_for_preview,
            MergeStrategy
        )
        
        # Get current database
        existing_df = st.session_state.get('df')
        new_questions = processing_result.questions
        
        # Create preview with default strategy
        preview = create_merge_preview(
            existing_df=existing_df,
            new_questions=new_questions,
            strategy=MergeStrategy.SKIP_DUPLICATES
        )
        
        # Prepare UI-friendly data
        preview_data = prepare_session_state_for_preview(preview, processing_result)
        st.session_state['preview_data'] = preview_data
        
        # Transition to preview state
        transition_to_state(UploadState.PREVIEW_MERGE, "preview_prepared")
        
    except Exception as e:
        handle_merge_error(e)

def execute_confirmed_merge():
    """Execute merge using Phase 3C API"""
    
    try:
        from modules.database_merger import (
            execute_database_merge,
            update_session_state_after_merge
        )
        
        preview_data = st.session_state.get('preview_data', {})
        selected_strategy = st.session_state.get('merge_strategy_selection', 'skip_duplicates')
        
        # Execute merge
        merge_result = execute_database_merge(
            existing_df=st.session_state['df'],
            processing_result=st.session_state['processing_results'],
            strategy=selected_strategy
        )
        
        if merge_result.success:
            # Update session state
            update_session_state_after_merge(merge_result)
            
            # Success state
            transition_to_state(UploadState.SUCCESS_STATE, "merge_completed")
            st.success(f"Successfully merged! Database now has {len(merge_result.merged_df)} questions.")
            
        else:
            # Handle merge failure
            handle_merge_failure(merge_result.error)
            
    except Exception as e:
        handle_merge_error(e)
```

---

## 🎯 **Implementation Plan**

### **Phase 3D-A: Core UI Framework (Week 1)**
1. **Basic structure**: `modules/upload_interface_v2.py` with state-driven pattern
2. **Status header**: Always-visible state and database info
3. **Fresh start interface**: Clean first-time user experience
4. **Integration testing**: Ensure Phase 3A/3B/3C APIs work through UI

### **Phase 3D-B: Database Management (Week 2)**
1. **Database loaded interface**: Append/replace/merge tabs
2. **File upload handlers**: Integration with file processor
3. **Basic error handling**: User-friendly error displays
4. **State transitions**: Ensure UI updates correctly with state changes

### **Phase 3D-C: Merge Preview (Week 3)**
1. **Merge preview interface**: Complete conflict visualization
2. **Strategy selection**: Real-time preview updates
3. **Conflict details**: Expandable detailed conflict information
4. **Confirmation flow**: Safe merge execution with rollback

### **Phase 3D-D: Integration & Polish (Week 4)**
1. **Main app integration**: Update `streamlit_app.py` imports
2. **Existing functionality**: Ensure question editor still works
3. **Performance optimization**: Efficient re-renders and state management
4. **User testing**: Validate all workflows work end-to-end

---

## ✅ **Success Criteria**

### **Functional Requirements**
- [ ] All 6 upload states have appropriate UI interfaces
- [ ] Fresh start workflow is intuitive and fast
- [ ] Append operation shows clear merge preview
- [ ] Replace operation has appropriate warnings
- [ ] Multi-file merge handles conflicts properly
- [ ] Error states provide clear recovery paths

### **Integration Requirements**
- [ ] All Phase 3A/3B/3C APIs used correctly
- [ ] Session state consistency maintained
- [ ] Existing question editor continues to work
- [ ] No widget key conflicts or duplicates
- [ ] State transitions trigger correct UI updates

### **User Experience Requirements**
- [ ] Interface is intuitive for first-time users
- [ ] Clear visual feedback for all operations
- [ ] No confusing states or dead ends
- [ ] Fast response times for typical operations
- [ ] Mobile-friendly responsive design

---

## 🧪 **Testing Strategy**

### **UI Integration Tests**
```python
def test_fresh_start_workflow():
    """Test complete fresh start upload"""
    # Simulate file upload
    # Verify state transitions
    # Check database loaded correctly

def test_append_workflow():
    """Test append with conflict resolution"""
    # Load initial database
    # Upload additional file
    # Test merge preview interface
    # Confirm merge operation

def test_error_recovery():
    """Test error handling and recovery"""
    # Upload invalid file
    # Verify error state
    # Test recovery options
```

### **Real Data Testing**
- Use `debug tests/Phase Five/latex_questions_v1_part1.json`
- Test with 25 real questions
- Validate merge conflicts work properly
- Ensure LaTeX content displays correctly

---

## 🚀 **Ready to Implement**

**Architecture Complete**: State-driven UI design leverages all proven backend APIs
**Integration Points**: All Phase 3A/3B/3C integration patterns defined
**Component Design**: Complete specifications for each UI state and component
**Implementation Plan**: Clear weekly progression with testing at each step

**Next Step**: Begin implementation of `modules/upload_interface_v2.py` starting with core framework and fresh start interface.

This design builds systematically on your proven backend foundation while providing the clean, intuitive interface your users need! 🎯