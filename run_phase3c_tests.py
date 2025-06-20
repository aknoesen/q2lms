#!/usr/bin/env python3
"""
Phase 3C Test Runner
Simple script to run all Phase 3C tests in the correct order
"""

import sys
import os
import subprocess

def run_test_file(filename):
    """Run a test file and return success status"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {filename}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, filename], 
                              capture_output=False, 
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {filename}: {e}")
        return False

def main():
    print("Phase 3C Database Merger - Test Suite Runner")
    print("=" * 60)
    
    # List of test files to run in order
    test_files = [
        "test_phase3c.py",
        "integration_example.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nFound test file: {test_file}")
            success = run_test_file(test_file)
            results[test_file] = success
        else:
            print(f"\nTest file not found: {test_file}")
            results[test_file] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_files)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_file, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{test_file:<30} {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Phase 3C is ready for integration.")
        return 0
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())