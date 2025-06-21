#!/usr/bin/env python3
"""
Comparison Test Script - Native vs Web App QTI Generation (CORRECTED)
This will help us identify exactly what's different between the two processing paths
"""

import json
import pandas as pd
import sys
import os
from datetime import datetime

# Add your modules path
sys.path.append('modules')

def load_test_json():
    """Load the controlled test JSON file"""
    
    test_json_content = {
        "questions": [
            {
                "id": "Q_00001",
                "type": "multiple_choice",
                "title": "Simple Circuit Analysis",
                "question_text": "For a resistor with $R = 100\\,\\Omega$ and current $I = 2\\,\\text{A}$, calculate the voltage using Ohm's law $V = IR$.",
                "choices": [
                    "$V = 200\\,\\text{V}$",
                    "$V = 50\\,\\text{V}$",
                    "$V = 100\\,\\text{V}$",
                    "$V = 300\\,\\text{V}$"
                ],
                "correct_answer": "$V = 200\\,\\text{V}$",
                "points": 2,
                "tolerance": 0.05,
                "feedback_correct": "Correct! Using Ohm's law: $V = IR = 2\\,\\text{A} \\times 100\\,\\Omega = 200\\,\\text{V}$",
                "feedback_incorrect": "Remember Ohm's law: $V = IR$. Calculate $V = 2 \\times 100 = 200\\,\\text{V}$",
                "image_file": [],
                "topic": "Circuit Analysis",
                "subtopic": "Ohm's Law",
                "difficulty": "Easy"
            },
            {
                "id": "Q_00002", 
                "type": "numerical",
                "title": "Frequency Calculation",
                "question_text": "Given angular frequency $\\omega = 628\\,\\text{rad/s}$, calculate the frequency in Hz using $f = \\frac{\\omega}{2\\pi}$.",
                "choices": [],
                "correct_answer": "100",
                "points": 3,
                "tolerance": 1,
                "feedback_correct": "Correct! $f = \\frac{\\omega}{2\\pi} = \\frac{628}{2\\pi} = \\frac{628}{6.283} \\approx 100\\,\\text{Hz}$",
                "feedback_incorrect": "Use the formula $f = \\frac{\\omega}{2\\pi}$ where $\\omega = 628\\,\\text{rad/s}$",
                "image_file": [],
                "topic": "Signal Processing",
                "subtopic": "Frequency Analysis", 
                "difficulty": "Medium"
            },
            {
                "id": "Q_00003",
                "type": "true_false", 
                "title": "Phase Relationship",
                "question_text": "For two sinusoids with phase difference $\\Delta\\phi = \\pi/2$ radians, one signal leads the other by exactly $90^\\circ$.",
                "choices": [
                    "True",
                    "False"
                ],
                "correct_answer": "True",
                "points": 1,
                "tolerance": 0.05,
                "feedback_correct": "Correct! $\\pi/2$ radians equals $90^\\circ$, indicating a quarter-cycle phase lead.",
                "feedback_incorrect": "Remember: $\\pi/2\\,\\text{rad} = 90^\\circ$. This represents a quarter-cycle phase difference.",
                "image_file": [],
                "topic": "Signal Processing",
                "subtopic": "Phase Analysis",
                "difficulty": "Medium"
            }
        ],
        "metadata": {
            "generated_by": "Controlled Test Generator",
            "generation_date": "2025-06-20",
            "format_version": "Phase Four LaTeX-Native",
            "total_questions": 3,
            "subject": "Electrical Engineering Test"
        }
    }
    
    return test_json_content

def fix_numeric_formatting(questions):
    """
    Ensure numeric values are formatted as integers when appropriate
    to match native QTI generation
    """
    
    for question in questions:
        # Fix points - convert float back to int if it's a whole number
        if 'points' in question:
            points = question['points']
            if isinstance(points, float) and points.is_integer():
                question['points'] = int(points)
        
        # Fix tolerance - similar logic
        if 'tolerance' in question:
            tolerance = question['tolerance']
            if isinstance(tolerance, float) and tolerance.is_integer():
                question['tolerance'] = int(tolerance)
                
        # Fix any other numeric fields that might have been converted to float
        numeric_fields = ['points', 'tolerance']
        for field in numeric_fields:
            if field in question:
                value = question[field]
                if isinstance(value, float) and value.is_integer():
                    question[field] = int(value)
    
    return questions

def fix_dataframe_dtypes(df):
    """
    Fix DataFrame column types to preserve integers
    """
    
    # Identify numeric columns that should be integers
    int_columns = ['Points', 'Question_Number']  # Add other integer columns
    
    for col in int_columns:
        if col in df.columns:
            # Convert float to int if all values are whole numbers
            if df[col].dtype == 'float64':
                if df[col].notna().all() and (df[col] % 1 == 0).all():
                    df[col] = df[col].astype('int64')
    
    return df

def generate_native_qti():
    """Generate QTI package using native/isolated approach (like our working test)"""
    
    print("🧪 GENERATING NATIVE QTI PACKAGE")
    print("=" * 50)
    
    try:
        # Import the clean exporter
        from exporter import CanvasLaTeXQTIGenerator
        
        # Load test data
        test_data = load_test_json()
        questions = test_data["questions"]
        
        print(f"📋 Loaded {len(questions)} test questions")
        
        # Generate QTI directly (native approach)
        generator = CanvasLaTeXQTIGenerator()
        qti_package = generator.create_qti_package(questions, "Native_Test")
        
        if qti_package:
            output_filename = f"native_qti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ Native QTI created: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            return output_filename, qti_package
        else:
            print("❌ Failed to create native QTI")
            return None, None
            
    except Exception as e:
        print(f"❌ Error in native QTI generation: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def simulate_webapp_processing():
    """Simulate the web app processing pipeline that might introduce differences"""
    
    print("\n🌐 SIMULATING WEB APP PROCESSING")
    print("=" * 50)
    
    try:
        # Load test data
        test_data = load_test_json()
        original_questions = test_data["questions"]
        
        print(f"📋 Starting with {len(original_questions)} original questions")
        
        # Step 1: Convert to DataFrame (like web app does)
        print("🔄 Step 1: Converting JSON to DataFrame...")
        df_data = []
        
        for i, q in enumerate(original_questions):
            row = {
                'ID': q.get('id', f"Q_{i+1:05d}"),
                'Title': q.get('title', ''),
                'Type': q.get('type', ''),
                'Question_Text': q.get('question_text', ''),
                'Points': q.get('points', 1),
                'Topic': q.get('topic', ''),
                'Subtopic': q.get('subtopic', ''),
                'Difficulty': q.get('difficulty', ''),
                'Correct_Answer': q.get('correct_answer', ''),
                'Tolerance': q.get('tolerance', 0.05)
            }
            
            # Add choices
            choices = q.get('choices', [])
            for j, choice in enumerate(choices):
                row[f'Choice_{chr(65+j)}'] = choice
                
            # Add feedback
            row['Correct_Feedback'] = q.get('feedback_correct', '')
            row['Incorrect_Feedback'] = q.get('feedback_incorrect', '')
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # NEW: Fix DataFrame data types
        df = fix_dataframe_dtypes(df)
        
        print(f"✅ DataFrame created: {len(df)} rows × {len(df.columns)} columns")
        
        # Step 2: Simulate web app filtering/processing
        print("🔄 Step 2: Simulating web app processing...")
        
        # Import web app exporter modules
        from exporter import filter_and_sync_questions, CanvasLaTeXQTIGenerator
        
        # Apply the same filtering logic as web app
        filtered_questions = filter_and_sync_questions(df, original_questions)
        
        # NEW: Fix numeric formatting in the filtered questions
        filtered_questions = fix_numeric_formatting(filtered_questions)
        
        print(f"✅ Filtered questions: {len(filtered_questions)}")
        
        # Step 3: Generate QTI using web app pipeline
        print("🔄 Step 3: Generating QTI via web app pipeline...")
        
        generator = CanvasLaTeXQTIGenerator()
        qti_package = generator.create_qti_package(filtered_questions, "Native_Test")
        
        if qti_package:
            output_filename = f"webapp_qti_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            with open(output_filename, 'wb') as f:
                f.write(qti_package)
            
            print(f"✅ Web app QTI created: {output_filename}")
            print(f"📊 Package size: {len(qti_package):,} bytes")
            return output_filename, qti_package, filtered_questions
        else:
            print("❌ Failed to create web app QTI")
            return None, None, None
            
    except Exception as e:
        print(f"❌ Error in web app simulation: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None, None

def compare_qti_packages(native_package, webapp_package):
    """Compare the two QTI packages to find differences"""
    
    print(f"\n🔍 COMPARING QTI PACKAGES")
    print("=" * 50)
    
    if not native_package or not webapp_package:
        print("❌ Cannot compare - one or both packages failed to generate")
        return
    
    print(f"📊 Package sizes:")
    print(f"  Native:  {len(native_package):,} bytes")
    print(f"  Web App: {len(webapp_package):,} bytes")
    
    if len(native_package) != len(webapp_package):
        print(f"⚠️  Size difference: {abs(len(native_package) - len(webapp_package))} bytes")
    else:
        print(f"✅ Identical package sizes")
    
    # Compare binary content
    if native_package == webapp_package:
        print(f"🎉 PACKAGES ARE IDENTICAL!")
        print(f"   This means the issue is NOT in our processing pipeline")
        print(f"   The Canvas '1 issues' is likely unrelated to our code")
    else:
        print(f"⚠️  PACKAGES ARE DIFFERENT")
        print(f"   This explains the Canvas import difference")
        print(f"   We need to analyze the XML content differences")
        
        # TODO: Add detailed XML comparison if needed
        print(f"\n💡 Recommendation: Import both packages to Canvas and compare results")

def run_comparison_test():
    """Run the complete comparison test"""
    
    print("🚀 STARTING QTI COMPARISON TEST")
    print("=" * 70)
    print(f"📅 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generate both packages
    native_file, native_package = generate_native_qti()
    webapp_file, webapp_package, filtered_questions = simulate_webapp_processing()
    
    # Compare results
    if native_package and webapp_package:
        compare_qti_packages(native_package, webapp_package)
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Import {native_file} into Canvas")
        print(f"2. Import {webapp_file} into Canvas") 
        print(f"3. Compare Canvas import results:")
        print(f"   - If BOTH show '1 issues': Problem is in our QTI generator")
        print(f"   - If NATIVE is clean: Problem is in web app processing")
        print(f"   - If BOTH are clean: Problem is specific to your real data")
        
        return native_file, webapp_file
    else:
        print(f"\n❌ Test failed - could not generate comparison packages")
        return None, None

if __name__ == "__main__":
    run_comparison_test()
