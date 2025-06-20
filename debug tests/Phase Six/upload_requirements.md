# Upload Interface Requirements Specification
## Version 2.0 - Clean Rebuild

---

## 🎯 **Core Workflows**

### **Workflow 1: Fresh Start (No Database Loaded)**
**Scenario**: User opens app with no existing database
- **Available Actions**: 
  - Upload single JSON file
  - Upload multiple JSON files (auto-merge)
- **UI State**: 
  - Show "No Database" status
  - Single upload widget
  - Clear instructions
- **Success**: Database loaded, interface switches to "Database Loaded" state

### **Workflow 2: Replace Database (Database Exists)**
**Scenario**: User has database loaded and wants to replace it entirely
- **Available Actions**:
  - Upload new JSON file to replace current database
  - Confirm replacement (destructive action)
  - Option to save current to history before replacing
- **UI State**:
  - Show current database info
  - Clear warning about replacement
  - Confirmation step required
- **Success**: Old database replaced, new database loaded

### **Workflow 3: Append Questions (Database Exists)**
**Scenario**: User has database loaded and wants to add more questions
- **Available Actions**:
  - Upload additional JSON file(s)
  - Preview questions to be added
  - Handle duplicate questions (skip/rename/replace)
  - Merge metadata appropriately
- **UI State**:
  - Show current database summary
  - Show preview of questions to add
  - Show final merged result preview
- **Success**: Questions appended to existing database

### **Workflow 4: Multiple File Merge (No Database or With Database)**
**Scenario**: User wants to combine multiple JSON files into one database
- **Available Actions**:
  - Upload multiple JSON files simultaneously
  - Preview each file's contents
  - Reorder files if needed
  - Handle conflicts between files
  - Choose merge strategy
- **UI State**:
  - File-by-file breakdown
  - Merge preview with statistics
  - Conflict resolution interface
- **Success**: All files merged into single database

---

## 🖥️ **Interface Requirements**

### **Visual State Management**
- **Clear State Indicators**:
  - 🟡 No Database Loaded
  - 🟢 Database Loaded (X questions)
  - 🔄 Processing Files
  - ❌ Error State
  - ✅ Success State

### **Widget Management**
- **No Duplicate Widgets**: Each upload scenario uses unique widget keys
- **Dynamic UI**: Interface adapts based on current state
- **Progressive Disclosure**: Advanced options hidden until needed
- **Clear CTAs**: Obvious next steps for each state

### **Feedback Systems**
- **Real-time Validation**: File format checking as user selects files
- **Progress Indicators**: For file processing and database operations
- **Success/Error Messages**: Clear feedback for all operations
- **Preview Capabilities**: Show what will happen before committing

---

## 🔧 **Technical Requirements**

### **File Processing**
- **Supported Formats**: JSON question databases
- **Format Detection**: Auto-detect Phase 3, Phase 4, Legacy formats
- **Validation**: 
  - JSON syntax validation
  - Required field checking
  - Question structure validation
  - LaTeX syntax validation
- **Error Handling**: Graceful degradation for malformed files

### **Database Operations**
- **Loading**: Single file → DataFrame conversion
- **Merging**: Multiple files → Combined DataFrame
- **Appending**: New questions → Existing DataFrame
- **Validation**: Duplicate detection and handling
- **Metadata Management**: Preserve and merge metadata appropriately

### **Session Management**
- **State Persistence**: Maintain database across page refreshes
- **History Tracking**: Keep record of recent databases
- **Rollback Capability**: Undo recent operations
- **Memory Management**: Efficient handling of large databases

---

## 🎨 **User Experience Requirements**

### **Ease of Use**
- **Intuitive Flow**: Natural progression from no database → loaded → operations
- **Minimal Clicks**: Essential operations accessible in 1-2 clicks
- **Clear Instructions**: Contextual help and guidance
- **Error Recovery**: Easy path to fix problems

### **Flexibility**
- **Multiple Workflows**: Support different user preferences
- **Batch Operations**: Handle multiple files efficiently
- **Advanced Options**: Power user features available but hidden
- **Customization**: Processing options (LaTeX, validation, etc.)

### **Performance**
- **Fast Loading**: Quick file processing and validation
- **Responsive UI**: No blocking operations
- **Memory Efficient**: Handle large files without crashes
- **Progressive Loading**: Show progress for slow operations

---

## 📊 **Interface Layout Structure**

### **Header Section**
- Database status indicator
- Quick stats (questions, topics, etc.)
- Action buttons (Clear, Export, etc.)

### **Upload Section**
- State-aware interface
- Context-appropriate upload widgets
- Preview areas for selected files

### **Processing Section**
- Options and configurations
- Validation results
- Preview of operations

### **Actions Section**
- Primary action buttons
- Secondary options
- Cancel/rollback options

---

## 🔍 **Error Handling Requirements**

### **File-Level Errors**
- **Invalid JSON**: Clear error message with line number if possible
- **Missing Fields**: List missing required fields
- **Format Issues**: Explain format expectations
- **Size Limits**: Handle oversized files gracefully

### **Database-Level Errors**
- **Merge Conflicts**: Present resolution options
- **Duplicate Questions**: Show duplicates and handling options
- **Validation Failures**: List all validation issues
- **Memory Issues**: Graceful degradation for large databases

### **Recovery Options**
- **Retry Mechanisms**: Allow user to fix and retry
- **Partial Success**: Handle when some files work, others don't
- **Rollback**: Return to previous state if operation fails
- **Help Resources**: Links to documentation or examples

---

## 🧪 **Testing Requirements**

### **Functional Testing**
- All 4 core workflows work correctly
- Error handling for all failure modes
- State transitions work properly
- Session persistence works

### **Usability Testing**
- Interface is intuitive for new users
- Advanced features are discoverable
- Error messages are helpful
- Performance is acceptable

### **Edge Cases**
- Very large files (100MB+)
- Malformed JSON files
- Empty databases
- Network interruptions during upload

---

## 📈 **Success Metrics**

### **User Experience**
- ✅ User can load their first database in under 30 seconds
- ✅ Append operation is discoverable and easy to use
- ✅ Error states are clear and actionable
- ✅ No duplicate widgets or confusing UI elements

### **Technical Performance**
- ✅ Handles files up to 200MB without issues
- ✅ Processing time under 10 seconds for typical files
- ✅ Memory usage remains reasonable
- ✅ No session state corruption

### **Feature Completeness**
- ✅ All 4 core workflows implemented
- ✅ Proper error handling for all scenarios
- ✅ State management works correctly
- ✅ Integration with existing question editor works

---

## 🚀 **Implementation Priority**

### **Phase 1 (MVP)**
1. Fresh Start workflow
2. Basic file validation
3. Simple replace workflow
4. Core error handling

### **Phase 2 (Enhanced)**
1. Append workflow
2. Multiple file merge
3. Advanced validation
4. History/rollback

### **Phase 3 (Polish)**
1. Advanced options
2. Performance optimization
3. Enhanced error messages
4. User testing and refinement