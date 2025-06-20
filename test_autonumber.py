#!/usr/bin/env python3
"""
Test auto-renumbering with real-world scenario that matches your Streamlit app
"""

import pandas as pd
import sys
import os

# Add modules directory to path
sys.path.append('modules')

try:
    from database_merger import DatabaseMerger, create_merge_preview, MergeStrategy
    print("[OK] Successfully imported database_merger")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

def test_real_world_scenario():
    """Test the scenario that matches your Streamlit app: 25 + 23 questions"""
    
    print("\nTesting Real-World Scenario: 25 + 23 Questions")
    print("=" * 60)
    
    # Create test data that matches your real scenario
    # 25 existing questions with IDs 0-24
    existing_data = []
    for i in range(25):
        existing_data.append({
            'id': str(i),
            'question_text': f'Existing question {i}',
            'correct_answer': 'A',
            'type': 'multiple_choice'
        })
    
    existing_df = pd.DataFrame(existing_data)
    
    # 23 new questions with IDs 0-22 (should conflict with existing 0-22)
    new_questions = []
    for i in range(23):
        new_questions.append({
            'id': str(i),
            'question_text': f'New question {i}',
            'correct_answer': 'B', 
            'type': 'multiple_choice'
        })
    
    print(f"Test Data (Real Scenario):")
    print(f"   Existing questions: {len(existing_df)} (IDs: 0-24)")
    print(f"   New questions: {len(new_questions)} (IDs: 0-22)")
    print(f"   Expected conflicts: 23 (IDs 0-22 overlap)")
    
    # Test 1: Direct merger instance
    print(f"\nTest 1: Direct DatabaseMerger Testing")
    merger = DatabaseMerger()
    
    # Test sequential conflict detection
    try:
        is_sequential = merger.detect_sequential_id_conflicts(existing_df, new_questions)
        print(f"   Sequential conflicts detected: {is_sequential}")
    except Exception as e:
        print(f"   [ERROR] Sequential detection failed: {e}")
        return
    
    # Test regular conflict detection
    try:
        conflicts_before = merger.conflict_detector.detect_conflicts(existing_df, new_questions)
        print(f"   Total conflicts detected: {len(conflicts_before)}")
        
        if conflicts_before:
            print(f"   First conflict type: {conflicts_before[0].conflict_type.value}")
            print(f"   First conflict details: {conflicts_before[0].conflict_details}")
    except Exception as e:
        print(f"   [ERROR] Conflict detection failed: {e}")
        return
    
    if is_sequential:
        try:
            # Test next available ID
            next_id = merger.get_next_available_id(existing_df)
            print(f"   Next available ID: {next_id}")
            
            # Test auto-renumbering
            renumbered_questions = merger.auto_renumber_questions(existing_df, new_questions)
            renumbered_ids = [q['id'] for q in renumbered_questions[:5]]  # Show first 5
            print(f"   Renumbered IDs (first 5): {renumbered_ids}")
            
            # Test conflicts after renumbering
            conflicts_after = merger.conflict_detector.detect_conflicts(existing_df, renumbered_questions)
            print(f"   Conflicts after renumbering: {len(conflicts_after)}")
            
        except Exception as e:
            print(f"   [ERROR] Auto-renumbering failed: {e}")
    else:
        print("   [WARNING] Sequential conflicts not detected - checking why...")
        
        # Debug the detection logic
        existing_ids = [int(row['id']) for _, row in existing_df.iterrows()]
        new_ids = [int(q['id']) for q in new_questions]
        
        print(f"   Existing IDs range: {min(existing_ids)}-{max(existing_ids)}")
        print(f"   New IDs range: {min(new_ids)}-{max(new_ids)}")
        
        overlapping_ids = set(existing_ids) & set(new_ids)
        print(f"   Overlapping IDs: {len(overlapping_ids)} (should be 23)")
        print(f"   First few overlaps: {sorted(list(overlapping_ids))[:10]}")
    
    # Test 2: Integration function
    print(f"\nTest 2: create_merge_preview with Real Data")
    try:
        preview = create_merge_preview(existing_df, new_questions, MergeStrategy.SKIP_DUPLICATES, auto_renumber=True)
        print(f"   Preview generated successfully")
        print(f"   Existing count: {preview.existing_count}")
        print(f"   New count: {preview.new_count}")
        print(f"   Final count: {preview.final_count}")
        print(f"   Total conflicts: {len(preview.conflicts)}")
        
        # Check if auto-renumbering info is in merge summary
        auto_renumbered = preview.merge_summary.get('auto_renumbered', False)
        print(f"   Auto-renumbered flag: {auto_renumbered}")
        
        if 'renumbering_info' in preview.merge_summary:
            renumbering_info = preview.merge_summary['renumbering_info']
            print(f"   Renumbering info: {renumbering_info}")
        
        # Show conflict details
        if preview.conflicts:
            print(f"   Sample conflicts:")
            for i, conflict in enumerate(preview.conflicts[:3]):  # Show first 3
                print(f"     {i+1}. {conflict.conflict_type.value}: {conflict.conflict_details}")
        else:
            print(f"   [GOOD] No conflicts after auto-renumbering")
    
    except Exception as e:
        print(f"   [ERROR] create_merge_preview failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nSUMMARY for Real-World Scenario:")
    print(f"  This test uses the same data pattern as your Streamlit app:")
    print(f"  - 25 existing questions (IDs 0-24)")
    print(f"  - 23 new questions (IDs 0-22)")
    print(f"  - Should detect 23 ID conflicts")
    print(f"  - Should auto-renumber new questions to IDs 25-47")
    print(f"  - Should result in 0 conflicts after renumbering")

if __name__ == "__main__":
    test_real_world_scenario()
