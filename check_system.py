"""
Windows-compatible system check (no emojis)
Run this to check your current system status
"""

import os
from pathlib import Path

def check_system_status():
    """Check the current status of your Phase 3 system"""
    
    project_root = Path(".")  # Current directory
    modules_dir = project_root / "modules"
    
    print("SYSTEM STATUS CHECK")
    print("=" * 50)
    
    # Check required files
    required_files = {
        "Phase 3A": "modules/file_processor_module.py",
        "Phase 3B": "modules/upload_state_manager.py", 
        "Phase 3C": "modules/database_merger.py",
        "Phase 3D": "modules/upload_interface_v2.py",
        "Main App": "streamlit_app.py"
    }
    
    all_present = True
    for phase, file_path in required_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"[OK] {phase}: {file_path} ({size_kb:.1f} KB)")
        else:
            print(f"[MISSING] {phase}: {file_path}")
            all_present = False
    
    # Check for backup files
    print(f"\nBACKUP FILES:")
    backup_files = [
        "modules/upload_handler_backup.py",
        "streamlit_app_backup.py"
    ]
    
    for backup_file in backup_files:
        full_path = project_root / backup_file
        if full_path.exists():
            print(f"[OK] Backup: {backup_file}")
        else:
            print(f"[NONE] No backup: {backup_file}")
    
    # Test file check
    test_paths = [
        "debug tests/Phase Five/latex_questions_v1_part1.json",
        "debug tests\\Phase Five\\latex_questions_v1_part1.json",  # Windows path
    ]
    
    test_file_found = False
    for test_path in test_paths:
        test_file = project_root / test_path
        if test_file.exists():
            print(f"[OK] Test file: {test_file}")
            test_file_found = True
            break
    
    if not test_file_found:
        print(f"[MISSING] Test file not found")
    
    print(f"\nSYSTEM ASSESSMENT:")
    if all_present:
        print("[OK] All required Phase 3 files present")
        print("[OK] Ready for auto-renumbering implementation")
        return True
    else:
        print("[ERROR] Missing required files")
        print("[ERROR] Need to restore from backups or re-implement")
        return False

def test_imports():
    """Test if Phase 3 modules can be imported"""
    print(f"\nIMPORT TESTS:")
    
    tests = [
        ("Phase 3A", "from modules.file_processor_module import FileProcessor"),
        ("Phase 3B", "from modules.upload_state_manager import UploadState"),
        ("Phase 3C", "from modules.database_merger import DatabaseMerger"),
    ]
    
    for phase, import_cmd in tests:
        try:
            exec(import_cmd)
            print(f"[OK] {phase} imports successfully")
        except ImportError as e:
            print(f"[ERROR] {phase} import failed: {e}")
        except Exception as e:
            print(f"[ERROR] {phase} error: {e}")

def simple_manual_steps():
    """Manual steps for verification"""
    print("\nMANUAL VERIFICATION STEPS:")
    print("1. Run: streamlit run streamlit_app.py")
    print("2. Test upload with test file")
    print("3. Test append operation (should show conflicts)")
    print("4. If working -> proceed with auto-renumbering")
    print("5. If broken -> check git status or restore backups")
    
    print("\nQUICK TEST COMMANDS:")
    print("git status")
    print("git log --oneline -5")
    print("streamlit run streamlit_app.py")

if __name__ == "__main__":
    system_ok = check_system_status()
    test_imports()
    simple_manual_steps()
    
    if system_ok:
        print("\nNEXT STEP: Test your system with Streamlit")
    else:
        print("\nNEXT STEP: Restore missing files first")
