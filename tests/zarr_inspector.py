#!/usr/bin/env python3
"""
Zarr v3 API Inspector - Find the actual JSON functions and structure.

This script explores the Zarr v3 installation to understand its actual structure
and locate the JSON serialization functions we need to patch.
"""

import sys
from pathlib import Path

# Setup path
current_dir = Path.cwd()
if current_dir.name == 'tests':
    src_path = current_dir.parent / 'src'
else:
    src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))


def explore_module(module, name, max_depth=2, current_depth=0):
    """Recursively explore a module's structure."""
    if current_depth >= max_depth:
        return
    
    indent = "  " * current_depth
    print(f"{indent}📦 {name}")
    
    try:
        for attr_name in sorted(dir(module)):
            if attr_name.startswith('_'):
                continue
                
            try:
                attr = getattr(module, attr_name)
                attr_type = type(attr).__name__
                
                if hasattr(attr, '__module__') and attr.__module__ and 'zarr' in attr.__module__:
                    if callable(attr):
                        print(f"{indent}  🔧 {attr_name}() - {attr_type}")
                    elif attr_type == 'module':
                        print(f"{indent}  📁 {attr_name} - {attr_type}")
                        if current_depth < max_depth - 1:
                            explore_module(attr, f"{name}.{attr_name}", max_depth, current_depth + 1)
                    else:
                        print(f"{indent}  📄 {attr_name} - {attr_type}")
            except Exception as e:
                print(f"{indent}  ❌ {attr_name} - Error: {e}")
    except Exception as e:
        print(f"{indent}❌ Cannot explore {name}: {e}")


def find_json_functions():
    """Search for JSON-related functions in Zarr."""
    import zarr
    
    print("🔍 Searching for JSON functions in Zarr...")
    
    # Common places where JSON functions might be
    search_paths = [
        ('zarr', zarr),
        ('zarr.util', None),
        ('zarr._util', None),
        ('zarr.core', None),
        ('zarr.core.util', None),
        ('zarr.storage', None),
        ('zarr.meta', None),
        ('zarr.metadata', None),
        ('zarr.abc', None)
    ]
    
    found_json_functions = []
    
    for path_name, module in search_paths:
        try:
            if module is None:
                # Try to import the module
                parts = path_name.split('.')
                current = zarr
                for part in parts[1:]:  # Skip 'zarr'
                    current = getattr(current, part)
                module = current
            
            print(f"\n✅ Found module: {path_name}")
            
            # Look for JSON-related attributes
            for attr_name in dir(module):
                if 'json' in attr_name.lower():
                    attr = getattr(module, attr_name)
                    if callable(attr):
                        found_json_functions.append(f"{path_name}.{attr_name}")
                        print(f"  🔧 {attr_name}() - {type(attr).__name__}")
                    else:
                        print(f"  📄 {attr_name} - {type(attr).__name__}")
                        
        except Exception as e:
            print(f"❌ Cannot access {path_name}: {e}")
    
    return found_json_functions


def inspect_zarr_storage():
    """Inspect Zarr storage and serialization."""
    import zarr
    
    print("\n🔍 Inspecting Zarr storage and serialization...")
    
    try:
        # Try to create a simple array and see what happens
        print("\n📝 Testing basic Zarr operations...")
        
        store = zarr.storage.MemoryStore()
        arr = zarr.create_array(store=store, shape=(10,), dtype='i4')
        
        print("✅ Basic array creation works")
        
        # Try to access metadata
        print(f"📊 Array info: shape={arr.shape}, dtype={arr.dtype}")
        
        # Check what happens with attributes
        arr.attrs['test'] = {'key': 'value'}
        print(f"📝 Stored attribute: {arr.attrs['test']}")
        
        # Try to access the underlying storage
        print("\n🔍 Examining storage...")
        print(f"📦 Store type: {type(store)}")
        print(f"📁 Store contents: {list(store.keys()) if hasattr(store, 'keys') else 'No keys method'}")
        
    except Exception as e:
        print(f"❌ Error during basic operations: {e}")
        import traceback
        traceback.print_exc()


def check_zarr_internals():
    """Check Zarr internal structure for metadata handling."""
    import zarr
    
    print("\n🔍 Checking Zarr internals...")
    
    # Look for metadata-related modules
    metadata_paths = [
        'zarr.core.metadata',
        'zarr.core.metadata.v3',
        'zarr.metadata',
        'zarr.meta'
    ]
    
    for path in metadata_paths:
        try:
            parts = path.split('.')
            current = zarr
            for part in parts[1:]:
                current = getattr(current, part)
            
            print(f"✅ Found: {path}")
            
            # Look for relevant classes/functions
            for attr_name in dir(current):
                if not attr_name.startswith('_'):
                    attr = getattr(current, attr_name)
                    if hasattr(attr, '__name__'):
                        print(f"  📦 {attr_name} - {type(attr).__name__}")
                        
        except Exception as e:
            print(f"❌ Cannot access {path}: {e}")


def main():
    """Main inspection function."""
    print("🔍 Zarr v3.0.8 API Inspector")
    print("=" * 50)
    
    try:
        import zarr
        print(f"✅ Zarr v{zarr.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import Zarr: {e}")
        return 1
    
    # Basic module exploration
    print(f"\n📦 Zarr module structure:")
    explore_module(zarr, "zarr", max_depth=2)
    
    # Search for JSON functions
    json_functions = find_json_functions()
    
    if json_functions:
        print(f"\n✅ Found JSON functions:")
        for func in json_functions:
            print(f"  - {func}")
    else:
        print(f"\n❌ No JSON functions found!")
    
    # Inspect storage
    inspect_zarr_storage()
    
    # Check internals
    check_zarr_internals()
    
    print(f"\n📋 Summary:")
    print(f"   Zarr version: {zarr.__version__}")
    print(f"   JSON functions found: {len(json_functions)}")
    print(f"   zarr.util exists: {'✅' if hasattr(zarr, 'util') else '❌'}")
    
    # Provide recommendations
    print(f"\n💡 Next steps:")
    if not hasattr(zarr, 'util'):
        print("   1. Zarr v3 has different API structure")
        print("   2. Need to find alternative JSON handling approach")
        print("   3. May need to patch at different level (storage/metadata)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())