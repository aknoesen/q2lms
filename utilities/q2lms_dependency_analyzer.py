#!/usr/bin/env python3
"""
Q2LMS Dependency Analyzer
Systematically analyze internal module dependencies and detect dead code
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
import json

class Q2LMSDependencyAnalyzer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.modules_dir = self.project_root / "modules"
        self.dependencies = {}
        self.reverse_dependencies = {}
        self.file_imports = {}
        self.dead_modules = set()
        
    def analyze_file_imports(self, file_path: Path) -> Set[str]:
        """Extract all module imports from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"⚠️ Error parsing {file_path}: {e}")
            return set()
        
        imports = set()
        
        # AST-based import detection
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('modules.'):
                        imports.add(alias.name.replace('modules.', ''))
                    elif '.' not in alias.name:  # Local module
                        imports.add(alias.name)
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module.startswith('modules.'):
                        imports.add(node.module.replace('modules.', ''))
                    elif node.module.startswith('.'):  # Relative import
                        # Handle relative imports
                        rel_module = node.module.lstrip('.')
                        if rel_module:
                            imports.add(rel_module)
        
        # Regex-based detection for dynamic imports
        dynamic_patterns = [
            r'from modules\.(\w+) import',
            r'import modules\.(\w+)',
            r'__import__\([\'"]modules\.(\w+)[\'"]',
            r'get_(\w+)_manager',  # Your specific pattern
            r'get_(\w+)_interface',  # Your specific pattern
            r'(\w+)Interface\(\)',  # Direct interface instantiation
        ]
        
        for pattern in dynamic_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    imports.update(match)
                else:
                    imports.add(match)
        
        return imports
    
    def analyze_string_references(self, file_path: Path) -> Set[str]:
        """Find module names referenced as strings (for dynamic imports)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
            return set()
        
        string_refs = set()
        
        # Look for module names in strings
        string_patterns = [
            r'[\'"](\w+_manager)[\'"]',
            r'[\'"](\w+_interface)[\'"]',
            r'[\'"](\w+_processor)[\'"]',
            r'[\'"](\w+_handler)[\'"]',
            r'[\'"](\w+_converter)[\'"]',
        ]
        
        for pattern in string_patterns:
            matches = re.findall(pattern, content)
            string_refs.update(matches)
        
        return string_refs
    
    def find_all_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        
        # Main files
        for file in self.project_root.glob("*.py"):
            python_files.append(file)
        
        # Module files
        if self.modules_dir.exists():
            for file in self.modules_dir.glob("*.py"):
                if file.name != "__init__.py":
                    python_files.append(file)
        
        return python_files
    
    def get_module_files(self) -> Dict[str, Path]:
        """Get mapping of module names to file paths"""
        module_files = {}
        
        if self.modules_dir.exists():
            for file in self.modules_dir.glob("*.py"):
                if file.name != "__init__.py":
                    module_name = file.stem
                    module_files[module_name] = file
        
        return module_files
    
    def analyze_dependencies(self):
        """Perform complete dependency analysis"""
        print("🔍 Analyzing Q2LMS Dependencies...")
        
        # Get all files
        python_files = self.find_all_python_files()
        module_files = self.get_module_files()
        
        print(f"📁 Found {len(python_files)} Python files")
        print(f"📦 Found {len(module_files)} module files")
        
        # Analyze each file
        for file_path in python_files:
            imports = self.analyze_file_imports(file_path)
            string_refs = self.analyze_string_references(file_path)
            all_refs = imports.union(string_refs)
            
            # Filter to only modules that exist
            valid_refs = {ref for ref in all_refs if ref in module_files}
            
            relative_path = file_path.relative_to(self.project_root)
            self.file_imports[str(relative_path)] = valid_refs
            
            if valid_refs:
                print(f"📄 {relative_path}: {', '.join(sorted(valid_refs))}")
        
        # Build reverse dependencies
        for file_path, imports in self.file_imports.items():
            for imported_module in imports:
                if imported_module not in self.reverse_dependencies:
                    self.reverse_dependencies[imported_module] = set()
                self.reverse_dependencies[imported_module].add(file_path)
        
        # Identify dead modules
        all_modules = set(module_files.keys())
        referenced_modules = set()
        for imports in self.file_imports.values():
            referenced_modules.update(imports)
        
        self.dead_modules = all_modules - referenced_modules
    
    def generate_report(self):
        """Generate comprehensive dependency report"""
        print("\n" + "="*60)
        print("📊 Q2LMS DEPENDENCY ANALYSIS REPORT")
        print("="*60)
        
        # Module usage summary
        module_files = self.get_module_files()
        total_modules = len(module_files)
        used_modules = total_modules - len(self.dead_modules)
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total modules: {total_modules}")
        print(f"  Used modules: {used_modules}")
        print(f"  Dead modules: {len(self.dead_modules)}")
        print(f"  Usage rate: {(used_modules/total_modules)*100:.1f}%")
        
        # Dead code detection
        if self.dead_modules:
            print(f"\n💀 DEAD MODULES (can potentially be removed):")
            for module in sorted(self.dead_modules):
                module_path = self.modules_dir / f"{module}.py"
                file_size = module_path.stat().st_size if module_path.exists() else 0
                print(f"  ❌ {module}.py ({file_size} bytes)")
        else:
            print(f"\n✅ NO DEAD MODULES DETECTED")
        
        # Dependency graph
        print(f"\n🔗 MODULE DEPENDENCIES:")
        for file_path, imports in sorted(self.file_imports.items()):
            if imports:
                print(f"  📄 {file_path}")
                for imported_module in sorted(imports):
                    print(f"    └── {imported_module}")
        
        # Reverse dependencies (what depends on each module)
        print(f"\n📦 MODULE USAGE (reverse dependencies):")
        for module in sorted(self.reverse_dependencies.keys()):
            dependents = self.reverse_dependencies[module]
            print(f"  🔧 {module} (used by {len(dependents)} files):")
            for dependent in sorted(dependents):
                print(f"    └── {dependent}")
        
        # Critical modules (used by many files)
        if self.reverse_dependencies:
            critical_threshold = 2
            critical_modules = {
                module: deps for module, deps in self.reverse_dependencies.items() 
                if len(deps) >= critical_threshold
            }
            
            if critical_modules:
                print(f"\n⚠️ CRITICAL MODULES (used by {critical_threshold}+ files):")
                for module, deps in sorted(critical_modules.items(), 
                                         key=lambda x: len(x[1]), reverse=True):
                    print(f"  🎯 {module} (used by {len(deps)} files)")
    
    def save_report(self, output_file: str = "dependency_report.json"):
        """Save detailed report to JSON file"""
        report_data = {
            "analysis_date": str(Path.cwd()),
            "total_modules": len(self.get_module_files()),
            "used_modules": len(self.get_module_files()) - len(self.dead_modules),
            "dead_modules": list(self.dead_modules),
            "file_imports": {file: list(imports) for file, imports in self.file_imports.items()},
            "reverse_dependencies": {
                module: list(deps) for module, deps in self.reverse_dependencies.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {output_file}")
    
    def suggest_cleanup(self):
        """Suggest specific cleanup actions"""
        print(f"\n🧹 CLEANUP SUGGESTIONS:")
        
        if self.dead_modules:
            print(f"\n1. REMOVE DEAD MODULES:")
            for module in sorted(self.dead_modules):
                print(f"   rm modules/{module}.py")
        
        # Look for modules with no reverse dependencies (except from main app)
        orphaned = []
        for module in self.get_module_files().keys():
            if module not in self.reverse_dependencies:
                orphaned.append(module)
            elif len(self.reverse_dependencies[module]) == 1:
                # Only used by one file
                single_user = list(self.reverse_dependencies[module])[0]
                if single_user == "streamlit_app.py":
                    continue  # Main app usage is fine
                orphaned.append(f"{module} (only used by {single_user})")
        
        if orphaned:
            print(f"\n2. REVIEW ORPHANED MODULES:")
            for module in orphaned:
                print(f"   🤔 {module}")
        
        # Suggest consolidation opportunities
        small_modules = []
        for module, path in self.get_module_files().items():
            if path.stat().st_size < 1000:  # Less than 1KB
                small_modules.append(f"{module} ({path.stat().st_size} bytes)")
        
        if small_modules:
            print(f"\n3. CONSIDER CONSOLIDATING SMALL MODULES:")
            for module in small_modules:
                print(f"   📏 {module}")

def main():
    """Run the Q2LMS dependency analysis"""
    analyzer = Q2LMSDependencyAnalyzer()
    analyzer.analyze_dependencies()
    analyzer.generate_report()
    analyzer.suggest_cleanup()
    analyzer.save_report()

if __name__ == "__main__":
    main()
