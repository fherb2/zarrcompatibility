# zarrcompatibility v3.0

**Zarr-focused JSON serialization enhancement for Python scientific computing**

🎯 **Solve the tuple-to-list conversion problem in Zarr metadata with zero side effects!**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Zarr](https://img.shields.io/badge/zarr-3.0+-green.svg)](https://zarr.readthedocs.io)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Quick Start

```python
import zarrcompatibility as zc
import zarr
import tempfile

# One-time setup - patches only Zarr, not global JSON!
zc.enable_zarr_serialization()

# Now tuples are preserved in Zarr metadata! 🎉
with tempfile.TemporaryDirectory() as tmpdir:
    group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
    group.attrs["version"] = (3, 0, 0)  # Stays as tuple!
    group.attrs["shape"] = (100, 200, 300)  # Also preserved!
    group.store.close()
    
    reloaded = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
    assert reloaded.attrs["version"] == (3, 0, 0)
    assert isinstance(reloaded.attrs["version"], tuple)  # ✅ Still a tuple!
    assert isinstance(reloaded.attrs["shape"], tuple)    # ✅ Also a tuple!
```

## 🎯 What Problem Does This Solve?

**The Problem:** Zarr converts tuples to lists in metadata, breaking semantic meaning:

```python
# Without zarrcompatibility
group.attrs["shape"] = (100, 200)      # Input: tuple
loaded_shape = group.attrs["shape"]    # Output: [100, 200] - now a list! 😞

# With zarrcompatibility v3.0
zc.enable_zarr_serialization()
group.attrs["shape"] = (100, 200)      # Input: tuple  
loaded_shape = group.attrs["shape"]    # Output: (100, 200) - still a tuple! 🎉
```

**Why This Matters:**
- 🔬 **Scientific Computing:** Shapes, coordinates, and dimensions should stay as tuples
- 🧮 **Mathematical Operations:** `numpy.array(shape)` expects tuples for certain operations
- 🎯 **Type Safety:** Your code expects tuples, not lists
- 📊 **Data Integrity:** Preserve the original semantic meaning of your metadata

## ✨ Key Features

### 🎯 **Surgical Precision - Zarr Only**
- ✅ Patches **only Zarr's internal JSON methods**
- ✅ Global `json.dumps`/`json.loads` remain **completely unchanged**
- ✅ Other libraries (requests, pandas, numpy) **unaffected**
- ✅ Import order **doesn't matter**
- ✅ **Zero side effects** on your application

### 🚀 **Enhanced Type Support**
Beyond tuples, zarrcompatibility v3.0 supports:

| Type | Example | Preserved As |
|------|---------|--------------|
| `tuple` | `(1, 2, 3)` | Exact tuple |
| `datetime` | `datetime.now()` | datetime object |
| `Enum` | `MyEnum.VALUE` | Enum instance |
| `UUID` | `uuid4()` | UUID object |
| `dataclass` | `@dataclass` objects | dataclass instance |
| `complex` | `1+2j` | complex number |
| `bytes` | `b"data"` | bytes object |
| `Decimal` | `Decimal("1.23")` | Decimal object |

### 🛡️ **Production-Grade Safety**
- 🔒 **No global pollution** - json module stays pristine
- 🎯 **Isolated impact** - only affects Zarr operations
- 🔄 **Reversible** - can disable/restore original behavior
- 🧪 **Extensively tested** - comprehensive test suite
- 📋 **Version managed** - automated Zarr compatibility checking

## 📦 Installation

```bash
pip install zarrcompatibility
```

**Requirements:**
- Python 3.8+
- Zarr 3.0.0+ (v2 not supported)

## 🏗️ Architecture: Why It's Safe

zarrcompatibility v3.0 uses **surgical patching** - it only modifies Zarr's internal JSON handling:

```python
# What we patch (Zarr internals only):
zarr.core.metadata.v3.V3JsonEncoder        # ✅ Zarr-specific
zarr.core.metadata.v3.ArrayV3Metadata      # ✅ Zarr-specific  
zarr.core.group.GroupMetadata              # ✅ Zarr-specific

# What we DON'T touch (stays unchanged):
json.dumps                                  # ❌ Never touched
json.loads                                  # ❌ Never touched
requests.post                               # ❌ Unaffected
pandas.to_json                              # ❌ Unaffected
```

This approach ensures **complete isolation** - your other libraries work exactly as before.

## 🧪 Advanced Usage

### Complex Scientific Metadata

```python
import zarrcompatibility as zc
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# Enable once per session
zc.enable_zarr_serialization()

class ExperimentType(Enum):
    CONTROL = "control"
    TREATMENT = "treatment"

@dataclass
class ExperimentConfig:
    name: str
    version: tuple
    created: datetime

# Rich metadata with preserved types
group = zarr.open_group("experiment.zarr", mode="w")
group.attrs.update({
    "config": ExperimentConfig(
        name="Trial_001", 
        version=(2, 1, 0),
        created=datetime.now()
    ),
    "experiment_type": ExperimentType.TREATMENT,
    "roi_coordinates": (10, 20, 100, 200),
    "sampling_rates": (1000, 2000, 4000),
    "analysis_params": {
        "window_size": (64, 64),
        "overlap": (32, 32),
        "frequencies": (10.0, 100.0, 1000.0)
    }
})

# All types preserved perfectly on reload! 🎉
```

### Integration with Scientific Workflows

```python
# Perfect for numpy array metadata
array = zarr.open_array("data.zarr", mode="w", shape=(1000, 2000), dtype="f4")
array.attrs.update({
    "original_shape": (10000, 20000),      # Tuple preserved
    "downsampling_factor": (10, 10),       # Tuple preserved  
    "roi_bounds": (100, 900, 200, 1800),   # Tuple preserved
    "processing_timestamp": datetime.now(), # datetime preserved
})

# Downstream code can rely on correct types
original_shape = array.attrs["original_shape"]
assert isinstance(original_shape, tuple)  # ✅ Always passes
height, width = original_shape             # ✅ Clean unpacking
```

## 🔧 Testing Your Installation

```python
import zarrcompatibility as zc

# Enable and test
zc.enable_zarr_serialization()

# Test tuple preservation
result = zc.test_serialization((1, 2, 3))
assert result == True  # Should pass

# Test with your own objects
from datetime import datetime
result = zc.test_serialization(datetime.now())
assert result == True  # Should pass

# Check Zarr version compatibility
versions = zc.get_supported_zarr_versions()
print(f"Recommended Zarr version: {versions['recommended']}")
```

## 📊 Compatibility Matrix

| zarrcompatibility | Zarr Versions | Python | Status |
|------------------|---------------|---------|--------|
| v3.0.0 | 3.0.0 - 3.0.8 | 3.8+ | ✅ Supported |

For detailed compatibility information:
```python
import zarrcompatibility as zc
print(zc.get_supported_zarr_versions())
```

## 🔄 Migration from v2.x

**v3.0 is a complete rewrite** with breaking changes for better safety:

```python
# OLD (v2.x - deprecated):
import zarrcompatibility as zc
zc.enable_universal_serialization()  # ❌ Too invasive, affected global JSON

# NEW (v3.0 - recommended):
import zarrcompatibility as zc  
zc.enable_zarr_serialization()       # ✅ Zarr-only, completely safe
```

**Benefits of upgrading:**
- ✅ **Zero side effects** on other libraries
- ✅ **Import order independence** 
- ✅ **Better error messages** and debugging
- ✅ **Automated version management**
- ✅ **Production-grade reliability**

## 🧪 Testing

Run the comprehensive test suite:

```bash
# From project root
python -m pytest tests/ -v

# Or run specific test categories
python tests/test_isolation.py       # Test global JSON isolation
python tests/test_functionality.py  # Test core functionality  
python tests/test_integration.py    # Test real-world workflows
```

## 🎯 Use Cases

**Perfect for:**
- 🔬 **Scientific computing** workflows with Zarr
- 📊 **Data analysis** pipelines using zarr arrays
- 🧬 **Bioinformatics** applications storing metadata
- 🌊 **Climate/weather** data with coordinate tuples
- 🎥 **Image processing** with shape/ROI tuples
- 🚀 **Machine learning** experiments with hyperparameter tuples

**Real-world applications:**
- **Microscopy data:** ROI coordinates as tuples
- **Satellite imagery:** Geographic bounds as tuples  
- **Time series:** Sampling parameters as tuples
- **Experimental data:** Trial configurations with rich metadata

## ⚠️ Important Notes

1. **Zarr v2 Not Supported:** This version only works with Zarr v3.0+
2. **One-time Setup:** Call `enable_zarr_serialization()` once per session
3. **Safe to Call Multiple Times:** No harm in calling enable multiple times
4. **Debugging:** Use `zc.print_patch_status()` to check what's patched

## 🆘 Troubleshooting

### Issue: "Zarr version not supported"
```python
import zarrcompatibility as zc
versions = zc.get_supported_zarr_versions() 
print(f"Install Zarr: pip install zarr=={versions['recommended']}")
```

### Issue: "Tuples still becoming lists"
```python
import zarrcompatibility as zc
# Make sure you've enabled it:
zc.enable_zarr_serialization()

# Check if patching worked:
zc.print_patch_status()
```

### Issue: "Other libraries acting weird"
This shouldn't happen with v3.0! If it does:
```python
import json
# Verify global JSON is unchanged:
assert json.dumps((1,2)) == "[1, 2]"  # Should still be a list

# If this fails, please file a bug report!
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Development setup:**
```bash
git clone https://github.com/your-org/zarrcompatibility
cd zarrcompatibility
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Zarr developers** for the excellent array storage library
- **Scientific Python community** for feedback and testing
- **Contributors** who helped identify edge cases and improve robustness

## 📞 Support

- 🐛 **Bug reports:** [GitHub Issues](https://github.com/your-org/zarrcompatibility/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/your-org/zarrcompatibility/discussions)  
- 📧 **Email:** [maintainer@example.com](mailto:maintainer@example.com)

---

**zarrcompatibility v3.0** - Finally, tuples that stay tuples in Zarr! 🎉