echo import sys > test_basic_fixed.py
echo import os >> test_basic_fixed.py
echo sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..')) >> test_basic_fixed.py
echo from modules.latex_processor import clean_text >> test_basic_fixed.py
echo result = clean_text("Test with 50Omega resistor") >> test_basic_fixed.py
echo print(result) >> test_basic_fixed.py
echo print("LaTeX processor working!") >> test_basic_fixed.py
from modules.latex_processor import clean_text
result = clean_text("Test with 50Ω resistor")
print(result)
print("✅ LaTeX processor working!")