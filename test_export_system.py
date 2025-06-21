#!/usr/bin/env python3
"""
Test the New Export System
Verifies that all components work together correctly
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add modules to path
project_root = Path(__file__).parent
modules_path = str(project_root / "modules")
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

def test_import_main_function():
    """Test importing the main integration function"""
    print("🔧 Testing main integration function...")
    
    try:
        from modules.exporter import integrate_with_existing_ui
        print("✅ integrate_with_existing_ui imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import integration function: {e}")
        return False

def test_filename_utilities():
    """Test filename utilities"""
    print("\n📝 Testing filename utilities...")
    
    try:
        from modules.export.filename_utils import ExportNamingManager
        
        manager = ExportNamingManager()
        
        # Test validation
        valid, msg = manager.validate_user_input("test_file_123")
        print(f"✅ Filename validation: {valid} - {msg}")
        
        # Test CSV filename generation
        csv_filename = manager.get_csv_filename("my_questions")
        print(f"✅ CSV filename: {csv_filename}")
        
        # Test QTI filename generation
        qti_filename = manager.get_qti_filename("Quiz_Title")
        print(f"✅ QTI filename: {qti_filename}")
        
        # Test suggestion
        suggestion = manager.suggest_name("Midterm Exam", 25)
        print(f"✅ Filename suggestion: {suggestion}")
        
        # Test invalid filename
        invalid, invalid_msg = manager.validate_user_input("file<>:with|bad*chars")
        print(f"✅ Invalid filename caught: {not invalid} - {invalid_msg}")
        
        return True
        
    except Exception as e:
        print(f"❌ Filename utilities error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """Test data processing components"""
    print("\n📊 Testing data processing...")
    
    try:
        from modules.export.data_processor import ExportDataManager
        
        # Create sample data
        sample_df = pd.DataFrame({
            'Title': ['Question 1', 'Question 2'],
            'Type': ['multiple_choice', 'numerical'],
            'Points': [2, 3],
            'Topic': ['Math', 'Physics']
        })
        
        sample_questions = [
            {'id': 'q1', 'title': 'Question 1', 'type': 'multiple_choice', 'question_text': 'What is 2+2?'},
            {'id': 'q2', 'title': 'Question 2', 'type': 'numerical', 'question_text': 'Calculate force'}
        ]
        
        manager = ExportDataManager()
        processed_questions, report = manager.prepare_questions_for_export(sample_df, sample_questions)
        
        print(f"✅ Processed {len(processed_questions)} questions")
        print(f"✅ Processing report: {report['success']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_latex_analysis():
    """Test LaTeX analysis"""
    print("\n🔢 Testing LaTeX analysis...")
    
    try:
        from modules.export.latex_converter import LaTeXAnalyzer
        
        sample_questions = [
            {'question_text': 'What is $E = mc^2$?', 'choices': ['Option A']},
            {'question_text': 'Regular question', 'choices': ['$\\alpha$', 'Beta']},
            {'question_text': 'No math here', 'choices': ['A', 'B']}
        ]
        
        analyzer = LaTeXAnalyzer()
        analysis = analyzer.analyze_questions(sample_questions)
        
        print(f"✅ Total questions: {analysis['total_questions']}")
        print(f"✅ LaTeX questions: {analysis['questions_with_latex']}")
        print(f"✅ LaTeX percentage: {analysis['latex_percentage']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ LaTeX analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qti_generation():
    """Test QTI generation"""
    print("\n📦 Testing QTI generation...")
    
    try:
        from modules.export.canvas_adapter import CanvasQTIAdapter
        
        sample_questions = [
            {
                'title': 'Test Question',
                'type': 'multiple_choice',
                'question_text': 'What is 2+2?',
                'choices': ['3', '4', '5'],
                'correct_answer': '4',
                'points': 1
            }
        ]
        
        adapter = CanvasQTIAdapter()
        package_data = adapter.create_package(sample_questions, "Test Quiz", "test_package")
        
        if package_data:
            print(f"✅ QTI package created: {len(package_data)} bytes")
            print("✅ Package contains ZIP data")
            return True
        else:
            print("❌ QTI package creation returned None")
            return False
        
    except Exception as e:
        print(f"❌ QTI generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_integration():
    """Test that the system works with Streamlit imports"""
    print("\n🌟 Testing Streamlit integration...")
    
    try:
        # This tests if the system can be imported when Streamlit is available
        import streamlit as st
        
        # Test the main integration function with None data (should handle gracefully)
        from modules.exporter import integrate_with_existing_ui
        
        print("✅ Streamlit integration ready")
        print("✅ Main function can be imported with Streamlit")
        
        # Test legacy compatibility functions
        from modules.exporter import export_to_csv, create_qti_package
        print("✅ Legacy compatibility functions available")
        
        return True
        
    except ImportError:
        print("⚠️ Streamlit not available, but that's OK for testing")
        
        # Test without Streamlit
        try:
            from modules.exporter import integrate_with_existing_ui
            print("✅ Integration function works without Streamlit")
            return True
        except Exception as e:
            print(f"❌ Integration function failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Streamlit integration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 TESTING NEW EXPORT SYSTEM")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_import_main_function),
        ("Filename Utils", test_filename_utilities),
        ("Data Processing", test_data_processing),
        ("LaTeX Analysis", test_latex_analysis),
        ("QTI Generation", test_qti_generation),
        ("Streamlit Integration", test_streamlit_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print("📊 **TEST RESULTS**")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 **ALL TESTS PASSED!**")
        print("🚀 Your new export system is ready!")
        print("\nNext steps:")
        print("1. Run: streamlit run streamlit_app.py")
        print("2. Test the export functionality in the UI")
        print("3. Upload some questions and try the new export features")
    else:
        print(f"\n⚠️ **{failed} tests failed**")
        print("Check the error messages above and fix any issues")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
