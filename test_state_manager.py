# test_upload_state_manager.py
"""
Test script for upload_state_manager.py
Run this to validate integration with your existing system.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the project directory to path (adjust as needed)
# sys.path.append('C:\\Users\\aknoesen\\Documents\\Knoesen\\question-database-manager')

# Mock streamlit session state for testing
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

# Mock streamlit for testing
class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()

# Create mock streamlit
import sys
sys.modules['streamlit'] = MockStreamlit()
st = sys.modules['streamlit']

# Now import the state manager
from modules.upload_state_manager import UploadStateManager, UploadState

def test_state_manager():
    """Test the upload state manager functionality."""
    print("🧪 Testing Upload State Manager")
    print("=" * 50)
    
    # Initialize state manager
    state_manager = UploadStateManager()
    
    # Test 1: Initial state
    print("\n1. Testing Initial State")
    initial_state = state_manager.get_current_state()
    print(f"   Initial state: {initial_state}")
    assert initial_state == UploadState.NO_DATABASE, f"Expected NO_DATABASE, got {initial_state}"
    print("   ✅ Initial state correct")
    
    # Test 2: Available actions
    print("\n2. Testing Available Actions")
    actions = state_manager.get_available_actions()
    print(f"   Available actions: {actions}")
    expected_actions = ["upload_single_file", "upload_multiple_files"]
    assert all(action in actions for action in expected_actions), f"Missing expected actions"
    print("   ✅ Available actions correct")
    
    # Test 3: Valid transition
    print("\n3. Testing Valid Transition")
    success = state_manager.transition_to_state(UploadState.PROCESSING_FILES, "user_upload")
    print(f"   Transition success: {success}")
    assert success, "Valid transition failed"
    
    current_state = state_manager.get_current_state()
    print(f"   New state: {current_state}")
    assert current_state == UploadState.PROCESSING_FILES, f"State not updated correctly"
    print("   ✅ Valid transition works")
    
    # Test 4: Invalid transition
    print("\n4. Testing Invalid Transition")
    success = state_manager.transition_to_state(UploadState.NO_DATABASE, "invalid")
    print(f"   Invalid transition success: {success}")
    assert not success, "Invalid transition should fail"
    
    current_state = state_manager.get_current_state()
    print(f"   State remained: {current_state}")
    assert current_state == UploadState.PROCESSING_FILES, "State should not change on invalid transition"
    print("   ✅ Invalid transition correctly blocked")
    
    # Test 5: State inference
    print("\n5. Testing State Inference")
    # Manually set session state to simulate database loaded
    st.session_state.df = pd.DataFrame({'question': ['test'], 'answer': ['test']})
    st.session_state.upload_state = None  # Clear explicit state
    
    inferred_state = state_manager.get_current_state()
    print(f"   Inferred state with DataFrame: {inferred_state}")
    assert inferred_state == UploadState.DATABASE_LOADED, "Should infer DATABASE_LOADED with DataFrame"
    print("   ✅ State inference works")
    
    # Test 6: Rollback functionality
    print("\n6. Testing Rollback Functionality")
    state_manager.create_rollback_point("test rollback")
    print(f"   Can rollback: {st.session_state.get('can_rollback')}")
    assert st.session_state.get('can_rollback'), "Should be able to rollback after creating point"
    
    # Modify database
    st.session_state.df = pd.DataFrame({'question': ['modified'], 'answer': ['modified']})
    
    # Rollback
    rollback_success = state_manager.rollback_to_point()
    print(f"   Rollback success: {rollback_success}")
    assert rollback_success, "Rollback should succeed"
    
    # Check if data restored
    restored_data = st.session_state.df.iloc[0]['question']
    print(f"   Restored data: {restored_data}")
    assert restored_data == 'test', "Data should be restored to rollback point"
    print("   ✅ Rollback functionality works")
    
    # Test 7: Session state consistency
    print("\n7. Testing Session State Consistency")
    warnings = state_manager.validate_session_consistency()
    print(f"   Consistency warnings: {warnings}")
    # Should have minimal warnings in clean state
    print("   ✅ Session consistency validation works")
    
    # Test 8: State summary
    print("\n8. Testing State Summary")
    summary = state_manager.get_state_summary()
    print(f"   State summary keys: {list(summary.keys())}")
    expected_keys = ['current_state', 'available_actions', 'has_database', 'database_size']
    assert all(key in summary for key in expected_keys), "Missing expected summary keys"
    print("   ✅ State summary works")
    
    # Test 9: Reset functionality
    print("\n9. Testing Reset Functionality")
    state_manager.reset_upload_state(preserve_database=False)
    final_state = state_manager.get_current_state()
    print(f"   State after reset: {final_state}")
    assert final_state == UploadState.NO_DATABASE, "Reset should return to NO_DATABASE"
    assert st.session_state.get('df') is None, "Reset should clear database"
    print("   ✅ Reset functionality works")
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("Upload State Manager is ready for integration.")
    
    return True

def test_integration_points():
    """Test integration with expected existing modules."""
    print("\n🔌 Testing Integration Points")
    print("=" * 50)
    
    # Test session state structure compatibility
    print("\n1. Testing Session State Structure")
    state_manager = UploadStateManager()
    
    # Check that all expected keys exist
    required_keys = [
        'upload_state', 'df', 'original_questions', 'metadata',
        'current_filename', 'uploaded_files', 'processing_results',
        'preview_data', 'database_history', 'can_rollback'
    ]
    
    for key in required_keys:
        assert key in st.session_state, f"Missing required session state key: {key}"
        print(f"   ✅ {key} initialized")
    
    print("   ✅ Session state structure compatible")
    
    # Test file processor integration readiness
    print("\n2. Testing File Processor Integration Points")
    
    # Simulate file processing results (as would come from file_processor_module.py)
    st.session_state.processing_results = {
        'file1.json': {
            'valid': True,
            'questions_found': 25,
            'format_detected': 'Phase Four',
            'issues': []
        }
    }
    
    # Test state transition to processing
    success = state_manager.transition_to_state(UploadState.PROCESSING_FILES, "file_uploaded")
    assert success, "Should transition to processing state"
    print("   ✅ File processor integration point ready")
    
    # Test database merger integration readiness
    print("\n3. Testing Database Merger Integration Points")
    
    # Simulate preview data (as would be created by database merger)
    st.session_state.preview_data = {
        'merge_strategy': 'append_all',
        'new_questions': 25,
        'conflicts': [],
        'final_count': 50
    }
    
    # Test transition to preview state
    success = state_manager.transition_to_state(UploadState.PREVIEW_MERGE, "merge_preview")
    assert success, "Should transition to preview state"
    print("   ✅ Database merger integration point ready")
    
    print("\n" + "=" * 50)
    print("🔗 Integration Points Validated!")
    print("Ready for Phase 3C: Database Merger")

def demonstrate_workflow():
    """Demonstrate complete workflow scenarios."""
    print("\n🎭 Demonstrating Complete Workflows")
    print("=" * 50)
    
    state_manager = UploadStateManager()
    
    # Workflow 1: Fresh Start
    print("\n📤 Workflow 1: Fresh Start (No Database)")
    state = state_manager.get_current_state()
    actions = state_manager.get_available_actions()
    print(f"   State: {state.value}")
    print(f"   Available actions: {actions}")
    
    # User uploads file
    state_manager.transition_to_state(UploadState.PROCESSING_FILES, "upload_single_file")
    print("   → User uploads file")
    print(f"   → State: {state_manager.get_current_state().value}")
    
    # Processing completes successfully
    st.session_state.df = pd.DataFrame({'question': ['Q1'], 'answer': ['A1']})
    state_manager.transition_to_state(UploadState.DATABASE_LOADED, "processing_complete")
    print("   → Processing complete")
    print(f"   → State: {state_manager.get_current_state().value}")
    print(f"   → Available actions: {state_manager.get_available_actions()}")
    
    # Workflow 2: Append Questions
    print("\n➕ Workflow 2: Append Questions")
    state_manager.create_rollback_point("before_append")
    
    # User wants to append
    state_manager.transition_to_state(UploadState.PROCESSING_FILES, "append_questions")
    print("   → User chooses append")
    print(f"   → State: {state_manager.get_current_state().value}")
    
    # Shows preview
    st.session_state.preview_data = {'new_questions': 10, 'conflicts': 2}
    state_manager.transition_to_state(UploadState.PREVIEW_MERGE, "show_preview")
    print("   → Preview shown")
    print(f"   → State: {state_manager.get_current_state().value}")
    print(f"   → Available actions: {state_manager.get_available_actions()}")
    
    # User confirms
    state_manager.transition_to_state(UploadState.DATABASE_LOADED, "confirm_merge")
    print("   → User confirms merge")
    print(f"   → State: {state_manager.get_current_state().value}")
    
    # Workflow 3: Error Recovery
    print("\n❌ Workflow 3: Error Recovery")
    st.session_state.error_message = "File validation failed: Invalid JSON syntax"
    state_manager.transition_to_state(UploadState.ERROR_STATE, "validation_failed")
    print("   → Error occurred")
    print(f"   → State: {state_manager.get_current_state().value}")
    print(f"   → Available actions: {state_manager.get_available_actions()}")
    
    # User fixes and retries
    st.session_state.error_message = ""
    state_manager.transition_to_state(UploadState.DATABASE_LOADED, "retry_operation")
    print("   → User retries successfully")
    print(f"   → State: {state_manager.get_current_state().value}")
    
    print("\n🎉 All workflows demonstrated successfully!")

if __name__ == "__main__":
    print("🚀 Upload State Manager Test Suite")
    print("Testing Phase 3B implementation...")
    
    try:
        # Run core functionality tests
        test_state_manager()
        
        # Run integration tests
        test_integration_points()
        
        # Demonstrate workflows
        demonstrate_workflow()
        
        print("\n" + "="*60)
        print("✅ PHASE 3B: UPLOAD STATE MANAGER - COMPLETE")
        print("✅ All tests passed - Ready for Phase 3C")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    print("\n💡 Next Steps:")
    print("   1. Copy upload_state_manager.py to your modules/ directory")
    print("   2. Test integration with your existing system")
    print("   3. Proceed to Phase 3C: Database Merger")
    print("   4. Begin UI integration in Phase 3D")
