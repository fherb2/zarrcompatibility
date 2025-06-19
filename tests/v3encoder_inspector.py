#!/usr/bin/env python3
"""
V3JsonEncoder Inspector - Understand how Zarr v3 actually handles JSON.

This will show us exactly what we need to patch and how.
"""

import sys
import json
from pathlib import Path

# Setup path
current_dir = Path.cwd()
if current_dir.name == 'tests':
    src_path = current_dir.parent / 'src'
else:
    src_path = current_dir / 'src'
sys.path.insert(0, str(src_path))


def inspect_v3_json_encoder():
    """Inspect the V3JsonEncoder class in detail."""
    print("🔍 Inspecting V3JsonEncoder...")
    
    try:
        from zarr.core.metadata.v3 import V3JsonEncoder
        print("✅ V3JsonEncoder imported successfully")
        
        # Check class structure
        print(f"📦 V3JsonEncoder type: {type(V3JsonEncoder)}")
        print(f"📦 V3JsonEncoder MRO: {V3JsonEncoder.__mro__}")
        
        # Check methods
        print(f"\n🔧 V3JsonEncoder methods:")
        for method_name in sorted(dir(V3JsonEncoder)):
            if not method_name.startswith('_') or method_name in ['__init__', '__call__']:
                method = getattr(V3JsonEncoder, method_name)
                if callable(method):
                    print(f"  🔧 {method_name}() - {type(method).__name__}")
        
        # Test basic usage
        print(f"\n🧪 Testing V3JsonEncoder...")
        encoder = V3JsonEncoder()
        
        # Test with simple data
        test_data = {"key": "value", "number": 42}
        encoded = encoder.encode(test_data)
        print(f"📝 Simple encode test: {encoded}")
        
        # Test with tuple (this should fail/convert to list)
        test_tuple = {"tuple_data": (1, 2, 3)}
        encoded_tuple = encoder.encode(test_tuple)
        print(f"📝 Tuple encode test: {encoded_tuple}")
        
        return encoder
        
    except Exception as e:
        print(f"❌ Failed to inspect V3JsonEncoder: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_zarr_json_flow():
    """Test the actual JSON flow in Zarr operations."""
    print(f"\n🔍 Testing actual Zarr JSON flow...")
    
    try:
        import zarr
        
        # Create array with metadata
        store = zarr.storage.MemoryStore()
        arr = zarr.create_array(store=store, shape=(5,), dtype='i4')
        
        # Add tuple attribute (this will show us where conversion happens)
        test_tuple = (1, 2, 3)
        arr.attrs['version'] = test_tuple
        
        print(f"📝 Stored: {test_tuple} (type: {type(test_tuple)})")
        
        # Reload and check what happened
        reloaded_arr = zarr.open_array(store=store, mode='r')
        result = reloaded_arr.attrs['version']
        
        print(f"📖 Retrieved: {result} (type: {type(result)})")
        
        if isinstance(result, tuple):
            print("✅ Tuple preserved! (unexpected)")
        else:
            print("❌ Tuple converted to list (expected without our patch)")
        
        # Check what's actually stored in the store
        print(f"\n🔍 Raw storage contents:")
        for key in store:
            try:
                raw_data = store[key]
                if isinstance(raw_data, bytes):
                    try:
                        decoded = raw_data.decode('utf-8')
                        if decoded.startswith('{'):
                            parsed = json.loads(decoded)
                            print(f"📄 {key}: {parsed}")
                        else:
                            print(f"📄 {key}: {decoded[:100]}...")
                    except:
                        print(f"📄 {key}: <binary data {len(raw_data)} bytes>")
                else:
                    print(f"📄 {key}: {raw_data}")
            except Exception as e:
                print(f"📄 {key}: <error reading: {e}>")
        
    except Exception as e:
        print(f"❌ Error testing Zarr JSON flow: {e}")
        import traceback
        traceback.print_exc()


def find_json_usage_in_zarr():
    """Find where JSON encoding is actually used in Zarr."""
    print(f"\n🔍 Finding JSON usage in Zarr metadata...")
    
    try:
        import zarr.core.metadata.v3 as v3meta
        
        # Check if there are any direct json.dumps calls
        import inspect
        
        for name, obj in inspect.getmembers(v3meta):
            if inspect.isclass(obj) or inspect.isfunction(obj):
                try:
                    source = inspect.getsource(obj)
                    if 'json' in source.lower() and ('dumps' in source or 'encode' in source):
                        print(f"🎯 Found JSON usage in {name}")
                        # Show relevant lines
                        lines = source.split('\n')
                        for i, line in enumerate(lines):
                            if 'json' in line.lower() and ('dumps' in line or 'encode' in line):
                                print(f"  Line {i}: {line.strip()}")
                except Exception:
                    pass
        
    except Exception as e:
        print(f"❌ Error finding JSON usage: {e}")


def main():
    """Main inspection function."""
    print("🔬 V3JsonEncoder Deep Dive")
    print("=" * 40)
    
    # Step 1: Inspect the encoder class
    encoder = inspect_v3_json_encoder()
    
    # Step 2: Test actual Zarr JSON flow
    test_zarr_json_flow()
    
    # Step 3: Find where JSON is used
    find_json_usage_in_zarr()
    
    print(f"\n💡 Key Findings:")
    print(f"   1. V3JsonEncoder exists: {'✅' if encoder else '❌'}")
    print(f"   2. Current behavior: Tuples → Lists (standard JSON)")
    print(f"   3. Need to patch: V3JsonEncoder.encode() method")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Patch V3JsonEncoder to use our type handlers")
    print(f"   2. Test tuple preservation works")
    print(f"   3. Verify no side effects on global JSON")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())