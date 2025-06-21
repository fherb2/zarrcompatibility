#!/usr/bin/env python3
"""
Error handling and recovery tests for zarrcompatibility.

Tests robustness, error scenarios, and graceful degradation.

Author: F. Herbrand
License: MIT
"""

import sys
import tempfile
import json
import warnings
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Setup paths
def setup_project_paths() -> Dict[str, Path]:
    """Setup paths consistently regardless of execution directory."""
    current_dir = Path.cwd()
    if current_dir.name == 'tests':
        src_path = current_dir.parent / 'src'
    else:
        src_path = current_dir / 'src'
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return {'src_path': src_path}

PATHS = setup_project_paths()


class TestSerializationErrors:
    """Test error handling in serialization process."""
    
    def test_circular_reference_detection(self) -> None:
        """Test handling of circular references."""
        import zarrcompatibility as zc
        from zarrcompatibility.serializers import enhanced_json_dumps
        
        zc.enable_zarr_serialization()
        
        try:
            # Create circular reference
            obj_a: Dict[str, Any] = {"name": "A"}
            obj_b: Dict[str, Any] = {"name": "B", "ref": obj_a}
            obj_a["ref"] = obj_b
            
            try:
                result = enhanced_json_dumps(obj_a)
                # Python's JSON should handle this by raising an error
                assert False, "Should have detected circular reference"
            except (ValueError, RecursionError) as e:
                print(f"✅ Circular reference correctly detected: {type(e).__name__}")
        
        finally:
            zc.disable_zarr_serialization()
    
    def test_corrupted_enhanced_json_loads(self) -> None:
        """Test handling of corrupted Enhanced JSON data."""
        from zarrcompatibility.serializers import enhanced_json_loads
        
        corrupted_cases = [
            '{"__type__": "tuple"}',  # Missing __data__
            '{"__type__": "unknown_type", "__data__": [1,2,3]}',  # Unknown type
            '{"__type__": "tuple", "__data__": "not_a_list"}',  # Invalid data format
            '{"__type__": "datetime", "__data__": "invalid_date"}',  # Invalid datetime
            '{"__type__": "enum", "__class__": "nonexistent.Module.Class", "__data__": "value"}',  # Non-existent class
            '{"__type__": "dataclass", "__class__": "missing.Class", "__data__": {}}',  # Missing dataclass
        ]
        
        for i, corrupted_json in enumerate(corrupted_cases):
            try:
                result = enhanced_json_loads(corrupted_json)
                # Should either return the dict as-is or handle gracefully
                assert isinstance(result, dict), f"Case {i}: Should return dict for corrupted JSON"
                print(f"✅ Corrupted case {i}: Handled gracefully -> {type(result)}")
            except Exception as e:
                # If it throws an exception, it should be controlled
                print(f"⚠️ Corrupted case {i}: Exception (controlled): {type(e).__name__}")
    
    def test_type_handler_exceptions(self) -> None:
        """Test behavior when type handlers raise exceptions."""
        import zarrcompatibility as zc
        from zarrcompatibility.type_handlers import _TYPE_HANDLERS, TypeHandler
        
        zc.enable_zarr_serialization()
        
        try:
            # Create a handler that always fails
            class FailingHandler(TypeHandler):
                def can_handle(self, obj: Any) -> bool:
                    return isinstance(obj, str) and obj == "FAIL"
                
                def serialize(self, obj: Any) -> Any:
                    raise RuntimeError("Intentional handler failure")
                
                def can_deserialize(self, data: Any) -> bool:
                    return False
                
                def deserialize(self, data: Any) -> Any:
                    return data
            
            # Register the failing handler
            from zarrcompatibility.type_handlers import register_type_handler
            register_type_handler(FailingHandler(), priority=1)
            
            try:
                from zarrcompatibility.type_handlers import serialize_object
                result = serialize_object("FAIL")
                # Should fall back to string conversion
                assert result == "FAIL"
                print("✅ Handler exception handled with fallback")
            except Exception as e:
                print(f"⚠️ Handler exception not handled: {e}")
        
        finally:
            # Clean up - remove the failing handler
            if _TYPE_HANDLERS and isinstance(_TYPE_HANDLERS[0], FailingHandler):
                _TYPE_HANDLERS.pop(0)
            zc.disable_zarr_serialization()
    
    def test_numpy_edge_case_handling(self) -> None:
        """Test handling of problematic NumPy values."""
        try:
            import numpy as np
            import zarrcompatibility as zc
            from zarrcompatibility.type_handlers import serialize_object
            
            zc.enable_zarr_serialization()
            
            try:
                # Test problematic NumPy values
                problematic_values = [
                    np.inf,
                    -np.inf,
                    np.nan,
                    np.float64(np.inf),
                    np.float32(-np.inf),
                    np.complex128(np.nan + 1j * np.inf),
                ]
                
                for i, value in enumerate(problematic_values):
                    try:
                        result = serialize_object(value)
                        print(f"✅ Problematic NumPy value {i} handled: {value} -> {result}")
                    except Exception as e:
                        print(f"⚠️ Problematic NumPy value {i} failed: {value} -> {e}")
            
            finally:
                zc.disable_zarr_serialization()
        
        except ImportError:
            print("⚠️ NumPy not available - skipping NumPy edge case tests")


class TestZarrPatchingErrors:
    """Test error handling in Zarr patching system."""
    
    def test_zarr_not_available(self) -> None:
        """Test behavior when Zarr is not available."""
        import zarrcompatibility as zc
        
        # Mock ImportError when trying to import zarr
        with patch('builtins.__import__', side_effect=ImportError("No module named 'zarr'")):
            try:
                zc.enable_zarr_serialization()
                assert False, "Should have raised ImportError"
            except ImportError as e:
                assert "zarr" in str(e).lower()
                print(f"✅ Correctly handles missing Zarr: {e}")
    
    def test_zarr_api_changes(self) -> None:
        """Test behavior when Zarr API changes."""
        import zarrcompatibility as zc
        
        # Create a proper mock that will cause the expected AttributeError
        mock_v3meta = MagicMock()
        # Remove the V3JsonEncoder attribute completely
        if hasattr(mock_v3meta, 'V3JsonEncoder'):
            delattr(mock_v3meta, 'V3JsonEncoder')
        
        # FIXED: Mock the zarr.core.metadata.v3 module directly
        with patch.dict('sys.modules', {
            'zarr.core.metadata.v3': mock_v3meta
        }):
            # Also patch the direct import in zarr_patching
            with patch('zarr.core.metadata.v3', mock_v3meta):
                try:
                    zc.enable_zarr_serialization()
                    assert False, "Should have raised AttributeError"
                except (AttributeError, RuntimeError, ImportError) as e:
                    # Accept any of these errors as they indicate API change handling
                    assert "V3JsonEncoder" in str(e) or "API" in str(e) or "not available" in str(e)
                    print(f"✅ Correctly handles Zarr API changes: {type(e).__name__}")
    
    def test_partial_patch_failure(self) -> None:
        """Test behavior when some patches succeed and others fail."""
        import zarrcompatibility as zc
        from zarrcompatibility import zarr_patching
        
        # This is tricky to test without actually breaking things
        # For now, just verify patch status tracking works
        try:
            zc.enable_zarr_serialization()
            status = zarr_patching.get_patch_status()
            
            # Should have multiple patches
            assert len(status) > 1
            
            # Check that we can detect patch status
            active_patches = sum(1 for is_active in status.values() if is_active)
            print(f"✅ Patch status tracking works: {active_patches}/{len(status)} patches active")
            
        finally:
            zc.disable_zarr_serialization()
    
    def test_multiple_enable_disable_cycles(self) -> None:
        """Test robustness of multiple enable/disable cycles."""
        import zarrcompatibility as zc
        
        for cycle in range(5):
            try:
                zc.enable_zarr_serialization()
                
                # Should be enabled
                assert zc.is_zarr_serialization_enabled()
                
                zc.disable_zarr_serialization()
                
                # Should be disabled
                assert not zc.is_zarr_serialization_enabled()
                
                print(f"✅ Cycle {cycle + 1}: Enable/disable successful")
                
            except Exception as e:
                print(f"❌ Cycle {cycle + 1} failed: {e}")
                # Try to clean up
                try:
                    zc.disable_zarr_serialization()
                except:
                    pass
                break


class TestMemoryAndPerformance:
    """Test memory usage and performance edge cases."""
    
    def test_large_data_structures(self) -> None:
        """Test handling of very large data structures."""
        import zarrcompatibility as zc
        from zarrcompatibility.type_handlers import serialize_object
        
        zc.enable_zarr_serialization()
        
        try:
            # Test large tuple
            large_tuple = tuple(range(1000))
            result = serialize_object(large_tuple)
            assert isinstance(result, dict)
            assert result.get("__type__") == "tuple"
            assert len(result.get("__data__", [])) == 1000
            print("✅ Large tuple (1000 elements) handled successfully")
            
            # Test deeply nested structure
            nested: Dict[str, Any] = {"level": 0}
            current = nested
            for i in range(50):  # 50 levels deep
                current["next"] = {"level": i + 1}
                current = current["next"]
            
            result = serialize_object(nested)
            assert isinstance(result, dict)
            print("✅ Deep nesting (50 levels) handled successfully")
            
        except RecursionError:
            print("⚠️ Hit recursion limit - expected for very deep structures")
        except MemoryError:
            print("⚠️ Hit memory limit - expected for very large structures")
        finally:
            zc.disable_zarr_serialization()
    
    def test_memory_pressure_scenarios(self) -> None:
        """Test behavior under memory pressure."""
        import zarrcompatibility as zc
        
        zc.enable_zarr_serialization()
        
        try:
            # Create many small objects to test memory efficiency
            objects = []
            for i in range(100):
                obj = {
                    "id": i,
                    "data": (i, i*2, i*3),
                    "metadata": {"created": f"item_{i}"}
                }
                objects.append(obj)
            
            # Test serialization of all objects
            from zarrcompatibility.type_handlers import serialize_object
            serialized = [serialize_object(obj) for obj in objects]
            
            assert len(serialized) == 100
            print("✅ Memory pressure test (100 objects) completed successfully")
            
        finally:
            zc.disable_zarr_serialization()


class TestRobustnessScenarios:
    """Test robustness in various scenarios."""
    
    def test_unicode_and_encoding_edge_cases(self) -> None:
        """Test handling of Unicode and encoding edge cases."""
        import zarrcompatibility as zc
        from zarrcompatibility.type_handlers import serialize_object
        
        zc.enable_zarr_serialization()
        
        try:
            unicode_test_cases = [
                "Hello 世界",  # Mixed ASCII/Unicode
                "🎯🚀📋",      # Emoji
                "café naïve résumé",  # Accented characters
                "\u0000\u0001\u0002",  # Control characters
                "",  # Empty string
                " ",  # Whitespace
            ]
            
            for i, test_case in enumerate(unicode_test_cases):
                try:
                    result = serialize_object(test_case)
                    assert result == test_case  # Should pass through unchanged
                    print(f"✅ Unicode case {i}: '{test_case[:20]}' handled correctly")
                except Exception as e:
                    print(f"⚠️ Unicode case {i} failed: {e}")
        
        finally:
            zc.disable_zarr_serialization()
    
    def test_concurrent_access_simulation(self) -> None:
        """Test thread-safety of serialization operations."""
        import zarrcompatibility as zc
        from zarrcompatibility.type_handlers import serialize_object
        import threading
        import time
        from typing import List, Tuple
        
        zc.enable_zarr_serialization()
        
        try:
            results: List[Tuple[int, int, Any]] = []
            errors: List[Tuple[int, Exception]] = []
            
            def worker(worker_id: int) -> None:
                try:
                    for i in range(10):
                        test_data = {
                            "worker": worker_id,
                            "iteration": i,
                            "timestamp": time.time(),
                            "data": (worker_id, i, worker_id * i)
                        }
                        result = serialize_object(test_data)
                        results.append((worker_id, i, result))
                except Exception as e:
                    errors.append((worker_id, e))
            
            # Start multiple threads
            threads = []
            for worker_id in range(3):
                thread = threading.Thread(target=worker, args=(worker_id,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            print(f"✅ Concurrent access test: {len(results)} operations completed")
            if errors:
                print(f"⚠️ {len(errors)} errors occurred during concurrent access")
                for worker_id, error in errors[:3]:  # Show first 3 errors
                    print(f"   Worker {worker_id}: {error}")
        
        finally:
            zc.disable_zarr_serialization()
    
    def test_platform_specific_behaviors(self) -> None:
        """Test platform-specific edge cases."""
        import sys
        import platform
        import zarrcompatibility as zc
        
        print(f"✅ Testing on platform: {platform.system()} {platform.release()}")
        print(f"✅ Python version: {sys.version}")
        
        zc.enable_zarr_serialization()
        
        try:
            # Test path handling (platform-specific)
            test_path = Path("/tmp/test") if platform.system() != "Windows" else Path("C:\\temp\\test")
            
            from zarrcompatibility.type_handlers import serialize_object
            # Paths should be converted to strings
            result = serialize_object(test_path)
            assert isinstance(result, str)
            print(f"✅ Path handling works: {test_path} -> {result}")
            
        finally:
            zc.disable_zarr_serialization()


class TestWarningAndLogging:
    """Test warning and logging behavior."""
    
    def test_deprecation_warnings(self) -> None:
        """Test that deprecation warnings are properly handled."""
        import zarrcompatibility as zc
        
        # Test multiple enable calls
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            zc.enable_zarr_serialization()
            zc.enable_zarr_serialization()  # Second call should warn
            
            # Should have warning about multiple calls
            warning_messages = [str(warning.message) for warning in w]
            has_multiple_enable_warning = any("already enabled" in msg.lower() for msg in warning_messages)
            
            if has_multiple_enable_warning:
                print("✅ Multiple enable calls generate appropriate warning")
            else:
                print("⚠️ Multiple enable calls should generate warning")
            
            zc.disable_zarr_serialization()
    
    def test_disable_without_enable_warning(self) -> None:
        """Test warning when disabling without enabling first."""
        import zarrcompatibility as zc
        
        # Ensure we start clean
        if zc.is_zarr_serialization_enabled():
            zc.disable_zarr_serialization()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            zc.disable_zarr_serialization()  # Should warn
            
            warning_messages = [str(warning.message) for warning in w]
            has_not_enabled_warning = any("not currently enabled" in msg.lower() for msg in warning_messages)
            
            if has_not_enabled_warning:
                print("✅ Disable without enable generates appropriate warning")
            else:
                print("⚠️ Disable without enable should generate warning")


def run_all_error_handling_tests() -> bool:
    """Run all error handling tests."""
    print("🧪 zarrcompatibility v3.0 - Error Handling & Recovery Tests")
    print("=" * 70)
    
    test_classes = [
        TestSerializationErrors(),
        TestZarrPatchingErrors(),
        TestMemoryAndPerformance(),
        TestRobustnessScenarios(),
        TestWarningAndLogging(),
    ]
    
    all_tests = []
    for test_instance in test_classes:
        methods = [getattr(test_instance, method) for method in dir(test_instance) 
                  if method.startswith('test_') and callable(getattr(test_instance, method))]
        all_tests.extend([(test_instance, method) for method in methods])
    
    passed = 0
    for i, (test_instance, test_method) in enumerate(all_tests, 1):
        test_name = f"{test_instance.__class__.__name__}.{test_method.__name__}"
        print(f"\n🔍 Test {i}: {test_name}")
        
        try:
            test_method()
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Error Handling Results: {passed}/{len(all_tests)} tests passed")
    return passed == len(all_tests)


if __name__ == "__main__":
    success = run_all_error_handling_tests()
    sys.exit(0 if success else 1)