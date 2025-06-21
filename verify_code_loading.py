#!/usr/bin/env python3
"""
Verifikation ob unser neuer serialize_object Code überhaupt geladen wurde.
"""

import sys
from pathlib import Path
import numpy as np

# Add src to path
current_dir = Path.cwd()
if current_dir.name == 'tests':
    src_path = current_dir.parent / 'src'
else:
    src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))

def inspect_serialize_object_source():
    """Inspiziere den aktuellen Source Code von serialize_object."""
    print("🔍 INSPECT: serialize_object source code")
    print("=" * 50)
    
    try:
        from zarrcompatibility.type_handlers import serialize_object
        import inspect
        
        # Get source code
        source = inspect.getsource(serialize_object)
        print("Current serialize_object source code:")
        print("-" * 40)
        print(source)
        print("-" * 40)
        
        # Check for our fix markers
        if "Check NumPy types BEFORE basic types" in source:
            print("✅ NEW CODE: NumPy-first fix detected!")
        else:
            print("❌ OLD CODE: NumPy-first fix NOT detected!")
            
        if "hasattr(obj, '__module__')" in source:
            print("✅ MODULE CHECK: Found __module__ check")
        else:
            print("❌ MODULE CHECK: Missing __module__ check")
            
        # Check order
        lines = source.split('\n')
        numpy_check_line = None
        basic_types_line = None
        
        for i, line in enumerate(lines):
            if "__module__" in line and "numpy" in line:
                numpy_check_line = i
            if "isinstance(obj, (str, int, float, bool))" in line:
                basic_types_line = i
                
        print(f"\nCODE ORDER CHECK:")
        print(f"  NumPy check at line: {numpy_check_line}")
        print(f"  Basic types check at line: {basic_types_line}")
        
        if numpy_check_line is not None and basic_types_line is not None:
            if numpy_check_line < basic_types_line:
                print("✅ ORDER: NumPy check comes BEFORE basic types (correct)")
            else:
                print("❌ ORDER: NumPy check comes AFTER basic types (wrong!)")
        
    except Exception as e:
        print(f"❌ Error inspecting source: {e}")
        import traceback
        traceback.print_exc()

def test_direct_function_call():
    """Test den direkten Funktions-Aufruf mit Debug Prints."""
    print(f"\n🧪 TEST: Direct function call with debug")
    print("=" * 45)
    
    try:
        from zarrcompatibility.type_handlers import serialize_object
        
        # Add temporary debug to the function call
        test_input = np.float64(2.71)
        print(f"Input: {test_input!r}")
        print(f"Type: {type(test_input)}")
        
        # Manual condition checks
        print(f"\nCONDITION CHECKS:")
        
        # Check 1: NumPy module check
        has_module = hasattr(test_input, '__module__')
        module_name = getattr(type(test_input), '__module__', 'unknown')
        is_numpy = module_name.startswith('numpy')
        
        print(f"  hasattr(__module__): {has_module}")
        print(f"  type().__module__: {module_name}")
        print(f"  startswith('numpy'): {is_numpy}")
        
        # Check 2: Basic type check  
        is_basic = isinstance(test_input, (str, int, float, bool))
        print(f"  isinstance(basic types): {is_basic}")
        
        # What should happen
        print(f"\nEXPECTED EXECUTION PATH:")
        if is_numpy:
            print(f"  ✅ Should hit NumPy check first")
            if hasattr(test_input, 'item'):
                expected = test_input.item()
                print(f"  ✅ Should return: {expected!r} (type: {type(expected)})")
        
        # Actual call
        print(f"\nACTUAL EXECUTION:")
        result = serialize_object(test_input)
        print(f"  Result: {result!r}")
        print(f"  Type: {type(result)}")
        print(f"  Same object: {result is test_input}")
        
        if result is test_input:
            print(f"❌ PROBLEM: Function returned original object!")
            print(f"   This means our NumPy check was NOT executed")
        else:
            print(f"✅ SUCCESS: Function converted the object")
        
    except Exception as e:
        print(f"❌ Error in direct test: {e}")
        import traceback
        traceback.print_exc()

def check_file_modification_time():
    """Check wenn type_handlers.py zuletzt modifiziert wurde."""
    print(f"\n📅 FILE MODIFICATION CHECK:")
    print("=" * 35)
    
    try:
        type_handlers_path = src_path / 'zarrcompatibility' / 'type_handlers.py'
        
        if type_handlers_path.exists():
            import os
            import datetime
            
            mod_time = os.path.getmtime(type_handlers_path)
            mod_datetime = datetime.datetime.fromtimestamp(mod_time)
            
            print(f"type_handlers.py last modified: {mod_datetime}")
            
            # Check if it's recent (within last hour)
            now = datetime.datetime.now()
            time_diff = now - mod_datetime
            
            if time_diff.total_seconds() < 3600:  # 1 hour
                print(f"✅ Recently modified ({time_diff.total_seconds():.0f} seconds ago)")
            else:
                print(f"⚠️ Modified {time_diff} ago - might be stale")
        else:
            print(f"❌ type_handlers.py not found at {type_handlers_path}")
            
    except Exception as e:
        print(f"❌ Error checking file time: {e}")

def main():
    """Main verification function."""
    print("🔬 VERIFICATION: Is our new code actually loaded?")
    print("=" * 60)
    
    inspect_serialize_object_source()
    test_direct_function_call()
    check_file_modification_time()
    
    print(f"\n📊 DIAGNOSIS:")
    print("If the source inspection shows old code or wrong order,")
    print("then the file wasn't properly saved/reloaded.")
    print("If the source is correct but execution fails,")
    print("then there's a logic error in our conditions.")

if __name__ == "__main__":
    main()
