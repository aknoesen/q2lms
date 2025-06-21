#!/usr/bin/env python3
"""
Import Debugging Script
Systematically check what's causing the import issues
"""

import sys
import os
from pathlib import Path

def check_directory_structure():
    """Check the current directory structure"""
    print("🔍 DIRECTORY STRUCTURE CHECK")
    print("=" * 50)
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    modules_dir = current_dir / "modules"
    export_dir = modules_dir / "export"
    
    print(f"\nChecking modules directory: {modules_dir}")
    print(f"Exists: {modules_dir.exists()}")
    if modules_dir.exists():
        print(f"Contents: {list(modules_dir.iterdir())}")
    
    print(f"\nChecking export directory: {export_dir}")
    print(f"Exists: {export_dir.exists()}")
    if export_dir.exists():
        print(f"Contents: {list(export_dir.iterdir())}")
        
        # Check for __init__.py
        init_file = export_dir / "__init__.py"
        print(f"__init__.py exists: {init_file.exists()}")
        if init_file.exists():
            print(f"__init__.py size: {init_file.stat().st_size} bytes")

def check_python_path():
    """Check Python path configuration"""
    print("\n🐍 PYTHON PATH CHECK")
    print("=" * 50)
    
    print("sys.path contents:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # Check if modules directory is in path
    current_dir = str(Path.cwd())
    modules_path = str(Path.cwd() / "modules")
    
    print(f"\nCurrent directory in sys.path: {current_dir in sys.path}")
    print(f"Modules directory in sys.path: {modules_path in sys.path}")

def check_module_files():
    """Check each module file for syntax errors"""
    print("\n📄 MODULE FILE CHECK")
    print("=" * 50)
    
    export_dir = Path.cwd() / "modules" / "export"
    
    if not export_dir.exists():
        print("❌ Export directory does not exist!")
        return
    
    module_files = [
        "__init__.py",
        "data_processor.py", 
        "filename_utils.py",
        "latex_converter.py",
        "qti_generator.py",
        "canvas_adapter.py",
        "export_ui.py"
    ]
    
    for filename in module_files:
        filepath = export_dir / filename
        print(f"\nChecking {filename}:")
        print(f"  Exists: {filepath.exists()}")
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"  Size: {len(content)} characters")
                print(f"  Lines: {content.count(chr(10)) + 1}")
                
                # Try to compile the file
                try:
                    compile(content, str(filepath), 'exec')
                    print(f"  ✅ Syntax OK")
                except SyntaxError as e:
                    print(f"  ❌ Syntax Error: {e}")
                    print(f"     Line {e.lineno}: {e.text}")
                
            except Exception as e:
                print(f"  ❌ Error reading file: {e}")

def test_imports():
    """Test individual imports to isolate the problem"""
    print("\n🔧 IMPORT TESTING")
    print("=" * 50)
    
    # Add modules to path if not already there
    modules_path = str(Path.cwd() / "modules")
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)
        print(f"✅ Added {modules_path} to sys.path")
    
    # Test imports one by one
    imports_to_test = [
        ("modules", "import modules"),
        ("modules.export", "import modules.export"),
        ("modules.export.filename_utils", "import modules.export.filename_utils"),
        ("modules.export.data_processor", "import modules.export.data_processor"),
        ("modules.export.latex_converter", "import modules.export.latex_converter"),
        ("modules.export.qti_generator", "import modules.export.qti_generator"),
        ("modules.export.canvas_adapter", "import modules.export.canvas_adapter"),
        ("modules.export.export_ui", "import modules.export.export_ui"),
    ]
    
    for module_name, import_statement in imports_to_test:
        print(f"\nTesting: {import_statement}")
        try:
            exec(import_statement)
            print(f"  ✅ SUCCESS")
        except Exception as e:
            print(f"  ❌ FAILED: {type(e).__name__}: {e}")
            
            # If it's a syntax error, show more details
            if isinstance(e, SyntaxError):
                print(f"     File: {e.filename}")
                print(f"     Line {e.lineno}: {e.text}")

def check_existing_exporter():
    """Check if the current exporter.py exists and works"""
    print("\n📦 EXISTING EXPORTER CHECK")  
    print("=" * 50)
    
    exporter_file = Path.cwd() / "modules" / "exporter.py"
    print(f"exporter.py exists: {exporter_file.exists()}")
    
    if exporter_file.exists():
        try:
            with open(exporter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"Size: {len(content)} characters")
            
            # Check for syntax errors
            try:
                compile(content, str(exporter_file), 'exec')
                print("✅ Syntax OK")
            except SyntaxError as e:
                print(f"❌ Syntax Error in exporter.py: {e}")
                
        except Exception as e:
            print(f"❌ Error reading exporter.py: {e}")

def main():
    """Run all diagnostic checks"""
    print("🔧 SYSTEMATIC IMPORT DEBUGGING")
    print("=" * 70)
    
    check_directory_structure()
    check_python_path()
    check_module_files()
    check_existing_exporter()
    test_imports()
    
    print("\n" + "=" * 70)
    print("🎯 DEBUGGING COMPLETE")
    print("\nNext steps based on results:")
    print("1. Fix any syntax errors found")
    print("2. Ensure all __init__.py files exist")
    print("3. Check that modules are in correct locations")
    print("4. Verify import paths are correct")
    print("\nTo fix common issues:")
    print("• Run: touch modules/export/__init__.py")
    print("• Check file permissions")
    print("• Verify Python version compatibility")

if __name__ == "__main__":
    main()