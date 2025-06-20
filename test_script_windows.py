#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from modules.file_processor import FileProcessor

def test_file(filename):
    print(f"Testing file: {filename}")
    print("=" * 50)
    
    # Mock uploaded file object
    class MockFile:
        def __init__(self, filepath):
            self.name = os.path.basename(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                self.content = f.read()
        
        def read(self):
            return self.content.encode('utf-8')
    
    try:
        # Test the processor
        processor = FileProcessor()
        mock_file = MockFile(filename)
        result = processor.process_file(mock_file)
        
        # Print results
        print(f"✅ File: {result.file_info['name']}")
        print(f"📁 Size: {result.file_info['size_mb']:.2f} MB")
        print(f"📊 Questions: {result.validation_result.question_count}")
        print(f"🔍 Format: {result.validation_result.format_detected.value}")
        print(f"✅ Valid: {result.validation_result.is_valid}")
        print(f"⏱️  Processing Time: {result.processing_time:.3f}s")
        print(f"⚠️  Total Issues: {len(result.validation_result.issues)}")
        
        # Show issues by level
        from collections import Counter
        issue_counts = Counter(issue.level.value for issue in result.validation_result.issues)
        for level, count in issue_counts.items():
            print(f"  {level.upper()}: {count}")
        
        # Show first few issues
        if result.validation_result.issues:
            print("\n📋 Issues Found:")
            for i, issue in enumerate(result.validation_result.issues[:5]):  # Show first 5
                print(f"  {i+1}. {issue.level.value.upper()}: {issue.message}")
                if issue.location:
                    print(f"     Location: {issue.location}")
                if issue.suggestion:
                    print(f"     Suggestion: {issue.suggestion}")
                print()
        
        # Show metadata if available
        if result.metadata:
            print("📋 Metadata Found:")
            for key, value in result.metadata.items():
                print(f"  {key}: {value}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Use raw string for Windows path
    test_file(r"debug tests\Phase Five\latex_questions_v1_part1.json")