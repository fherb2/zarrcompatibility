"""
Zarr-specific patching functions for zarrcompatibility.

FIXED VERSION - Now correctly patches GroupMetadata.to_buffer_dict 
where the actual JSON serialization happens.

This module contains the core patching logic that modifies Zarr's internal
JSON serialization methods to support additional Python types. This version
targets Zarr v3's V3JsonEncoder class and metadata handling methods.

The module patches these key Zarr components:
    - zarr.core.metadata.v3.V3JsonEncoder (core JSON encoder class)
    - GroupMetadata.to_buffer_dict (where JSON serialization actually happens!)
    - GroupMetadata.from_dict (group metadata deserialization)
    - ArrayV3Metadata.from_dict (array metadata deserialization)

Key Functions:
    - patch_v3_json_encoder(): Patch Zarr's JSON encoder class
    - patch_zarr_v3_json_loading(): Patch metadata loading for type restoration
    - restore_original_zarr_functions(): Restore original Zarr behavior
    - is_zarr_patched(): Check if patching is active

Design Principles:
    - Surgical precision: Only patch Zarr, never global JSON
    - Reversible: Can restore original behavior
    - Safe: Extensive error handling and validation
    - Isolated: No effects on other libraries

Author: F. Herbrand
License: MIT
"""

import warnings
from typing import Any, Dict, Optional, Callable

from . import serializers
from .type_handlers import is_zarr_array_metadata_field


# Global registry of original Zarr functions for restoration
_original_zarr_functions: Dict[str, Any] = {}
_zarr_patching_active = False


def _store_original_function(name: str, func: Callable) -> None:
    """Store original function for later restoration."""
    if name not in _original_zarr_functions:
        _original_zarr_functions[name] = func


def patch_v3_json_encoder() -> None:
    """
    Patch Zarr v3's JSON encoder class.
    
    This function replaces the V3JsonEncoder class with an enhanced version
    that supports additional Python types while maintaining full compatibility
    with existing Zarr code.
    
    Raises
    ------
    ImportError
        If Zarr v3 metadata module is not available
    AttributeError
        If V3JsonEncoder class is not found (API change)
    """
    global _zarr_patching_active
    
    try:
        from zarr.core.metadata.v3 import V3JsonEncoder
        import zarr.core.metadata.v3 as v3meta
    except ImportError as e:
        raise ImportError(
            "Cannot patch Zarr v3 JSON encoder: zarr.core.metadata.v3 not available. "
            "Please install Zarr v3.0+: pip install zarr>=3.0.0"
        ) from e
    
    # Check if V3JsonEncoder exists
    if not hasattr(v3meta, 'V3JsonEncoder'):
        raise AttributeError(
            "V3JsonEncoder not found in zarr.core.metadata.v3. "
            "This may indicate an incompatible Zarr version or API change."
        )
    
    # Store original encoder class
    _store_original_function('V3JsonEncoder', V3JsonEncoder)
    
    # Create enhanced encoder class
    class EnhancedV3JsonEncoder(V3JsonEncoder):
        """Enhanced V3JsonEncoder with support for additional Python types."""
        
        def default(self, obj: Any) -> Any:
            """
            Convert objects to JSON-serializable form using type handlers.
            
            This method is called by json.dumps() for objects that are not
            natively JSON-serializable. It first tries our type handlers,
            then falls back to the parent class behavior.
            """
            # Use our type handlers first
            converted = serializers.convert_for_zarr_json(obj)
            
            # If our handlers converted the object, return the conversion
            if converted is not obj:
                return converted
            
            # Otherwise, fall back to parent class behavior
            return super().default(obj)
    
    # Apply the patch by replacing the class IN THE MODULE
    v3meta.V3JsonEncoder = EnhancedV3JsonEncoder
    
    # CRITICAL FIX: Also patch it in the group module if it's imported there
    try:
        from zarr.core import group
        # If group module has imported V3JsonEncoder, update it there too
        if hasattr(group, 'V3JsonEncoder'):
            group.V3JsonEncoder = EnhancedV3JsonEncoder
            print("✅ Also patched V3JsonEncoder in zarr.core.group")
    except (ImportError, AttributeError):
        pass
    
    _zarr_patching_active = True
    print("✅ Patched zarr.core.metadata.v3.V3JsonEncoder")


def patch_zarr_v3_json_loading() -> None:
    """
    Patch Zarr v3's JSON loading to restore our enhanced types.
    
    This function ensures that when Zarr loads JSON data, our type
    restoration logic is applied to convert enhanced JSON back to
    proper Python objects.
    """
    try:
        import zarr.core.metadata.v3 as v3meta
        from zarr.core.metadata.v3 import ArrayV3Metadata
        
        # Store original from_dict method  
        if hasattr(ArrayV3Metadata, 'from_dict'):
            _store_original_function('ArrayV3Metadata.from_dict', ArrayV3Metadata.from_dict)
            
            @classmethod
            def enhanced_from_dict(cls, data: Dict[str, Any]):
                """Enhanced from_dict with type restoration - but skip Array metadata."""
                # CRITICAL FIX: Do NOT apply our type restoration to Array metadata
                # Array metadata needs specific numeric types that our restoration might break
                # Only apply restoration to Group metadata where our custom types make sense
                
                # Call original method directly without restoration for Arrays
                return _original_zarr_functions['ArrayV3Metadata.from_dict'](data)
            
            ArrayV3Metadata.from_dict = enhanced_from_dict
            print("✅ Patched ArrayV3Metadata.from_dict (passthrough only)")
        
        # CRITICAL: Patch Attributes.__setitem__ to preserve dataclasses BEFORE Zarr processes them
        try:
            from zarr.core.attributes import Attributes
            
            if hasattr(Attributes, '__setitem__'):
                _store_original_function('Attributes.__setitem__', Attributes.__setitem__)
                
                def enhanced_attributes_setitem(self, key, value):
                    """Enhanced Attributes.__setitem__ that pre-processes complex types."""
                    # Apply our type conversion to preserve complex types as enhanced JSON
                    processed_value = serializers.convert_for_zarr_json(value)
                    
                    # Call original method with processed value
                    return _original_zarr_functions['Attributes.__setitem__'](self, key, processed_value)
                
                Attributes.__setitem__ = enhanced_attributes_setitem
                print("✅ Patched Attributes.__setitem__ to preserve complex types")
            
            # CRITICAL: Also patch Attributes.__getitem__ to restore types for memory store
            if hasattr(Attributes, '__getitem__'):
                _store_original_function('Attributes.__getitem__', Attributes.__getitem__)
                
                def enhanced_attributes_getitem(self, key):
                    """Enhanced Attributes.__getitem__ that restores complex types."""
                    # Get the raw value from original method
                    raw_value = _original_zarr_functions['Attributes.__getitem__'](self, key)
                    
                    # Apply our type restoration
                    restored_value = serializers.restore_from_zarr_json(raw_value)
                    
                    return restored_value
                
                Attributes.__getitem__ = enhanced_attributes_getitem
                print("✅ Patched Attributes.__getitem__ to restore complex types")
        
        except ImportError:
            print("⚠️  zarr.core.attributes.Attributes not found")
        
        # CRITICAL: Patch GroupMetadata.to_buffer_dict for Group attributes!
        # This is where the actual JSON serialization happens for group attributes
        try:
            from zarr.core.group import GroupMetadata
            
            if hasattr(GroupMetadata, 'to_buffer_dict'):
                _store_original_function('GroupMetadata.to_buffer_dict', GroupMetadata.to_buffer_dict)
                
                def enhanced_group_to_buffer_dict(self, prototype):
                    """Enhanced GroupMetadata.to_buffer_dict that processes attributes."""
                    import json
                    from zarr.core.metadata.v3 import V3JsonEncoder, _replace_special_floats
                    
                    # Get the dict representation
                    data = self.to_dict()
                    
                    # CRITICAL FIX: Only process 'attributes' for Groups, not Array metadata
                    # Array metadata (data_type, shape, etc.) should NOT be enhanced
                    if 'attributes' in data and data['attributes'] and data.get('node_type') == 'group':
                        # Only process group attributes, skip array metadata
                        processed_attributes = {}
                        for key, value in data['attributes'].items():
                            # Apply our type conversion to each attribute value
                            if not is_zarr_array_metadata_field(key, value):
                                processed_attributes[key] = serializers.convert_for_zarr_json(value)
                            else:
                                processed_attributes[key] = value  # Keep array metadata unchanged
                        data['attributes'] = processed_attributes
                    
                    # Use enhanced JSON encoding
                    class AttributeProcessingEncoder(V3JsonEncoder):
                        def default(self, obj):
                            # Apply our type conversion for any remaining objects
                            converted = serializers.convert_for_zarr_json(obj)
                            if converted is not obj:
                                return converted
                            return super().default(obj)
                    
                    # Use the standard Zarr flow but with our enhanced encoder
                    json_str = json.dumps(_replace_special_floats(data), cls=AttributeProcessingEncoder)
                    json_bytes = json_str.encode()
                    
                    # Return in the expected format
                    if prototype is not None:
                        return {"zarr.json": prototype.buffer.from_bytes(json_bytes)}
                    else:
                        return {"zarr.json": json_bytes}  
                
                
                GroupMetadata.to_buffer_dict = enhanced_group_to_buffer_dict
                print("✅ Patched GroupMetadata.to_buffer_dict for Group attributes")
                
        except ImportError:
            print("⚠️  zarr.core.group.GroupMetadata not found")
        
        # Also patch GroupMetadata.from_dict for loading
        try:
            from zarr.core.group import GroupMetadata
            
            if hasattr(GroupMetadata, 'from_dict'):
                _store_original_function('GroupMetadata.from_dict', GroupMetadata.from_dict)
                
                @classmethod
                def enhanced_group_from_dict(cls, data: Dict[str, Any]):
                    """Enhanced GroupMetadata.from_dict with type restoration."""
                    # Make a copy to avoid modifying the original
                    data_copy = data.copy() if isinstance(data, dict) else data
                    
                    # CRITICAL FIX: Apply our type restoration to attributes specifically
                    if isinstance(data_copy, dict) and 'attributes' in data_copy and data_copy['attributes']:
                        # Process each attribute through our type handlers
                        restored_attributes = {}
                        for key, value in data_copy['attributes'].items():
                            restored_attributes[key] = serializers.restore_from_zarr_json(value)
                        data_copy['attributes'] = restored_attributes
                    
                    # Call original method with restored data
                    return _original_zarr_functions['GroupMetadata.from_dict'](data_copy)
                
                GroupMetadata.from_dict = enhanced_group_from_dict
                print("✅ Patched GroupMetadata.from_dict for Group attributes")
                
        except ImportError:
            print("⚠️  zarr.core.group.GroupMetadata.from_dict not found")
    
    except Exception as e:
        warnings.warn(
            f"Failed to patch JSON loading: {e}. "
            "Type restoration may not work correctly.",
            UserWarning,
            stacklevel=2
        )


def restore_original_zarr_functions() -> None:
    """
    Restore all original Zarr functions, undoing all patches.
    
    This function reverses all patches applied by this module, restoring
    Zarr to its original behavior. After calling this function, tuples will
    again be converted to lists in Zarr metadata.
    """
    global _zarr_patching_active
    
    if not _original_zarr_functions:
        warnings.warn(
            "No original functions stored. Either patching was never applied "
            "or functions were already restored.",
            UserWarning,
            stacklevel=2
        )
        return
    
    restoration_count = 0
    
    # Restore V3JsonEncoder
    if 'V3JsonEncoder' in _original_zarr_functions:
        try:
            import zarr.core.metadata.v3 as v3meta
            v3meta.V3JsonEncoder = _original_zarr_functions['V3JsonEncoder']
            restoration_count += 1
        except ImportError:
            pass
    
    # Restore metadata classes
    try:
        import zarr.core.metadata.v3
        
        # Restore ArrayV3Metadata
        if 'ArrayV3Metadata.from_dict' in _original_zarr_functions:
            zarr.core.metadata.v3.ArrayV3Metadata.from_dict = _original_zarr_functions['ArrayV3Metadata.from_dict']
            restoration_count += 1
            
    except ImportError:
        pass
    
    # Restore Attributes class
    try:
        from zarr.core.attributes import Attributes
        
        # Restore Attributes.__setitem__
        if 'Attributes.__setitem__' in _original_zarr_functions:
            Attributes.__setitem__ = _original_zarr_functions['Attributes.__setitem__']
            restoration_count += 1
        
        # Restore Attributes.__getitem__
        if 'Attributes.__getitem__' in _original_zarr_functions:
            Attributes.__getitem__ = _original_zarr_functions['Attributes.__getitem__']
            restoration_count += 1
            
    except ImportError:
        pass
    
    # Restore GroupMetadata
    try:
        from zarr.core.group import GroupMetadata
        
        # Restore GroupMetadata.to_buffer_dict
        if 'GroupMetadata.to_buffer_dict' in _original_zarr_functions:
            GroupMetadata.to_buffer_dict = _original_zarr_functions['GroupMetadata.to_buffer_dict']
            restoration_count += 1
            
        # Restore GroupMetadata.from_dict
        if 'GroupMetadata.from_dict' in _original_zarr_functions:
            GroupMetadata.from_dict = _original_zarr_functions['GroupMetadata.from_dict']
            restoration_count += 1
            
    except ImportError:
        pass
    
    # Clear the registry
    _original_zarr_functions.clear()
    _zarr_patching_active = False
    
    print(f"✅ Restored {restoration_count} original Zarr functions")


def is_zarr_patched() -> bool:
    """
    Check if Zarr patching is currently active.
    
    Returns
    -------
    bool
        True if Zarr functions are currently patched, False otherwise
    """
    return _zarr_patching_active and bool(_original_zarr_functions)


def get_patch_status() -> Dict[str, bool]:
    """
    Get detailed status of all Zarr patches.
    
    Returns
    -------
    dict
        Dictionary mapping function names to their patch status
    """
    status = {}
    
    # Check V3JsonEncoder
    try:
        import zarr.core.metadata.v3 as v3meta
        status['V3JsonEncoder'] = 'V3JsonEncoder' in _original_zarr_functions
    except ImportError:
        status['V3JsonEncoder'] = False
    
    # Check metadata classes
    try:
        import zarr.core.metadata.v3
        status['ArrayV3Metadata.from_dict'] = 'ArrayV3Metadata.from_dict' in _original_zarr_functions
    except ImportError:
        status['ArrayV3Metadata.from_dict'] = False
    
    # Check Attributes class
    try:
        from zarr.core.attributes import Attributes
        status['Attributes.__setitem__'] = 'Attributes.__setitem__' in _original_zarr_functions
        status['Attributes.__getitem__'] = 'Attributes.__getitem__' in _original_zarr_functions
    except ImportError:
        status['Attributes.__setitem__'] = False
        status['Attributes.__getitem__'] = False
    
    # Check GroupMetadata classes
    try:
        from zarr.core.group import GroupMetadata
        status['GroupMetadata.to_buffer_dict'] = 'GroupMetadata.to_buffer_dict' in _original_zarr_functions
        status['GroupMetadata.from_dict'] = 'GroupMetadata.from_dict' in _original_zarr_functions
    except ImportError:
        status['GroupMetadata.to_buffer_dict'] = False
        status['GroupMetadata.from_dict'] = False
    
    return status


def print_patch_status() -> None:
    """
    Print a detailed report of current patch status.
    
    This function provides a human-readable summary of which Zarr functions
    are currently patched and which are using original behavior.
    """
    print("🔧 Zarr Patching Status Report")
    print("=" * 40)
    
    status = get_patch_status()
    patched_count = sum(1 for patched in status.values() if patched)
    total_count = len(status)
    
    print(f"📊 Overall: {patched_count}/{total_count} functions patched")
    print()
    
    # Show V3JsonEncoder status
    v3_encoder_patched = status.get('V3JsonEncoder', False)
    icon = "✅" if v3_encoder_patched else "❌"
    status_text = "patched" if v3_encoder_patched else "original"
    print("🎯 Core JSON Encoder:")
    print(f"   {icon} V3JsonEncoder: {status_text}")
    print()
    
    # Show metadata functions
    metadata_functions = {k: v for k, v in status.items() if 'Metadata' in k}
    if metadata_functions:
        print("📋 Metadata Functions:")
        for func_name, is_patched in metadata_functions.items():
            icon = "✅" if is_patched else "❌"
            status_text = "patched" if is_patched else "original"
            print(f"   {icon} {func_name}: {status_text}")
        print()
    
    if patched_count == total_count:
        print("🎉 All Zarr functions are patched and ready!")
    elif patched_count == 0:
        print("⚠️  No Zarr functions are currently patched.")
        print("   Call enable_zarr_serialization() to enable enhancements.")
    else:
        print("⚠️  Partial patching detected. Some functions may not work correctly.")
        print("   Try calling enable_zarr_serialization() again.")


def validate_zarr_patches() -> bool:
    """
    Validate that all expected Zarr patches are working correctly.
    
    This function performs basic validation to ensure that the patched
    functions are behaving as expected and can handle enhanced types.
    
    Returns
    -------
    bool
        True if all patches are working correctly, False otherwise
    """
    try:
        # Test basic tuple serialization through V3JsonEncoder
        from zarr.core.metadata.v3 import V3JsonEncoder
        
        encoder = V3JsonEncoder()
        test_data = {"test_tuple": (1, 2, 3)}
        
        # Test encoding
        encoded = encoder.encode(test_data)
        
        # Check if our enhancement is working
        import json
        decoded = json.loads(encoded)
        
        # If tuple is preserved as our special format, patching works
        if isinstance(decoded.get("test_tuple"), dict) and decoded["test_tuple"].get("__type__") == "tuple":
            print("✅ Zarr patch validation successful - tuple preservation active")
            return True
        else:
            print(f"❌ Zarr patch validation failed - tuple not preserved: {decoded}")
            return False
        
    except Exception as e:
        print(f"❌ Zarr patch validation failed: {e}")
        return False