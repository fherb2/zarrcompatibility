"""
Zarr-specific patching functions for zarrcompatibility.

This module contains the core patching logic that modifies Zarr's internal
JSON serialization methods to support additional Python types. Unlike the
old approach that patched the global json module, this module only patches
Zarr-specific functions, ensuring zero side effects on other libraries.

The module patches these key Zarr components:
    - zarr.util.json_dumps and json_loads (core JSON functions)
    - ArrayV3Metadata.to_buffer_dict and from_dict (array metadata)
    - GroupV3Metadata.to_buffer_dict and from_dict (group metadata)

Key Functions:
    - patch_zarr_util_json(): Patch Zarr's core JSON utilities
    - patch_zarr_v3_metadata(): Patch Zarr v3 metadata serialization methods
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


# Global registry of original Zarr functions for restoration
_original_zarr_functions: Dict[str, Any] = {}
_zarr_patching_active = False


def _store_original_function(name: str, func: Callable) -> None:
    """Store original function for later restoration."""
    if name not in _original_zarr_functions:
        _original_zarr_functions[name] = func


def patch_zarr_util_json() -> None:
    """
    Patch Zarr's core JSON utility functions.
    
    This function replaces zarr.util.json_dumps and zarr.util.json_loads
    with enhanced versions that support additional Python types while
    maintaining full compatibility with existing Zarr code.
    
    Raises
    ------
    ImportError
        If Zarr is not installed or zarr.util module is not available
    AttributeError
        If expected Zarr functions are not found (API change)
    """
    global _zarr_patching_active
    
    try:
        import zarr.util
    except ImportError as e:
        raise ImportError(
            "Cannot patch Zarr utilities: Zarr not installed or incompatible version. "
            "Please install Zarr v3.0+: pip install zarr>=3.0.0"
        ) from e
    
    # Check if functions exist
    if not hasattr(zarr.util, 'json_dumps'):
        raise AttributeError(
            "zarr.util.json_dumps not found. This may indicate an incompatible "
            "Zarr version or API change. Please check supported Zarr versions."
        )
    
    if not hasattr(zarr.util, 'json_loads'):
        raise AttributeError(
            "zarr.util.json_loads not found. This may indicate an incompatible "
            "Zarr version or API change. Please check supported Zarr versions."
        )
    
    # Store original functions
    _store_original_function('zarr.util.json_dumps', zarr.util.json_dumps)
    _store_original_function('zarr.util.json_loads', zarr.util.json_loads)
    
    # Create enhanced wrapper functions
    def enhanced_zarr_json_dumps(obj: Any, **kwargs) -> bytes:
        """Enhanced zarr.util.json_dumps with type preservation."""
        # Convert object using our type handlers
        converted_obj = serializers.convert_for_zarr_json(obj)
        
        # Call original Zarr function with converted object
        return _original_zarr_functions['zarr.util.json_dumps'](converted_obj, **kwargs)
    
    def enhanced_zarr_json_loads(data: bytes, **kwargs) -> Any:
        """Enhanced zarr.util.json_loads with type restoration."""
        # Call original Zarr function first
        loaded_data = _original_zarr_functions['zarr.util.json_loads'](data, **kwargs)
        
        # Restore objects using our type handlers
        return serializers.restore_from_zarr_json(loaded_data)
    
    # Apply patches
    zarr.util.json_dumps = enhanced_zarr_json_dumps
    zarr.util.json_loads = enhanced_zarr_json_loads
    
    _zarr_patching_active = True
    print("✅ Patched zarr.util.json_dumps and zarr.util.json_loads")


def patch_zarr_v3_metadata() -> None:
    """
    Patch Zarr v3 metadata serialization methods.
    
    This function patches the to_buffer_dict and from_dict methods of
    ArrayV3Metadata and GroupV3Metadata to ensure that our enhanced
    JSON serialization is used for all metadata operations.
    
    Raises
    ------
    ImportError
        If Zarr v3 metadata modules are not available
    AttributeError
        If expected metadata classes or methods are not found
    """
    try:
        import zarr.core.metadata.v3
    except ImportError as e:
        raise ImportError(
            "Cannot patch Zarr v3 metadata: zarr.core.metadata.v3 not available. "
            "This may indicate Zarr v2 or incompatible version. "
            "zarrcompatibility requires Zarr v3.0+."
        ) from e
    
    # Patch ArrayV3Metadata
    try:
        array_metadata_class = zarr.core.metadata.v3.ArrayV3Metadata
        
        # Check if methods exist
        if not hasattr(array_metadata_class, 'to_buffer_dict'):
            raise AttributeError("ArrayV3Metadata.to_buffer_dict not found")
        if not hasattr(array_metadata_class, 'from_dict'):
            raise AttributeError("ArrayV3Metadata.from_dict not found")
        
        # Store original methods
        _store_original_function('ArrayV3Metadata.to_buffer_dict', array_metadata_class.to_buffer_dict)
        _store_original_function('ArrayV3Metadata.from_dict', array_metadata_class.from_dict)
        
        # Create enhanced methods
        def enhanced_array_to_buffer_dict(self, prototype):
            """Enhanced ArrayV3Metadata.to_buffer_dict with type preservation."""
            # Get the metadata as dict first
            metadata_dict = self.to_dict()
            
            # Convert using our type handlers (this handles attributes)
            converted_dict = serializers.convert_for_zarr_json(metadata_dict)
            
            # Call original method with converted dict
            # Note: We need to temporarily replace the to_dict result
            original_to_dict = self.to_dict
            self.to_dict = lambda: converted_dict
            
            try:
                result = _original_zarr_functions['ArrayV3Metadata.to_buffer_dict'](self, prototype)
            finally:
                self.to_dict = original_to_dict
            
            return result
        
        @classmethod
        def enhanced_array_from_dict(cls, data):
            """Enhanced ArrayV3Metadata.from_dict with type restoration."""
            # Restore objects first using our type handlers
            restored_data = serializers.restore_from_zarr_json(data)
            
            # Call original method with restored data
            return _original_zarr_functions['ArrayV3Metadata.from_dict'](restored_data)
        
        # Apply patches
        array_metadata_class.to_buffer_dict = enhanced_array_to_buffer_dict
        array_metadata_class.from_dict = enhanced_array_from_dict
        
        print("✅ Patched ArrayV3Metadata.to_buffer_dict and from_dict")
        
    except Exception as e:
        warnings.warn(
            f"Failed to patch ArrayV3Metadata: {e}. "
            "Array metadata may not preserve types correctly.",
            UserWarning,
            stacklevel=2
        )
    
    # Patch GroupV3Metadata  
    try:
        group_metadata_class = zarr.core.metadata.v3.GroupV3Metadata
        
        # Check if methods exist
        if not hasattr(group_metadata_class, 'to_buffer_dict'):
            raise AttributeError("GroupV3Metadata.to_buffer_dict not found")
        if not hasattr(group_metadata_class, 'from_dict'):
            raise AttributeError("GroupV3Metadata.from_dict not found")
        
        # Store original methods
        _store_original_function('GroupV3Metadata.to_buffer_dict', group_metadata_class.to_buffer_dict)
        _store_original_function('GroupV3Metadata.from_dict', group_metadata_class.from_dict)
        
        # Create enhanced methods
        def enhanced_group_to_buffer_dict(self, prototype):
            """Enhanced GroupV3Metadata.to_buffer_dict with type preservation."""
            # Get the metadata as dict first
            metadata_dict = self.to_dict()
            
            # Convert using our type handlers (this handles attributes)
            converted_dict = serializers.convert_for_zarr_json(metadata_dict)
            
            # Call original method with converted dict
            original_to_dict = self.to_dict
            self.to_dict = lambda: converted_dict
            
            try:
                result = _original_zarr_functions['GroupV3Metadata.to_buffer_dict'](self, prototype)
            finally:
                self.to_dict = original_to_dict
            
            return result
        
        @classmethod  
        def enhanced_group_from_dict(cls, data):
            """Enhanced GroupV3Metadata.from_dict with type restoration."""
            # Restore objects first using our type handlers
            restored_data = serializers.restore_from_zarr_json(data)
            
            # Call original method with restored data
            return _original_zarr_functions['GroupV3Metadata.from_dict'](restored_data)
        
        # Apply patches
        group_metadata_class.to_buffer_dict = enhanced_group_to_buffer_dict
        group_metadata_class.from_dict = enhanced_group_from_dict
        
        print("✅ Patched GroupV3Metadata.to_buffer_dict and from_dict")
        
    except Exception as e:
        warnings.warn(
            f"Failed to patch GroupV3Metadata: {e}. "
            "Group metadata may not preserve types correctly.",
            UserWarning,
            stacklevel=2
        )


def restore_original_zarr_functions() -> None:
    """
    Restore all original Zarr functions, undoing all patches.
    
    This function reverses all patches applied by this module, restoring
    Zarr to its original behavior. This is useful for testing and debugging.
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
    
    # Restore zarr.util functions
    try:
        import zarr.util
        if 'zarr.util.json_dumps' in _original_zarr_functions:
            zarr.util.json_dumps = _original_zarr_functions['zarr.util.json_dumps']
            restoration_count += 1
        if 'zarr.util.json_loads' in _original_zarr_functions:
            zarr.util.json_loads = _original_zarr_functions['zarr.util.json_loads']
            restoration_count += 1
    except ImportError:
        pass
    
    # Restore metadata classes
    try:
        import zarr.core.metadata.v3
        
        # Restore ArrayV3Metadata
        if 'ArrayV3Metadata.to_buffer_dict' in _original_zarr_functions:
            zarr.core.metadata.v3.ArrayV3Metadata.to_buffer_dict = _original_zarr_functions['ArrayV3Metadata.to_buffer_dict']
            restoration_count += 1
        if 'ArrayV3Metadata.from_dict' in _original_zarr_functions:
            zarr.core.metadata.v3.ArrayV3Metadata.from_dict = _original_zarr_functions['ArrayV3Metadata.from_dict']
            restoration_count += 1
        
        # Restore GroupV3Metadata
        if 'GroupV3Metadata.to_buffer_dict' in _original_zarr_functions:
            zarr.core.metadata.v3.GroupV3Metadata.to_buffer_dict = _original_zarr_functions['GroupV3Metadata.to_buffer_dict']
            restoration_count += 1
        if 'GroupV3Metadata.from_dict' in _original_zarr_functions:
            zarr.core.metadata.v3.GroupV3Metadata.from_dict = _original_zarr_functions['GroupV3Metadata.from_dict']
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
    
    # Check zarr.util functions
    try:
        import zarr.util
        status['zarr.util.json_dumps'] = 'zarr.util.json_dumps' in _original_zarr_functions
        status['zarr.util.json_loads'] = 'zarr.util.json_loads' in _original_zarr_functions
    except ImportError:
        status['zarr.util.json_dumps'] = False
        status['zarr.util.json_loads'] = False
    
    # Check metadata classes
    try:
        import zarr.core.metadata.v3
        status['ArrayV3Metadata.to_buffer_dict'] = 'ArrayV3Metadata.to_buffer_dict' in _original_zarr_functions
        status['ArrayV3Metadata.from_dict'] = 'ArrayV3Metadata.from_dict' in _original_zarr_functions
        status['GroupV3Metadata.to_buffer_dict'] = 'GroupV3Metadata.to_buffer_dict' in _original_zarr_functions
        status['GroupV3Metadata.from_dict'] = 'GroupV3Metadata.from_dict' in _original_zarr_functions
    except ImportError:
        status['ArrayV3Metadata.to_buffer_dict'] = False
        status['ArrayV3Metadata.from_dict'] = False
        status['GroupV3Metadata.to_buffer_dict'] = False
        status['GroupV3Metadata.from_dict'] = False
    
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
    
    # Group by category
    util_functions = {k: v for k, v in status.items() if k.startswith('zarr.util')}
    metadata_functions = {k: v for k, v in status.items() if not k.startswith('zarr.util')}
    
    if util_functions:
        print("🛠️  Zarr Utility Functions:")
        for func_name, is_patched in util_functions.items():
            icon = "✅" if is_patched else "❌"
            status_text = "patched" if is_patched else "original"
            print(f"   {icon} {func_name}: {status_text}")
        print()
    
    if metadata_functions:
        print("📋 Zarr Metadata Functions:")
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
        # Test basic tuple serialization through Zarr utilities
        import zarr.util
        
        test_data = {"test_tuple": (1, 2, 3)}
        
        # Test zarr.util.json_dumps
        json_bytes = zarr.util.json_dumps(test_data)
        
        # Test zarr.util.json_loads  
        restored_data = zarr.util.json_loads(json_bytes)
        
        # Verify tuple was preserved
        if not isinstance(restored_data["test_tuple"], tuple):
            return False
        
        if restored_data["test_tuple"] != (1, 2, 3):
            return False
        
        print("✅ Zarr patch validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Zarr patch validation failed: {e}")
        return False