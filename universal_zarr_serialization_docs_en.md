# Universal Zarr Serialization - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Installation and Quick Start](#installation-and-quick-start)
4. [Core Functions](#core-functions)
5. [Mixin Classes](#mixin-classes)
6. [Advanced Features](#advanced-features)
7. [Usage Examples](#usage-examples)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Universal Zarr Serialization Module** is a complete, production-ready solution for JSON serialization of arbitrary Python objects with special focus on Zarr compatibility. It provides 10 intelligent serialization strategies, comprehensive error handling, and both automatic and manual control.

### Why This Module?
- **Universal**: Works with ANY Python class
- **Intelligent**: 10 fallback strategies for maximum compatibility
- **Safe**: Circular reference protection and robust error handling
- **Flexible**: Automatic and manual modes
- **Zarr-optimized**: Specifically developed for Zarr workflows

---

## Key Features

### 🚀 **Universal Compatibility**
- Regular Python Classes
- Dataclasses (with/without @dataclass)
- Enums of all types
- Built-in Types (datetime, UUID, Decimal, bytes, complex)
- Nested structures
- Lists, Dictionaries, Sets
- Custom Objects with own serialization methods

### 🛡️ **Robustness**
- Circular Reference Detection
- Exception-tolerant serialization
- Performance-optimized for large objects
- Memory-efficient recursive processing

### 🎛️ **Flexibility**
- Global activation (Monkey-Patching)
- Mixin classes for object-oriented usage
- Explicit-Control Functions
- Class Decorators
- Custom Serialization Hooks

---

## Installation and Quick Start

### Installation
```python
# Copy module to your project directory
# universal_zarr_serialization.py
```

### Fastest Start (1 line)
```python
import universal_zarr_serialization as uzs
uzs.enable_universal_serialization()

# Done! All classes now work with JSON and Zarr
```

### Example
```python
import json
import zarr
from datetime import datetime
from enum import Enum

class Status(Enum):
    READY = "ready"
    PROCESSING = "processing"

class MyProject:
    def __init__(self, name, status, created):
        self.name = name
        self.status = status
        self.created = created

project = MyProject("Test", Status.READY, datetime.now())

# Works automatically after uzs.enable_universal_serialization()
json_str = json.dumps(project)
print(json_str)  # Fully serialized!

# Zarr Integration
group = zarr.open_group("data.zarr", mode="w")
group.attrs["project"] = project  # Works!
```

---

## Core Functions

### `serialize_object(obj)`
**The core serialization function with 10 intelligent strategies:**

```python
def serialize_object(obj):
    # Strategy 1: Basic JSON types (str, int, float, bool, None)
    # Strategy 2: __json__() method (highest priority)
    # Strategy 3: to_dict() method
    # Strategy 4: dataclasses.asdict()
    # Strategy 5: Enum.value
    # Strategy 6: Built-in types (datetime, UUID, Decimal, bytes, complex)
    # Strategy 7: __dict__ attributes
    # Strategy 8: Iterables (lists, tuples, sets)
    # Strategy 9: Mappings (dictionaries)
    # Strategy 10: String fallback
```

**Example:**
```python
import universal_zarr_serialization as uzs

class ComplexClass:
    def __init__(self):
        self.data = {"nested": True}
        self.items = [1, 2, 3]

obj = ComplexClass()
serialized = uzs.serialize_object(obj)
print(serialized)  # {'data': {'nested': True}, 'items': [1, 2, 3]}
```

### `deserialize_object(data, target_class=None)`
**Intelligent deserialization:**

```python
# Automatic deserialization
data = {"name": "test", "value": 42}
obj = uzs.deserialize_object(data, MyClass)

# Works with nested structures
nested_data = {"items": [{"name": "item1"}, {"name": "item2"}]}
result = uzs.deserialize_object(nested_data)
```

### `enable_universal_serialization()`
**Global activation:**

```python
uzs.enable_universal_serialization()
# From now on, json.dumps() works with all objects automatically

# Undo:
uzs.disable_universal_serialization()
```

---

## Mixin Classes

### `JSONSerializable`
**Base mixin for JSON functionality:**

```python
class MyClass(uzs.JSONSerializable):
    def __init__(self, name, value):
        self.name = name
        self.value = value

obj = MyClass("test", 42)

# Available methods:
obj.to_dict()       # {'name': 'test', 'value': 42}
obj.to_json()       # '{"name": "test", "value": 42}'
obj.__json__()      # {'name': 'test', 'value': 42}

# Class methods:
MyClass.from_dict({"name": "restored", "value": 100})
MyClass.from_json('{"name": "restored", "value": 100}')
```

### `ZarrCompatible`
**Extended Zarr-specific functionality:**

```python
class AudioSettings(uzs.ZarrCompatible):
    def __init__(self, bitrate, format, channels):
        self.bitrate = bitrate
        self.format = format
        self.channels = channels

settings = AudioSettings(320, "FLAC", 2)

# Zarr-specific methods:
attrs_dict = settings.to_zarr_attrs()
AudioSettings.from_zarr_attrs(attrs_dict)

# Direct Zarr integration:
import zarr
group = zarr.open_group("audio.zarr", mode="w")
settings.save_to_zarr_group(group, "audio_settings")
loaded_settings = AudioSettings.load_from_zarr_group(group, "audio_settings")
```

---

## Advanced Features

### `@make_serializable` Decorator
**Make classes serializable without inheritance:**

```python
@uzs.make_serializable
class ExistingClass:
    def __init__(self, data):
        self.data = data

obj = ExistingClass("test")
obj.to_json()  # Works automatically!
```

### `prepare_for_zarr(obj)`
**Explicit Zarr preparation:**

```python
class ComplexObject:
    def __init__(self):
        self.timestamp = datetime.now()
        self.settings = AudioSettings(320, "MP3", 2)

obj = ComplexObject()
zarr_ready = uzs.prepare_for_zarr(obj)
# Guaranteed Zarr-compatible, even without global activation
```

### `test_serialization(obj, verbose=True)`
**Serialization testing:**

```python
class TestClass:
    def __init__(self):
        self.value = "test"

obj = TestClass()
success = uzs.test_serialization(obj, verbose=True)
# Output:
# ✅ Serialization test passed for TestClass
#    Original: <TestClass object>
#    Serialized: {'value': 'test'}
#    Deserialized: <TestClass object>
```

---

## Usage Examples

### Example 1: Audio Processing Pipeline
```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import zarr
import universal_zarr_serialization as uzs

uzs.enable_universal_serialization()

class AudioFormat(Enum):
    WAV = "wav"
    FLAC = "flac"
    MP3 = "mp3"

@dataclass
class AudioMetadata:
    title: str
    artist: str
    duration: float
    sample_rate: int

class AudioProcessor(uzs.ZarrCompatible):
    def __init__(self, input_format, output_format, quality):
        self.input_format = input_format
        self.output_format = output_format
        self.quality = quality
        self.processed_files = []
        self.created_at = datetime.now()
    
    def add_file(self, filename, metadata):
        self.processed_files.append({
            "filename": filename,
            "metadata": metadata,
            "processed_at": datetime.now()
        })

# Usage
processor = AudioProcessor(
    input_format=AudioFormat.WAV,
    output_format=AudioFormat.FLAC,
    quality="high"
)

metadata = AudioMetadata("Song Title", "Artist", 180.5, 44100)
processor.add_file("song.wav", metadata)

# Zarr storage
root = zarr.open_group("audio_project.zarr", mode="w")
processor.save_to_zarr_group(root, "processor_config")

# Loading
loaded_processor = AudioProcessor.load_from_zarr_group(root, "processor_config")
```

### Example 2: Scientific Data Analysis
```python
import numpy as np
from typing import List, Dict, Any

class ExperimentConfig(uzs.JSONSerializable):
    def __init__(self, name: str, parameters: Dict[str, float]):
        self.name = name
        self.parameters = parameters
        self.created_at = datetime.now()
        self.results = []
    
    def add_result(self, measurement: float, conditions: Dict[str, Any]):
        self.results.append({
            "measurement": measurement,
            "conditions": conditions,
            "timestamp": datetime.now()
        })

class Experiment(uzs.ZarrCompatible):
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.data_arrays = {}
        self.analysis_results = {}
    
    def store_data(self, name: str, data: np.ndarray):
        self.data_arrays[name] = {
            "shape": data.shape,
            "dtype": str(data.dtype),
            "stored_at": datetime.now()
        }

# Usage
config = ExperimentConfig("Temperature Study", {"temp_min": 20.0, "temp_max": 80.0})
config.add_result(45.2, {"humidity": 60, "pressure": 1013})

experiment = Experiment(config)
experiment.store_data("temperature_readings", np.random.random((100, 10)))

# Complete Zarr storage
zarr_group = zarr.open_group("experiment.zarr", mode="w")
experiment.save_to_zarr_group(zarr_group)

# Configuration is automatically JSON-serialized and stored in Zarr!
```

### Example 3: Custom Serialization Hooks
```python
class DatabaseConnection(uzs.JSONSerializable):
    def __init__(self, host, port, database, username):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self._password = "secret"  # Should not be serialized
        self._connection = None
    
    def __json__(self):
        """Custom serialization - exclude sensitive data"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "connection_type": "postgresql",
            "_serialized_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return cls(data["host"], data["port"], data["database"], data["username"])

# Usage
db = DatabaseConnection("localhost", 5432, "mydb", "user")
json_str = db.to_json()
# Password is not included in JSON!

restored_db = DatabaseConnection.from_json(json_str)
```

---

## Best Practices

### 1. Global Activation at Program Start
```python
# At the beginning of your main.py or __init__.py
import universal_zarr_serialization as uzs
uzs.enable_universal_serialization()
```

### 2. Mixin Classes for New Classes
```python
# For new classes
class MyNewClass(uzs.ZarrCompatible):
    pass
```

### 3. Custom __json__ for Sensitive Data
```python
class SecureClass:
    def __json__(self):
        # Only serialize public data
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}
```

### 4. Test Before Production
```python
# Test your critical classes
critical_obj = MyCriticalClass()
success = uzs.test_serialization(critical_obj)
assert success, "Serialization must work for critical objects"
```

### 5. Separate Zarr Attributes vs Arrays
```python
# Configuration/Metadata → attrs
group.attrs["config"] = my_config_object

# Large data → Arrays
group.create_dataset("data", data=large_numpy_array)
```

---

## API Reference

### Core Functions

#### `serialize_object(obj: Any) -> Any`
Serializes any Python object to JSON-compatible data.

#### `deserialize_object(data: Any, target_class: Optional[Type] = None) -> Any`
Deserializes JSON data back to Python objects.

#### `enable_universal_serialization() -> None`
Enables universal serialization globally through monkey-patching.

#### `disable_universal_serialization() -> None`
Disables universal serialization and restores original behavior.

### Utility Functions

#### `make_serializable(cls: Type) -> Type`
Class decorator that adds JSON serialization methods to a class.

#### `is_json_serializable(obj: Any) -> bool`
Checks if an object is JSON-serializable.

#### `prepare_for_zarr(obj: Any) -> Any`
Explicitly prepares an object for Zarr storage.

#### `test_serialization(obj: Any, verbose: bool = True) -> bool`
Tests serialization/deserialization of an object.

### Mixin Classes

#### `JSONSerializable`
Base mixin with JSON serialization methods:
- `__json__()` - JSON representation
- `to_dict()` - Dictionary conversion
- `to_json(**kwargs)` - JSON string
- `from_dict(cls, data)` - Create from dictionary
- `from_json(cls, json_str)` - Create from JSON string

#### `ZarrCompatible(JSONSerializable)`
Extended Zarr-specific functionality:
- `to_zarr_attrs()` - Zarr attributes dictionary
- `from_zarr_attrs(cls, attrs)` - Create from Zarr attributes
- `save_to_zarr_group(zarr_group, attr_name)` - Save to Zarr group
- `load_from_zarr_group(cls, zarr_group, attr_name)` - Load from Zarr group

---

## Troubleshooting

### Problem: Circular References
**Symptom:** RecursionError or "Maximum recursion depth exceeded"
**Solution:** 
```python
class Parent:
    def __json__(self):
        return {
            "name": self.name,
            "child_count": len(self.children)
            # No direct child references!
        }
```

### Problem: Performance with Large Objects
**Symptom:** Slow serialization
**Solution:**
```python
class LargeClass:
    def __json__(self):
        # Only serialize summary
        return {
            "summary": f"Large object with {len(self.data)} items",
            "timestamp": datetime.now().isoformat()
        }
```

### Problem: Zarr AttributeError when Loading
**Symptom:** Loaded objects are dictionaries, not original classes
**Solution:**
```python
# Reconstruction helper function
def reconstruct_from_zarr(zarr_group, attr_name, target_class):
    attrs = zarr_group.attrs[attr_name]
    if hasattr(target_class, 'from_zarr_attrs'):
        return target_class.from_zarr_attrs(attrs)
    elif hasattr(target_class, 'from_dict'):
        return target_class.from_dict(attrs)
    else:
        return target_class(**attrs)
```

### Problem: Enum Serialization Issues
**Symptom:** Enums not properly serialized
**Solution:**
```python
class MyEnum(Enum):
    VALUE1 = "value1"
    
    def __json__(self):
        return self.value  # Explicit control
```

### Problem: DateTime Timezone Issues
**Symptom:** Timezone information lost
**Solution:**
```python
class TimestampClass:
    def __json__(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "timezone": str(self.timestamp.tzinfo) if self.timestamp.tzinfo else "UTC"
        }
```

### Problem: Large Nested Objects
**Symptom:** Memory issues or slow performance
**Solution:**
```python
class OptimizedClass:
    def __json__(self):
        # Serialize only essential data
        return {
            "id": self.id,
            "summary": self.get_summary(),
            # Skip heavy nested objects
            "nested_count": len(self.nested_objects) if self.nested_objects else 0
        }
```

### Problem: Custom Object Types Not Recognized
**Symptom:** Objects serialized as strings
**Solution:**
```python
# Add custom strategy to your class
class SpecialClass:
    def __json__(self):
        return {
            "_type": "SpecialClass",
            "data": self.special_data,
            "metadata": self.get_metadata()
        }
    
    @classmethod
    def from_json(cls, data):
        if isinstance(data, dict) and data.get("_type") == "SpecialClass":
            obj = cls()
            obj.special_data = data["data"]
            obj.load_metadata(data["metadata"])
            return obj
        return data
```

---

## Advanced Usage Patterns

### Pattern 1: Hierarchical Configuration Management
```python
class ProjectConfig(uzs.ZarrCompatible):
    def __init__(self):
        self.database = DatabaseConnection("localhost", 5432, "proj", "user")
        self.processing = AudioProcessor(AudioFormat.WAV, AudioFormat.FLAC, "high")
        self.experiment = ExperimentConfig("Audio Analysis", {"threshold": 0.8})
    
    def save_complete_config(self, zarr_path):
        """Save entire project configuration to Zarr"""
        root = zarr.open_group(zarr_path, mode="w")
        self.save_to_zarr_group(root, "project_config")
        return root

config = ProjectConfig()
zarr_group = config.save_complete_config("project.zarr")
```

### Pattern 2: Versioned Serialization
```python
class VersionedClass(uzs.JSONSerializable):
    VERSION = "2.1.0"
    
    def __json__(self):
        return {
            "_version": self.VERSION,
            "_class": self.__class__.__name__,
            "data": self.data,
            "created_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_json(cls, data):
        version = data.get("_version", "1.0.0")
        if version != cls.VERSION:
            data = cls._migrate_from_version(data, version)
        return cls(data["data"])
    
    @classmethod
    def _migrate_from_version(cls, data, from_version):
        """Handle version migrations"""
        # Migration logic here
        return data
```

### Pattern 3: Plugin Architecture
```python
class PluginBase(uzs.JSONSerializable):
    def __json__(self):
        return {
            "plugin_type": self.__class__.__name__,
            "config": self.get_config()
        }

class AudioPlugin(PluginBase):
    def get_config(self):
        return {"format": self.format, "quality": self.quality}

class VideoPlugin(PluginBase):
    def get_config(self):
        return {"resolution": self.resolution, "codec": self.codec}

# Plugin factory
def load_plugin_from_zarr(zarr_group, plugin_name):
    plugin_data = zarr_group.attrs[plugin_name]
    plugin_type = plugin_data["plugin_type"]
    
    if plugin_type == "AudioPlugin":
        return AudioPlugin.from_dict(plugin_data)
    elif plugin_type == "VideoPlugin":
        return VideoPlugin.from_dict(plugin_data)
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")
```

---

**Version:** 1.0.0  
**Python:** 3.7+  
**Zarr:** 2.x+  
**License:** MIT

**The Universal Zarr Serialization Module - Your complete solution for Python object serialization in Zarr.**