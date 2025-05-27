# Universal Zarr Serialization - Vollständige Dokumentation

## Inhaltsverzeichnis
1. [Überblick](#überblick)
2. [Hauptmerkmale](#hauptmerkmale)
3. [Installation und Schnellstart](#installation-und-schnellstart)
4. [Kern-Funktionen](#kern-funktionen)
5. [Mixin-Klassen](#mixin-klassen)
6. [Erweiterte Features](#erweiterte-features)
7. [Anwendungsbeispiele](#anwendungsbeispiele)
8. [Best Practices](#best-practices)
9. [API-Referenz](#api-referenz)
10. [Fehlerbehebung](#fehlerbehebung)

---

## Überblick

Das **Universal Zarr Serialization Modul** ist eine vollständige, produktionsreife Lösung für JSON-Serialisierung beliebiger Python-Objekte mit speziellem Fokus auf Zarr-Kompatibilität. Es bietet 10 intelligente Serialisierungsstrategien, umfassende Fehlerbehandlung und sowohl automatische als auch manuelle Kontrolle.

### Warum dieses Modul?
- **Universell**: Funktioniert mit JEDER Python-Klasse
- **Intelligent**: 10 Fallback-Strategien für maximale Kompatibilität
- **Sicher**: Circular Reference Protection und robuste Fehlerbehandlung
- **Flexibel**: Automatische und manuelle Modi
- **Zarr-optimiert**: Speziell für Zarr-Workflows entwickelt

---

## Hauptmerkmale

### 🚀 **Universelle Kompatibilität**
- Regular Python Classes
- Dataclasses (mit/ohne @dataclass)
- Enums aller Art
- Built-in Types (datetime, UUID, Decimal, bytes, complex)
- Verschachtelte Strukturen
- Listen, Dictionaries, Sets
- Custom Objects mit eigenen Serialisierungsmethoden

### 🛡️ **Robustheit**
- Circular Reference Detection
- Exception-tolerante Serialisierung
- Performance-optimiert für große Objekte
- Memory-effiziente rekursive Verarbeitung

### 🎛️ **Flexibilität**
- Globale Aktivierung (Monkey-Patching)
- Mixin-Klassen für objekt-orientierte Nutzung
- Explicit-Control Functions
- Class Decorators
- Custom Serialization Hooks

---

## Installation und Schnellstart

### Installation
```python
# Modul in Ihr Projekt-Verzeichnis kopieren
# universal_zarr_serialization.py
```

### Schnellster Start (1 Zeile)
```python
import universal_zarr_serialization as uzs
uzs.enable_universal_serialization()

# Fertig! Alle Klassen funktionieren jetzt mit JSON und Zarr
```

### Beispiel
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

# Funktioniert automatisch nach uzs.enable_universal_serialization()
json_str = json.dumps(project)
print(json_str)  # Vollständig serialisiert!

# Zarr Integration
group = zarr.open_group("data.zarr", mode="w")
group.attrs["project"] = project  # Funktioniert!
```

---

## Kern-Funktionen

### `serialize_object(obj)`
**Die Kern-Serialisierungsfunktion mit 10 intelligenten Strategien:**

```python
def serialize_object(obj):
    # Strategie 1: Basic JSON types (str, int, float, bool, None)
    # Strategie 2: __json__() method (highest priority)
    # Strategie 3: to_dict() method
    # Strategie 4: dataclasses.asdict()
    # Strategie 5: Enum.value
    # Strategie 6: Built-in types (datetime, UUID, Decimal, bytes, complex)
    # Strategie 7: __dict__ attributes
    # Strategie 8: Iterables (lists, tuples, sets)
    # Strategie 9: Mappings (dictionaries)
    # Strategie 10: String fallback
```

**Beispiel:**
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
**Intelligente Deserialisierung:**

```python
# Automatische Deserialisierung
data = {"name": "test", "value": 42}
obj = uzs.deserialize_object(data, MyClass)

# Funktioniert mit verschachtelten Strukturen
nested_data = {"items": [{"name": "item1"}, {"name": "item2"}]}
result = uzs.deserialize_object(nested_data)
```

### `enable_universal_serialization()`
**Globale Aktivierung:**

```python
uzs.enable_universal_serialization()
# Ab jetzt funktioniert json.dumps() mit allen Objekten automatisch

# Rückgängig machen:
uzs.disable_universal_serialization()
```

---

## Mixin-Klassen

### `JSONSerializable`
**Basis-Mixin für JSON-Funktionalität:**

```python
class MyClass(uzs.JSONSerializable):
    def __init__(self, name, value):
        self.name = name
        self.value = value

obj = MyClass("test", 42)

# Verfügbare Methoden:
obj.to_dict()       # {'name': 'test', 'value': 42}
obj.to_json()       # '{"name": "test", "value": 42}'
obj.__json__()      # {'name': 'test', 'value': 42}

# Klassen-Methoden:
MyClass.from_dict({"name": "restored", "value": 100})
MyClass.from_json('{"name": "restored", "value": 100}')
```

### `ZarrCompatible`
**Erweiterte Zarr-spezifische Funktionalität:**

```python
class AudioSettings(uzs.ZarrCompatible):
    def __init__(self, bitrate, format, channels):
        self.bitrate = bitrate
        self.format = format
        self.channels = channels

settings = AudioSettings(320, "FLAC", 2)

# Zarr-spezifische Methoden:
attrs_dict = settings.to_zarr_attrs()
AudioSettings.from_zarr_attrs(attrs_dict)

# Direkte Zarr-Integration:
import zarr
group = zarr.open_group("audio.zarr", mode="w")
settings.save_to_zarr_group(group, "audio_settings")
loaded_settings = AudioSettings.load_from_zarr_group(group, "audio_settings")
```

---

## Erweiterte Features

### `@make_serializable` Decorator
**Klassen ohne Vererbung serialisierbar machen:**

```python
@uzs.make_serializable
class ExistingClass:
    def __init__(self, data):
        self.data = data

obj = ExistingClass("test")
obj.to_json()  # Funktioniert automatisch!
```

### `prepare_for_zarr(obj)`
**Explizite Zarr-Vorbereitung:**

```python
class ComplexObject:
    def __init__(self):
        self.timestamp = datetime.now()
        self.settings = AudioSettings(320, "MP3", 2)

obj = ComplexObject()
zarr_ready = uzs.prepare_for_zarr(obj)
# Garantiert Zarr-kompatibel, auch ohne globale Aktivierung
```

### `test_serialization(obj, verbose=True)`
**Serialisierungs-Test:**

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

## Anwendungsbeispiele

### Beispiel 1: Audio-Processing Pipeline
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

# Verwendung
processor = AudioProcessor(
    input_format=AudioFormat.WAV,
    output_format=AudioFormat.FLAC,
    quality="high"
)

metadata = AudioMetadata("Song Title", "Artist", 180.5, 44100)
processor.add_file("song.wav", metadata)

# Zarr-Speicherung
root = zarr.open_group("audio_project.zarr", mode="w")
processor.save_to_zarr_group(root, "processor_config")

# Laden
loaded_processor = AudioProcessor.load_from_zarr_group(root, "processor_config")
```

### Beispiel 2: Wissenschaftliche Datenanalyse
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

# Verwendung
config = ExperimentConfig("Temperature Study", {"temp_min": 20.0, "temp_max": 80.0})
config.add_result(45.2, {"humidity": 60, "pressure": 1013})

experiment = Experiment(config)
experiment.store_data("temperature_readings", np.random.random((100, 10)))

# Vollständige Zarr-Speicherung
zarr_group = zarr.open_group("experiment.zarr", mode="w")
experiment.save_to_zarr_group(zarr_group)

# Die Konfiguration ist automatisch JSON-serialisiert in Zarr gespeichert!
```

### Beispiel 3: Custom Serialization Hooks
```python
class DatabaseConnection(uzs.JSONSerializable):
    def __init__(self, host, port, database, username):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self._password = "secret"  # Soll nicht serialisiert werden
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

# Verwendung
db = DatabaseConnection("localhost", 5432, "mydb", "user")
json_str = db.to_json()
# Password ist nicht im JSON enthalten!

restored_db = DatabaseConnection.from_json(json_str)
```

---

## Best Practices

### 1. Globale Aktivierung am Programmstart
```python
# Am Anfang Ihrer main.py oder __init__.py
import universal_zarr_serialization as uzs
uzs.enable_universal_serialization()
```

### 2. Mixin-Klassen für neue Klassen
```python
# Für neue Klassen
class MyNewClass(uzs.ZarrCompatible):
    pass
```

### 3. Custom __json__ für sensitive Daten
```python
class SecureClass:
    def __json__(self):
        # Nur öffentliche Daten serialisieren
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_')}
```

### 4. Testen vor Produktion
```python
# Testen Sie Ihre kritischen Klassen
critical_obj = MyCriticalClass()
success = uzs.test_serialization(critical_obj)
assert success, "Serialization must work for critical objects"
```

### 5. Zarr-Attribute vs Arrays trennen
```python
# Konfiguration/Metadaten → attrs
group.attrs["config"] = my_config_object

# Große Daten → Arrays
group.create_dataset("data", data=large_numpy_array)
```

---

## API-Referenz

### Kern-Funktionen

#### `serialize_object(obj: Any) -> Any`
Serialisiert ein beliebiges Python-Objekt zu JSON-kompatiblen Daten.

#### `deserialize_object(data: Any, target_class: Optional[Type] = None) -> Any`
Deserialisiert JSON-Daten zurück zu Python-Objekten.

#### `enable_universal_serialization() -> None`
Aktiviert universelle Serialisierung global durch Monkey-Patching.

#### `disable_universal_serialization() -> None`
Deaktiviert universelle Serialisierung und stellt ursprüngliches Verhalten wieder her.

### Utility-Funktionen

#### `make_serializable(cls: Type) -> Type`
Class-Decorator, der JSON-Serialisierungsmethoden zu einer Klasse hinzufügt.

#### `is_json_serializable(obj: Any) -> bool`
Überprüft, ob ein Objekt JSON-serialisierbar ist.

#### `prepare_for_zarr(obj: Any) -> Any`
Bereitet ein Objekt explizit für Zarr-Speicherung vor.

#### `test_serialization(obj: Any, verbose: bool = True) -> bool`
Testet Serialisierung/Deserialisierung eines Objekts.

### Mixin-Klassen

#### `JSONSerializable`
Basis-Mixin mit JSON-Serialisierungsmethoden:
- `__json__()` - JSON-Repräsentation
- `to_dict()` - Dictionary-Konvertierung
- `to_json(**kwargs)` - JSON-String
- `from_dict(cls, data)` - Aus Dictionary erstellen
- `from_json(cls, json_str)` - Aus JSON-String erstellen

#### `ZarrCompatible(JSONSerializable)`
Erweiterte Zarr-spezifische Funktionalität:
- `to_zarr_attrs()` - Zarr-Attribute Dictionary
- `from_zarr_attrs(cls, attrs)` - Aus Zarr-Attributen erstellen
- `save_to_zarr_group(zarr_group, attr_name)` - In Zarr-Gruppe speichern
- `load_from_zarr_group(cls, zarr_group, attr_name)` - Aus Zarr-Gruppe laden

---

## Fehlerbehebung

### Problem: Circular References
**Symptom:** RecursionError oder "Maximum recursion depth exceeded"
**Lösung:** 
```python
class Parent:
    def __json__(self):
        return {
            "name": self.name,
            "child_count": len(self.children)
            # Keine direkten Child-Referenzen!
        }
```

### Problem: Performance bei großen Objekten
**Symptom:** Langsame Serialisierung
**Lösung:**
```python
class LargeClass:
    def __json__(self):
        # Nur Zusammenfassung serialisieren
        return {
            "summary": f"Large object with {len(self.data)} items",
            "timestamp": datetime.now().isoformat()
        }
```

### Problem: Zarr AttributeError beim Laden
**Symptom:** Loaded objects are dictionaries, not original classes
**Lösung:**
```python
# Rekonstruktions-Hilfsfunktion
def reconstruct_from_zarr(zarr_group, attr_name, target_class):
    attrs = zarr_group.attrs[attr_name]
    if hasattr(target_class, 'from_zarr_attrs'):
        return target_class.from_zarr_attrs(attrs)
    elif hasattr(target_class, 'from_dict'):
        return target_class.from_dict(attrs)
    else:
        return target_class(**attrs)
```

### Problem: Enum serialization issues
**Symptom:** Enums not properly serialized
**Lösung:**
```python
class MyEnum(Enum):
    VALUE1 = "value1"
    
    def __json__(self):
        return self.value  # Explizite Kontrolle
```

### Problem: DateTime timezone issues
**Symptom:** Timezone information lost
**Lösung:**
```python
class TimestampClass:
    def __json__(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "timezone": str(self.timestamp.tzinfo) if self.timestamp.tzinfo else "UTC"
        }
```

---

**Version:** 1.0.0  
**Python:** 3.7+  
**Zarr:** 2.x+  
**Lizenz:** MIT

**Das Universal Zarr Serialization Modul - Ihre komplette Lösung für Python-Objekt-Serialisierung in Zarr.**