# zarrcompatibility v2.1 - Complete Rebuild Plan

## 🎯 **Project Overview**

**Mission:** Transform zarrcompatibility from invasive global JSON patching to surgical Zarr-only patching, eliminating side effects while preserving tuple functionality.

**Target:** Scientific Python users who need tuple preservation in Zarr metadata without breaking their existing toolchain.

---

## 📊 **Current Status Analysis (v2.0.1)**

### ❌ **Critical Problems**
1. **Global JSON Pollution:** Patches `json.dumps`/`json.loads` affecting ALL libraries
2. **Import Order Sensitivity:** Breaks when imported after other JSON-using libraries  
3. **Silent Failures:** Users don't understand why requests/pandas suddenly behave differently
4. **Support Nightmare:** Debugging becomes impossible when JSON behavior changes globally

### ✅ **What Works**
- Tuple preservation mechanism: `{"__type__": "tuple", "__data__": [...]}`
- Complex type serialization (datetime, enum, UUID, dataclass)
- zarrwlr integration

---

## 🔬 **Zarr v3 Architecture Analysis**

### **Zarr's JSON System (Discovered)**
```python
# Zarr v3 JSON Flow:
zarr.util.json_dumps()  # Central JSON serialization
    ↓
ArrayV3Metadata.to_buffer_dict()  # Metadata serialization  
    ↓
V3JsonEncoder  # Zarr-specific JSON encoder
    ↓
Store (zarr.json files)
```

### **Key Insight: Zarr Has Clean Abstractions**
- `zarr.util.json_dumps` / `zarr.util.json_loads` - Core JSON functions
- `ArrayV3Metadata.to_buffer_dict()` - Array metadata serialization  
- `ArrayV3Metadata.from_dict()` - Array metadata deserialization
- `GroupV3Metadata.to_buffer_dict()` - Group metadata serialization
- `GroupV3Metadata.from_dict()` - Group metadata deserialization

**🎉 ADVANTAGE:** We can patch these specific methods instead of global JSON!

---

## 🚀 **New Architecture: Zarr-Only Patching**

### **Core Strategy**
```python
def enable_zarr_serialization():
    """Patch ONLY Zarr's JSON system, leave global json untouched"""
    
    # 1. Zarr Version Compatibility Check
    validate_zarr_version()
    
    # 2. Patch Zarr's Core JSON Functions
    patch_zarr_util_json()  # zarr.util.json_dumps/loads
    
    # 3. Patch Zarr v3 Metadata Methods  
    patch_zarr_v3_serialization()   # to_buffer_dict methods
    patch_zarr_v3_deserialization() # from_dict methods
```

### **Patch Points Identified**
1. **`zarr.util.json_dumps`** - Central serialization
2. **`zarr.util.json_loads`** - Central deserialization  
3. **`ArrayV3Metadata.to_buffer_dict`** - Array metadata writing
4. **`ArrayV3Metadata.from_dict`** - Array metadata reading
5. **`GroupV3Metadata.to_buffer_dict`** - Group metadata writing
6. **`GroupV3Metadata.from_dict`** - Group metadata reading

### **Benefits of New Approach**
- ✅ **Zero Side Effects:** Global JSON remains untouched
- ✅ **Import Order Independent:** Works regardless of import sequence
- ✅ **Library Isolation:** requests, pandas, numpy unaffected
- ✅ **Easier Debugging:** Problems isolated to Zarr operations only
- ✅ **Professional Grade:** Safe for production scientific environments

---

## 🔧 **Implementation Plan**

### **Phase 1: Core Zarr Patching** 
**Goal:** Replace global JSON patching with Zarr-specific patching

#### **1.1 Zarr Version Management**
```python
# supported_zarr_versions.json (auto-updated by CI)
{
    "min_version": "3.0.0",
    "max_tested": "3.0.8", 
    "known_working": ["3.0.0", "3.0.1", "3.0.5", "3.0.8"],
    "last_update": "2025-01-19"
}

def validate_zarr_version():
    """Check if installed Zarr version is supported"""
    if zarr_version < min_version:
        raise ImportError(f"zarrcompatibility requires Zarr v3+ (found {zarr_version})")
    if zarr_version > max_tested:
        warnings.warn(f"Zarr {zarr_version} untested. Last tested: {max_tested}")
```

#### **1.2 Zarr Utility Patching**
```python
def patch_zarr_util_json():
    """Patch zarr.util.json_dumps and json_loads with tuple preservation"""
    
    # Store originals
    zarr.util._original_json_dumps = zarr.util.json_dumps
    zarr.util._original_json_loads = zarr.util.json_loads
    
    # Replace with enhanced versions
    zarr.util.json_dumps = enhanced_zarr_json_dumps
    zarr.util.json_loads = enhanced_zarr_json_loads
```

#### **1.3 Metadata Method Patching**
```python
def patch_zarr_v3_serialization():
    """Patch Zarr v3 metadata serialization methods"""
    
    # Patch ArrayV3Metadata
    original_array_to_buffer = zarr.core.metadata.v3.ArrayV3Metadata.to_buffer_dict
    zarr.core.metadata.v3.ArrayV3Metadata.to_buffer_dict = enhanced_array_to_buffer_dict
    
    # Patch GroupV3Metadata  
    original_group_to_buffer = zarr.core.metadata.v3.GroupV3Metadata.to_buffer_dict
    zarr.core.metadata.v3.GroupV3Metadata.to_buffer_dict = enhanced_group_to_buffer_dict

def patch_zarr_v3_deserialization():
    """Patch Zarr v3 metadata deserialization methods"""
    
    # Patch ArrayV3Metadata.from_dict
    original_array_from_dict = zarr.core.metadata.v3.ArrayV3Metadata.from_dict
    zarr.core.metadata.v3.ArrayV3Metadata.from_dict = enhanced_array_from_dict
    
    # Patch GroupV3Metadata.from_dict
    original_group_from_dict = zarr.core.metadata.v3.GroupV3Metadata.from_dict  
    zarr.core.metadata.v3.GroupV3Metadata.from_dict = enhanced_group_from_dict
```

### **Phase 2: Advanced Zarr Version Management**
**Goal:** Automated CI/CD for Zarr compatibility testing

#### **2.1 GitHub Actions CI Strategy**
```yaml
# .github/workflows/zarr-compatibility.yml
name: Zarr Compatibility Check
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly on 1st
  workflow_dispatch:

jobs:
  test-zarr-versions:
    strategy:
      matrix:
        zarr-version: [
          "3.0.0", "3.0.1", "3.0.2", "3.0.3", 
          "3.0.4", "3.0.5", "3.0.6", "3.0.7", "3.0.8"
        ]
    steps:
      - name: Test zarrcompatibility with Zarr ${{ matrix.zarr-version }}
      - name: Update supported_zarr_versions.json
      - name: Create auto-PR if new version works
```

#### **2.2 Auto-Update Mechanism**
- Monthly CI checks latest Zarr releases
- Tests run automatically against new versions
- `supported_zarr_versions.json` updated automatically  
- README and docs updated with compatibility info
- Auto-patch releases for version support updates

### **Phase 3: Comprehensive Testing**
**Goal:** Bulletproof testing covering all scenarios

#### **3.1 Test Categories**

##### **Isolation Tests** (Critical!)
```python
def test_global_json_unaffected():
    """Ensure global json module remains completely unchanged"""
    import json
    original_dumps = json.dumps
    original_loads = json.loads
    
    # Enable our patching
    import zarrcompatibility as zc
    zc.enable_zarr_serialization()
    
    # Verify global json is untouched
    assert json.dumps is original_dumps
    assert json.loads is original_loads
    assert json.dumps((1,0)) == "[1, 0]"  # Standard tuple->list behavior

def test_other_libraries_unaffected():
    """Test that common libraries work normally after our patching"""
    import requests, pandas, numpy
    # ... test that these are unaffected
    
def test_import_order_independence():
    """Test all possible import orders work correctly"""
    # Test various import sequences
```

##### **Functionality Tests**
```python
def test_zarr_tuple_preservation_end_to_end():
    """Test complete tuple preservation in Zarr workflow"""
    
def test_zarr_complex_types():
    """Test datetime, enum, UUID, dataclass in Zarr metadata"""
    
def test_zarr_nested_structures():
    """Test complex nested data structures with tuples"""
```

##### **Multi-Version Tests**
```python
# Load from supported_zarr_versions.json
ZARR_VERSIONS = load_supported_versions()

@pytest.mark.parametrize("zarr_version", ZARR_VERSIONS)  
def test_with_zarr_version(zarr_version):
    """Test compatibility across all supported Zarr versions"""
```

#### **3.2 Test Execution Framework**
```python
# tests/conftest.py
def pytest_configure(config):
    """Configure pytest for multiple execution modes"""
    
# Command line execution support
if __name__ == "__main__":
    # Support: python test_*.py -v
    pytest.main([__file__] + sys.argv[1:])
```

### **Phase 4: Documentation & Migration**
**Goal:** Professional documentation and smooth migration

#### **4.1 Module Documentation**
```python
"""
Zarr-focused JSON serialization enhancement for Python scientific computing.

This module provides enhanced JSON serialization capabilities specifically for Zarr
metadata storage, solving the tuple-to-list conversion problem and adding support
for additional Python types, while maintaining complete isolation from the global
JSON module.

🎯 **Key Features:**
    - Tuple preservation in Zarr metadata (tuples stay tuples!)
    - Support for datetime, enum, UUID, dataclass, complex, decimal types
    - Zero side effects on global JSON or other libraries  
    - Import order independence
    - Professional-grade production safety
    - Zarr v3 optimized (v2 not supported)

🚀 **Quick Start:**
    >>> import zarrcompatibility as zc
    >>> import zarr
    >>> import tempfile
    >>> 
    >>> # One-time setup
    >>> zc.enable_zarr_serialization()
    >>> 
    >>> # Tuples now preserved in Zarr!
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
    ...     group.attrs["version"] = (2, 1, 0)  # Stays as tuple!
    ...     group.store.close()
    ...     
    ...     reloaded = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
    ...     assert reloaded.attrs["version"] == (2, 1, 0)
    ...     assert isinstance(reloaded.attrs["version"], tuple)  # ✅

🔒 **Safety Guarantees:**
    - Global json.dumps/loads remain completely unchanged
    - Other libraries (requests, pandas, numpy) unaffected
    - Import order doesn't matter
    - No unexpected side effects in your application

🏗️ **Architecture:**
    This module works by patching only Zarr's internal JSON serialization
    methods, creating a clean separation between Zarr operations and the
    rest of your Python environment.

📦 **Supported Types in Zarr Metadata:**
    - tuple: (1, 2, 3) → preserved as tuple
    - datetime: datetime.now() → ISO string, restored as datetime
    - Enum: MyEnum.VALUE → enum value, restored as enum  
    - UUID: uuid4() → string, restored as UUID
    - dataclass: @dataclass objects → dict, restored as dataclass
    - complex: 1+2j → {"real": 1, "imag": 2}, restored as complex
    - bytes: b"data" → base64 string, restored as bytes
    - Decimal: Decimal("1.23") → string, restored as Decimal

⚙️ **Requirements:**
    - Python 3.8+
    - Zarr 3.0.0+ (v2 not supported)
    - See supported_zarr_versions.json for tested versions

👥 **Migration from v2.0:**
    Replace enable_universal_serialization() with enable_zarr_serialization()
    
    # Old (v2.0 - deprecated):
    zc.enable_universal_serialization()  # ❌ Too invasive
    
    # New (v2.1 - recommended):  
    zc.enable_zarr_serialization()       # ✅ Zarr-only, safe

📋 **Version:** 2.1.0
📧 **Author:** F. Herbrand  
📄 **License:** MIT
🔗 **Repository:** [Add repository URL]
📚 **Documentation:** [Add docs URL]
"""
```

#### **4.2 Migration Guide for zarrwlr**
```python
# zarrwlr migration (breaking change acceptable)

# Before (v2.0):
import zarrcompatibility as zc
zc.enable_universal_serialization()

# After (v2.1):  
import zarrcompatibility as zc
zc.enable_zarr_serialization()  # Much safer!
```

---

## 🎛️ **Technical Implementation Details**

### **Tuple Preservation Mechanism**
**Keep existing:** `{"__type__": "tuple", "__data__": [...]}`  
**Rationale:** Proven to work, explicit, handles edge cases

### **Enhanced JSON Functions**
```python
def enhanced_zarr_json_dumps(obj, **kwargs):
    """Enhanced json_dumps for Zarr with tuple preservation"""
    converted = convert_tuples_recursive(obj)
    return original_zarr_json_dumps(converted, **kwargs)

def enhanced_zarr_json_loads(s, **kwargs):  
    """Enhanced json_loads for Zarr with tuple restoration"""
    data = original_zarr_json_loads(s, **kwargs)
    return restore_tuples_recursive(data)
```

### **Error Handling Strategy**
```python
def validate_zarr_version():
    """Robust Zarr version checking with helpful error messages"""
    try:
        import zarr
        version = zarr.__version__
        
        if not version.startswith("3."):
            raise ImportError(
                f"zarrcompatibility v2.1 requires Zarr v3.0+, found v{version}. "
                f"For Zarr v2, please downgrade to zarrcompatibility v2.0 or upgrade Zarr."
            )
            
        if version not in KNOWN_WORKING_VERSIONS:
            warnings.warn(
                f"Zarr v{version} not tested with zarrcompatibility. "
                f"Last tested version: {MAX_TESTED_VERSION}. "
                f"Consider upgrading zarrcompatibility or downgrading Zarr."
            )
            
    except ImportError as e:
        raise ImportError(
            "zarrcompatibility requires Zarr to be installed. "
            "Install with: pip install zarr>=3.0.0"
        ) from e
```

---

## 📋 **Implementation Checklist**

### **Phase 1: Core Implementation** ✅ Ready to implement
- [ ] Create enhanced_zarr_json_dumps/loads functions
- [ ] Implement patch_zarr_util_json()  
- [ ] Implement patch_zarr_v3_serialization()
- [ ] Implement patch_zarr_v3_deserialization()
- [ ] Create enable_zarr_serialization() main function
- [ ] Remove all global JSON patching code
- [ ] Add Zarr version validation
- [ ] Create supported_zarr_versions.json

### **Phase 2: Testing** ✅ Architecture defined
- [ ] Write isolation tests (global JSON unaffected)
- [ ] Write functionality tests (tuple preservation works)
- [ ] Write multi-version tests (multiple Zarr versions)
- [ ] Implement command-line test execution
- [ ] Add verbose mode support (-v flag)
- [ ] Create pytest configuration

### **Phase 3: CI/CD** 🔄 Future implementation  
- [ ] Create GitHub Actions workflow
- [ ] Implement monthly Zarr version checking
- [ ] Auto-update supported_zarr_versions.json
- [ ] Auto-generate compatibility documentation
- [ ] Auto-create patch releases for new versions

### **Phase 4: Documentation** ✅ Architecture defined
- [ ] Write comprehensive module docstring  
- [ ] Add NumPy-style docstrings to all functions
- [ ] Create migration guide for zarrwlr
- [ ] Update README.md with new API
- [ ] Document supported Zarr versions

### **Phase 5: Release** ✅ Ready for planning
- [ ] Update zarrwlr to use new API
- [ ] Test end-to-end with zarrwlr
- [ ] Create v2.1.0 release notes
- [ ] Deploy v2.1.0 release

---

## 🎯 **Success Criteria**

### **Must Have (MVP)**
1. ✅ **Zero Global Pollution:** Global json module completely unaffected
2. ✅ **Tuple Preservation:** Tuples preserved in Zarr metadata end-to-end
3. ✅ **Import Independence:** Works regardless of import order
4. ✅ **Library Isolation:** requests, pandas, numpy remain unaffected
5. ✅ **zarrwlr Integration:** zarrwlr works with new API

### **Should Have**  
1. ✅ **Multi-Type Support:** datetime, enum, UUID, dataclass work
2. ✅ **Version Management:** Clean Zarr version compatibility checking
3. ✅ **Professional Docs:** Production-ready documentation
4. ✅ **Comprehensive Tests:** Cover all edge cases and scenarios

### **Could Have (Future)**
1. 🔄 **Auto-CI:** Automated Zarr version compatibility testing
2. 🔄 **Performance Metrics:** Benchmark Zarr-only vs global patching
3. 🔄 **Extended Types:** Support for more complex Python types

---

## ⚡ **Next Steps**

1. **Start Implementation:** Begin with Phase 1 core implementation
2. **Test Frequently:** Run isolation tests early and often  
3. **Validate with zarrwlr:** Test integration throughout development
4. **Document as We Go:** Keep documentation synchronized with code

---

## 🎉 **Expected Outcome**

A **professional-grade**, **production-safe** zarrcompatibility v2.1 that:
- Solves the tuple preservation problem in Zarr
- Has zero side effects on the broader Python ecosystem  
- Works reliably across different import orders and library combinations
- Provides a foundation for future scientific Python workflows
- Demonstrates best practices for library patching without global pollution

**Result:** Scientific users can finally use tuples in Zarr metadata without fear! 🚀