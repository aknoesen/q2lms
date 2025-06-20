# setup_and_test_fixed.py
"""
Setup and test script for Phase 3B: Upload State Manager
Run this from your question-database-manager directory on Windows.
"""

import os
import sys
from pathlib import Path
import importlib.util

def setup_environment():
    """Setup the environment for testing."""
    print("🔧 Setting up test environment...")
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Check if we're in the right directory
    expected_files = ['modules', 'streamlit_app.py']
    missing_files = []
    
    for file in expected_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing expected files/folders: {missing_files}")
        print("Please run this script from your question-database-manager directory")
        return False
    
    # Add current directory to Python path
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print("✅ Environment setup complete")
    return True

def create_mock_streamlit():
    """Create mock streamlit for testing without importing actual streamlit."""
    
    class MockSessionState:
        def __init__(self):
            self._state = {}
        
        def __getitem__(self, key):
            return self._state[key]
        
        def __setitem__(self, key, value):
            self._state[key] = value
        
        def __contains__(self, key):
            return key in self._state
        
        def get(self, key, default=None):
            return self._state.get(key, default)
        
        def keys(self):
            return self._state.keys()
        
        def __setattr__(self, key, value):
            if key.startswith('_'):
                super().__setattr__(key, value)
            else:
                self._state[key] = value
        
        def __getattr__(self, key):
            if key in self._state:
                return self._state[key]
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    class MockStreamlit:
        def __init__(self):
            self.session_state = MockSessionState()
    
    # Replace streamlit in sys.modules
    sys.modules['streamlit'] = MockStreamlit()
    return sys.modules['streamlit']

def safe_import_module(module_path, module_name):
    """Safely import a module and return success status."""
    try:
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, module, None
        else:
            return False, None, f"Module file not found: {module_path}"
    except Exception as e:
        return False, None, str(e)

def test_file_processor_integration():
    """Test that we can import and use the file processor from Phase 3A."""
    print("\n🔗 Testing Phase 3A Integration...")
    
    file_processor_path = Path('modules') / 'file_processor_module.py'
    success, module, error = safe_import_module(file_processor_path, 'file_processor_module')
    
    if not success:
        print(f"❌ Could not import file_processor_module: {error}")
        return False
    
    try:
        # Get the FileProcessor class
        FileProcessor = getattr(module, 'FileProcessor', None)
        if FileProcessor is None:
            print("❌ FileProcessor class not found in module")
            return False
        
        print("✅ Successfully imported FileProcessor from Phase 3A")
        
        # Create a test instance
        processor = FileProcessor()
        print("✅ FileProcessor instance created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error with FileProcessor: {e}")
        return False

def test_upload_state_manager():
    """Test the upload state manager."""
    print("\n🧪 Testing Upload State Manager...")
    
    # First check if the file exists
    state_manager_path = Path('modules') / 'upload_state_manager.py'
    if not state_manager_path.exists():
        print(f"❌ upload_state_manager.py not found at {state_manager_path}")
        print("Please copy the upload_state_manager.py to your modules/ directory")
        return False
    
    success, module, error = safe_import_module(state_manager_path, 'upload_state_manager')
    
    if not success:
        print(f"❌ Could not import upload_state_manager: {error}")
        return False
    
    try:
        # Get the required classes
        UploadStateManager = getattr(module, 'UploadStateManager', None)
        UploadState = getattr(module, 'UploadState', None)
        
        if UploadStateManager is None or UploadState is None:
            print("❌ Required classes not found in upload_state_manager module")
            return False
        
        print("✅ Successfully imported UploadStateManager")
        
        # Create instance
        state_manager = UploadStateManager()
        print("✅ UploadStateManager instance created")
        
        # Test basic functionality
        current_state = state_manager.get_current_state()
        print(f"✅ Current state: {current_state}")
        
        # Test transition
        success = state_manager.transition_to_state(UploadState.PROCESSING_FILES, "test")
        print(f"✅ State transition success: {success}")
        
        # Test actions
        actions = state_manager.get_available_actions()
        print(f"✅ Available actions: {actions}")
        
        return True
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_system_compatibility():
    """Test compatibility with existing system components."""
    print("\n🔄 Testing Existing System Compatibility...")
    
    modules_to_test = [
        ('session_manager.py', 'session_manager'),
        ('database_processor.py', 'database_processor'),
        ('question_editor.py', 'question_editor')
    ]
    
    for filename, module_name in modules_to_test:
        module_path = Path('modules') / filename
        success, module, error = safe_import_module(module_path, module_name)
        
        if success:
            print(f"✅ {filename} imports successfully")
        elif module_path.exists():
            print(f"⚠️  {filename} found but import failed: {error}")
        else:
            print(f"⚠️  {filename} not found - this may be okay depending on system state")
    
    # Test streamlit app structure
    streamlit_app = Path('streamlit_app.py')
    if streamlit_app.exists():
        print("✅ streamlit_app.py found")
    else:
        print("❌ streamlit_app.py not found")
    
    return True

def create_integration_test():
    """Create a simple integration test."""
    print("\n🎯 Running Integration Test...")
    
    try:
        import pandas as pd
        
        # Import upload state manager
        state_manager_path = Path('modules') / 'upload_state_manager.py'
        success, module, error = safe_import_module(state_manager_path, 'upload_state_manager')
        
        if not success:
            print(f"   ❌ Could not import upload_state_manager for integration test: {error}")
            return False
        
        UploadStateManager = getattr(module, 'UploadStateManager')
        UploadState = getattr(module, 'UploadState')
        
        # Create state manager
        sm = UploadStateManager()
        
        # Test scenario: Fresh start -> Load database -> Append
        print("   Testing workflow: Fresh Start -> Database Load -> Append")
        
        # 1. Fresh start
        state = sm.get_current_state()
        assert state == UploadState.NO_DATABASE, f"Expected NO_DATABASE, got {state}"
        print("   ✅ Fresh start state correct")
        
        # 2. Simulate file upload
        success = sm.transition_to_state(UploadState.PROCESSING_FILES, "upload_file")
        assert success, "Should transition to processing"
        print("   ✅ Transitioned to processing")
        
        # 3. Simulate successful processing
        # Get streamlit mock
        st = sys.modules['streamlit']
        st.session_state.df = pd.DataFrame({'question': ['Q1'], 'answer': ['A1']})
        
        success = sm.transition_to_state(UploadState.DATABASE_LOADED, "processing_complete")
        assert success, "Should transition to database loaded"
        print("   ✅ Database loaded successfully")
        
        # 4. Test rollback functionality
        sm.create_rollback_point("test_point")
        assert st.session_state.can_rollback, "Should be able to rollback"
        print("   ✅ Rollback point created")
        
        # 5. Test state summary
        summary = sm.get_state_summary()
        assert 'current_state' in summary, "Summary should have current_state"
        print("   ✅ State summary working")
        
        # 6. Test state inference
        # Clear explicit state and test inference
        st.session_state.upload_state = None
        inferred_state = sm.get_current_state()
        assert inferred_state == UploadState.DATABASE_LOADED, f"Should infer DATABASE_LOADED, got {inferred_state}"
        print("   ✅ State inference working")
        
        # 7. Test rollback operation
        rollback_success = sm.rollback_to_point()
        assert rollback_success, "Rollback should succeed"
        print("   ✅ Rollback operation working")
        
        print("   🎉 Integration test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_file_integration():
    """Test with real test file if available."""
    print("\n📁 Testing Real File Integration...")
    
    test_file_path = Path('debug tests') / 'Phase Five' / 'latex_questions_v1_part1.json'
    
    if not test_file_path.exists():
        print(f"   ⚠️  Test file not found at {test_file_path}")
        print("   Skipping real file test")
        return True
    
    try:
        # Import both modules
        fp_path = Path('modules') / 'file_processor_module.py'
        sm_path = Path('modules') / 'upload_state_manager.py'
        
        # Import file processor
        fp_success, fp_module, fp_error = safe_import_module(fp_path, 'file_processor_module')
        if not fp_success:
            print(f"   ❌ Could not import file processor: {fp_error}")
            return False
        
        # Import state manager
        sm_success, sm_module, sm_error = safe_import_module(sm_path, 'upload_state_manager')