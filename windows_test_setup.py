# setup_and_test.py
"""
Setup and test script for Phase 3B: Upload State Manager
Run this from your question-database-manager directory on Windows.
"""

import os
import sys
from pathlib import Path

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
    
    class MockStreamlit:
        def __init__(self):
            self.session_state = MockSessionState()
    
    # Replace streamlit in sys.modules
    sys.modules['streamlit'] = MockStreamlit()
    return sys.modules['streamlit']

def test_file_processor_integration():
    """Test that we can import and use the file processor from Phase 3A."""
    print("\n🔗 Testing Phase 3A Integration...")
    
    try:
        from modules.file_processor_module import FileProcessor
        print("✅ Successfully imported FileProcessor from Phase 3A")
        
        # Create a test instance
        processor = FileProcessor()
        print("✅ FileProcessor instance created successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Could not import FileProcessor: {e}")
        print("Phase 3A (file_processor_module.py) may not be in modules/ directory")
        return False
    except Exception as e:
        print(f"❌ Error with FileProcessor: {e}")
        return False

def test_upload_state_manager():
    """Test the upload state manager."""
    print("\n🧪 Testing Upload State Manager...")
    
    try:
        # First check if the file exists
        state_manager_path = Path('modules') / 'upload_state_manager.py'
        if not state_manager_path.exists():
            print(f"❌ upload_state_manager.py not found at {state_manager_path}")
            print("Please copy the upload_state_manager.py to your modules/ directory")
            return False
        
        # Import the module
        from modules.upload_state_manager import UploadStateManager, UploadState
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
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Runtime error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_system_compatibility():
    """Test compatibility with existing system components."""
    print("\n🔄 Testing Existing System Compatibility...")
    
    # Test session manager import
    try:
        from modules.session_manager import *
        print("✅ session_manager.py imports successfully")
    except ImportError:
        print("⚠️  session_manager.py not found - this is okay if not created yet")
    except Exception as e:
        print(f"⚠️  session_manager.py import issue: {e}")
    
    # Test database processor import
    try:
        from modules.database_processor import *
        print("✅ database_processor.py imports successfully")
    except ImportError:
        print("⚠️  database_processor.py not found")
    except Exception as e:
        print(f"⚠️  database_processor.py import issue: {e}")
    
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
        from modules.upload_state_manager import UploadStateManager, UploadState
        
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
        
        print("   🎉 Integration test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner."""
    print("🚀 Phase 3B: Upload State Manager Test Suite")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        return False
    
    # Create mock streamlit
    st = create_mock_streamlit()
    print("✅ Mock Streamlit environment created")
    
    # Run tests
    tests = [
        ("File Processor Integration (Phase 3A)", test_file_processor_integration),
        ("Upload State Manager Core", test_upload_state_manager),
        ("Existing System Compatibility", test_existing_system_compatibility),
        ("Integration Test", create_integration_test)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Phase 3B: Upload State Manager is ready for integration")
        print("\n📋 Next Steps:")
        print("   1. Copy upload_state_manager.py to modules/ directory (if not done)")
        print("   2. Proceed to Phase 3C: Database Merger")
        print("   3. Begin UI integration planning")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed")
        print("Please check the errors above and fix before proceeding")
    
    return passed == len(results)

if __name__ == "__main__":
    main()
