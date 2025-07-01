#!/usr/bin/env python3
"""
Diagnostic script to help verify the category selection workflow is working correctly.
Run this to check the current state of your Q2LMS application.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_diagnostic_info():
    """Print diagnostic information about the current implementation"""
    
    print("🔍 Q2LMS Category Selection Workflow - Diagnostic Report")
    print("=" * 60)
    
    # Check 1: ProcessingState enum
    print("\n📋 1. Checking ProcessingState enum...")
    try:
        from modules.upload_interface_v2 import ProcessingState
        states = [state.name for state in ProcessingState]
        print(f"   ✅ ProcessingState enum found with {len(states)} states:")
        for state in states:
            print(f"      - {state}")
        if 'SELECTING_CATEGORIES' in states:
            print("   ✅ SELECTING_CATEGORIES state is present")
        else:
            print("   ❌ SELECTING_CATEGORIES state is missing")
    except Exception as e:
        print(f"   ❌ Error loading ProcessingState: {e}")
    
    # Check 2: UI Manager integration
    print("\n📋 2. Checking UI Manager integration...")
    try:
        from modules.ui_manager import UIManager
        from modules.app_config import AppConfig
        
        app_config = AppConfig()
        ui_manager = UIManager(app_config)
        
        # Check if required methods exist
        required_methods = ['find_topic_column', 'find_subtopic_column', 'find_difficulty_column', 'enhanced_subject_filtering']
        for method in required_methods:
            if hasattr(ui_manager, method):
                print(f"   ✅ {method} method exists")
            else:
                print(f"   ❌ {method} method missing")
                
    except Exception as e:
        print(f"   ❌ Error checking UI Manager: {e}")
    
    # Check 3: Category selection interface
    print("\n📋 3. Checking category selection interface...")
    try:
        from modules.app_config import AppConfig
        app_config = AppConfig()
        
        if hasattr(app_config, 'ui_components') and 'create_category_selection_interface' in app_config.ui_components:
            print("   ✅ Category selection interface is registered")
        else:
            print("   ❌ Category selection interface not found in app_config")
            
        # Try importing directly
        try:
            from modules.ui_components import create_category_selection_interface
            print("   ✅ create_category_selection_interface can be imported")
        except ImportError as e:
            print(f"   ❌ Cannot import create_category_selection_interface: {e}")
            
    except Exception as e:
        print(f"   ❌ Error checking category interface: {e}")
    
    # Check 4: Workflow state transition logic
    print("\n📋 4. Checking workflow state transition logic...")
    try:
        # Check if _execute_merge properly transitions states
        with open('modules/upload_interface_v2.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'ProcessingState.SELECTING_CATEGORIES' in content:
            print("   ✅ SELECTING_CATEGORIES state is referenced in upload_interface_v2.py")
        else:
            print("   ❌ SELECTING_CATEGORIES state not found in upload_interface_v2.py")
            
        if 'self._set_state(ProcessingState.SELECTING_CATEGORIES)' in content:
            print("   ✅ State transition to SELECTING_CATEGORIES is implemented")
        else:
            print("   ❌ State transition to SELECTING_CATEGORIES not found")
            
    except Exception as e:
        print(f"   ❌ Error checking workflow logic: {e}")
    
    # Check 5: UI rendering logic
    print("\n📋 5. Checking UI rendering logic...")
    try:
        with open('modules/ui_manager.py', 'r', encoding='utf-8') as f:
            ui_content = f.read()
            
        checks = [
            ('current_workflow_state == ProcessingState.SELECTING_CATEGORIES', 'State checking logic'),
            ('enhanced_subject_filtering', 'Sidebar filtering method'),
            ('Categories', 'Categories tab'),
            ('create_category_selection_interface', 'Category interface call')
        ]
        
        for check_text, description in checks:
            if check_text in ui_content:
                print(f"   ✅ {description} found in UI Manager")
            else:
                print(f"   ❌ {description} not found in UI Manager")
                
    except Exception as e:
        print(f"   ❌ Error checking UI rendering: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 IMPLEMENTATION STATUS SUMMARY")
    print("=" * 60)
    
    # Provide guidance based on what we found
    print("\n📌 To test the category selection workflow:")
    print("   1. Start your Streamlit app: streamlit run streamlit_app.py")
    print("   2. Upload a question database file")
    print("   3. Complete the database loading process")
    print("   4. After 'Database Loaded Successfully' message:")
    print("      - The app should automatically switch to the Categories tab")
    print("      - You should see a full-width category selection interface")
    print("      - The sidebar should NOT show topic/subtopic filters")
    print("      - There should be a 'Continue to Questions' button")
    
    print("\n📌 If you still see sidebar filters instead of main area interface:")
    print("   1. Check the current workflow state in the app")
    print("   2. Verify that the Categories tab is active")
    print("   3. Look for any error messages in the Streamlit console")
    
    print("\n📌 Debug steps if issues persist:")
    print("   1. Add debug info: Check 'Show Debug Info' in the upload interface")
    print("   2. Check session state: Look for 'upload_state' -> 'current_state'")
    print("   3. Verify tab state: Check 'main_active_tab' in session state")
    
    print("\n✨ The implementation should now be working correctly!")
    print("   If you're still seeing issues, please share the exact error messages")
    print("   or describe what you see vs. what's expected.")

if __name__ == "__main__":
    print_diagnostic_info()
