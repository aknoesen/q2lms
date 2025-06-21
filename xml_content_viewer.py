#!/usr/bin/env python3
"""
QTI XML Content Viewer
Look at the actual XML content to see what's wrong
"""

import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

def view_qti_xml_content(zip_filename):
    """View the actual XML content of a QTI package"""
    
    print(f"🔍 EXAMINING: {zip_filename}")
    print("=" * 60)
    
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            # List all files
            print(f"📂 Files in package:")
            for filename in zipf.namelist():
                info = zipf.getinfo(filename)
                print(f"   📄 {filename}: {info.file_size} bytes")
            
            # Find and display main XML content
            xml_files = [f for f in zipf.namelist() if f.endswith('.xml') and not f.startswith('ims')]
            
            if xml_files:
                main_xml = xml_files[0]
                print(f"\n📄 MAIN XML CONTENT ({main_xml}):")
                print("-" * 40)
                
                xml_content = zipf.read(main_xml).decode('utf-8')
                
                # Pretty print the XML
                try:
                    parsed = minidom.parseString(xml_content)
                    pretty_xml = parsed.toprettyxml(indent="  ")
                    print(pretty_xml)
                except Exception as e:
                    print(f"❌ XML parsing error: {e}")
                    print(f"📝 Raw XML content:")
                    print(xml_content)
            
            # Also show manifest
            if 'imsmanifest.xml' in zipf.namelist():
                print(f"\n📄 MANIFEST CONTENT:")
                print("-" * 40)
                manifest_content = zipf.read('imsmanifest.xml').decode('utf-8')
                try:
                    parsed = minidom.parseString(manifest_content)
                    pretty_manifest = parsed.toprettyxml(indent="  ")
                    print(pretty_manifest)
                except Exception as e:
                    print(f"❌ Manifest parsing error: {e}")
                    print(manifest_content)
    
    except Exception as e:
        print(f"❌ Error examining package: {e}")
        import traceback
        print(traceback.format_exc())

def check_xml_validity(zip_filename):
    """Check if the XML is valid and well-formed"""
    
    print(f"\n🔬 XML VALIDITY CHECK: {zip_filename}")
    print("=" * 60)
    
    try:
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            xml_files = [f for f in zipf.namelist() if f.endswith('.xml')]
            
            for xml_file in xml_files:
                print(f"\n📄 Checking: {xml_file}")
                xml_content = zipf.read(xml_file).decode('utf-8')
                
                try:
                    # Parse with ElementTree
                    root = ET.fromstring(xml_content)
                    print(f"   ✅ Valid XML structure")
                    print(f"   📋 Root element: {root.tag}")
                    print(f"   📋 Root attributes: {root.attrib}")
                    
                    # Count elements by type
                    all_elements = root.findall('.//*')
                    element_counts = {}
                    for elem in all_elements:
                        tag = elem.tag.split('}')[-1]  # Remove namespace
                        element_counts[tag] = element_counts.get(tag, 0) + 1
                    
                    print(f"   📊 Element counts:")
                    for tag, count in sorted(element_counts.items()):
                        if count > 0:
                            print(f"      {tag}: {count}")
                
                except ET.ParseError as e:
                    print(f"   ❌ XML Parse Error: {e}")
                    print(f"   📝 First 200 chars: {xml_content[:200]}")
                
                except Exception as e:
                    print(f"   ❌ Other error: {e}")
    
    except Exception as e:
        print(f"❌ Error checking validity: {e}")

def main():
    """Check all the generated QTI packages"""
    
    import glob
    import os
    
    print("🚀 QTI XML CONTENT EXAMINATION")
    print("=" * 80)
    
    # Find the latest generated files
    qti_files = []
    for pattern in ['minimal_test_*.zip', 'latex_test_*.zip', 'controlled_test_*.zip']:
        files = glob.glob(pattern)
        if files:
            latest = max(files, key=os.path.getctime)
            qti_files.append(latest)
    
    if not qti_files:
        print("❌ No QTI files found. Run canvas_compatibility_tester.py first.")
        return
    
    for qti_file in qti_files:
        view_qti_xml_content(qti_file)
        check_xml_validity(qti_file)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
