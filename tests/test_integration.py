#!/usr/bin/env python3
"""
Integration tests for zarrcompatibility v2.1.

This test module verifies that zarrcompatibility integrates correctly with
zarrwlr and other real-world usage scenarios. These tests focus on the
complete workflow from zarrwlr through zarrcompatibility to Zarr.

Test Categories:
    1. zarrwlr integration tests
    2. Real-world workflow simulation
    3. Performance and compatibility
    4. Migration testing (v2.0 to v2.1)
    5. Error scenarios and recovery

The tests can be run with pytest or directly from command line:
    python test_integration.py -v

Author: F. Herbrand
License: MIT
"""

import json
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
from enum import Enum

# Test framework setup
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

try:
    import zarr
    ZARR_AVAILABLE = True
except ImportError:
    ZARR_AVAILABLE = False

# Simulate zarrwlr usage patterns
class DataType(Enum):
    EXPERIMENTAL = "experimental"
    SIMULATION = "simulation"
    ANALYSIS = "analysis"


class SimulatedZarrwlr:
    """Simulated zarrwlr-like class for integration testing."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.metadata = {}
        self.arrays = {}
    
    def set_metadata(self, **kwargs):
        """Set metadata (typical zarrwlr pattern)."""
        self.metadata.update(kwargs)
    
    def create_dataset(self, name: str, shape: tuple, **attrs):
        """Create dataset with attributes (typical zarrwlr pattern)."""
        import numpy as np
        
        # Create Zarr array
        zarr_path = self.base_path / f"{name}.zarr"
        arr = zarr.open_array(str(zarr_path), mode="w", 
                             shape=shape, dtype="f4")
        
        # Add attributes
        arr.attrs.update(attrs)
        
        # Store some test data
        arr[:] = np.random.random(shape)
        
        self.arrays[name] = arr
        return arr
    
    def save_experiment(self):
        """Save experiment metadata (typical zarrwlr pattern)."""
        # Create main group
        group_path = self.base_path / "experiment.zarr"
        group = zarr.open_group(str(group_path), mode="w")
        
        # Store metadata with typical zarrwlr patterns
        group.attrs.update(self.metadata)
        
        # Create references to arrays
        for name, arr in self.arrays.items():
            group.attrs[f"{name}_info"] = {
                "path": f"{name}.zarr",
                "shape": arr.shape,
                "dtype": str(arr.dtype)
            }
        
        group.store.close()
        return group_path
    
    def load_experiment(self, group_path: Path):
        """Load experiment (typical zarrwlr pattern)."""
        group = zarr.open_group(str(group_path), mode="r")
        
        # Load metadata
        self.metadata = dict(group.attrs)
        
        # Load array references
        for key, value in group.attrs.items():
            if key.endswith("_info") and isinstance(value, dict):
                array_name = key[:-5]  # Remove "_info"
                if "path" in value:
                    arr_path = self.base_path / value["path"]
                    if arr_path.exists():
                        self.arrays[array_name] = zarr.open_array(str(arr_path), mode="r")
        
        return group


class TestZarrwlrIntegration:
    """Test integration with zarrwlr-like workflows."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
        
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_basic_zarrwlr_workflow(self):
        """Test basic zarrwlr-like workflow with tuple preservation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate zarrwlr workflow
            experiment = SimulatedZarrwlr(tmpdir)
            
            # Set experiment metadata with tuples (typical pattern)
            experiment.set_metadata(
                version=(2, 1, 0),
                experiment_id="EXP_001",
                data_type=DataType.EXPERIMENTAL,
                created=datetime.now(),
                dimensions=(100, 200, 50),
                processing_steps=("calibration", "filtering", "analysis"),
                parameters={
                    "sampling_rate": (1000, 2000),
                    "frequency_range": (10.0, 1000.0)
                }
            )
            
            # Create datasets with tuple metadata
            dataset1 = experiment.create_dataset(
                "raw_data", 
                shape=(100, 200),
                original_shape=(1000, 2000),
                processing_chain=[
                    {"step": "downsample", "factor": (10, 10)},
                    {"step": "normalize", "range": (0.0, 1.0)}
                ]
            )
            
            dataset2 = experiment.create_dataset(
                "processed_data",
                shape=(50, 100),
                derived_from="raw_data",
                transformation_matrix=((1, 0), (0, 1)),
                roi_coordinates=(25, 50, 75, 100)
            )
            
            # Save experiment
            group_path = experiment.save_experiment()
            
            # Verify save worked
            assert group_path.exists()
            
            # Load experiment back (simulate zarrwlr reload)
            new_experiment = SimulatedZarrwlr(tmpdir)
            new_experiment.load_experiment(group_path)
            
            # Verify metadata preserved with correct types
            metadata = new_experiment.metadata
            
            assert metadata["version"] == (2, 1, 0)
            assert isinstance(metadata["version"], tuple)
            
            assert metadata["data_type"] == DataType.EXPERIMENTAL
            assert isinstance(metadata["data_type"], DataType)
            
            assert isinstance(metadata["created"], datetime)
            
            assert metadata["dimensions"] == (100, 200, 50)
            assert isinstance(metadata["dimensions"], tuple)
            
            assert metadata["processing_steps"] == ("calibration", "filtering", "analysis")
            assert isinstance(metadata["processing_steps"], tuple)
            
            # Verify nested parameter tuples
            params = metadata["parameters"]
            assert params["sampling_rate"] == (1000, 2000)
            assert isinstance(params["sampling_rate"], tuple)
            assert params["frequency_range"] == (10.0, 1000.0)
            assert isinstance(params["frequency_range"], tuple)
            
            # Verify array metadata preserved
            raw_data = new_experiment.arrays["raw_data"]
            assert raw_data.attrs["original_shape"] == (1000, 2000)
            assert isinstance(raw_data.attrs["original_shape"], tuple)
            
            chain = raw_data.attrs["processing_chain"]
            assert chain[0]["factor"] == (10, 10)
            assert isinstance(chain[0]["factor"], tuple)
            assert chain[1]["range"] == (0.0, 1.0)
            assert isinstance(chain[1]["range"], tuple)
            
            processed_data = new_experiment.arrays["processed_data"]
            assert processed_data.attrs["transformation_matrix"] == ((1, 0), (0, 1))
            assert isinstance(processed_data.attrs["transformation_matrix"], tuple)
            assert processed_data.attrs["roi_coordinates"] == (25, 50, 75, 100)
            assert isinstance(processed_data.attrs["roi_coordinates"], tuple)
    
    def test_complex_experiment_structure(self):
        """Test complex experiment structure with hierarchical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create complex nested structure (advanced zarrwlr pattern)
            base_group = zarr.open_group(f"{tmpdir}/complex_experiment.zarr", mode="w")
            
            # Main experiment metadata
            base_group.attrs.update({
                "experiment_info": {
                    "name": "Complex Experiment",
                    "version": (3, 0, 1),
                    "created": datetime.now(),
                    "coordinates": {
                        "origin": (0.0, 0.0, 0.0),
                        "extent": (100.0, 200.0, 50.0),
                        "resolution": (0.1, 0.1, 0.5)
                    }
                }
            })
            
            # Create experimental groups
            trials_group = base_group.create_group("trials")
            analysis_group = base_group.create_group("analysis")
            
            # Add trial data
            for trial_id in range(3):
                trial_group = trials_group.create_group(f"trial_{trial_id:03d}")
                trial_group.attrs.update({
                    "trial_id": trial_id,
                    "parameters": {
                        "stimulus_position": (trial_id * 10, trial_id * 20),
                        "duration": (1.0, 2.0, 3.0)[trial_id],
                        "conditions": ("baseline", "stimulus", "recovery")
                    },
                    "timestamps": tuple(range(trial_id * 100, (trial_id + 1) * 100, 10))
                })
                
                # Create trial array
                trial_array = trial_group.create_array(
                    "data", 
                    shape=(100, 50), 
                    dtype="f4"
                )
                trial_array.attrs["roi_bounds"] = (0, 50, 0, 100)
                trial_array.attrs["sampling_info"] = {
                    "rate": 1000.0,
                    "channels": (1, 2, 3, 4),
                    "gain": (1.0, 1.0, 2.0, 2.0)
                }
            
            # Add analysis results
            analysis_group.attrs.update({
                "summary_statistics": {
                    "mean_response": (10.5, 20.3, 15.7),
                    "std_response": (2.1, 3.4, 2.8),
                    "peak_times": (0.15, 0.23, 0.18)
                },
                "processing_info": {
                    "filter_params": {
                        "highpass": 0.1,
                        "lowpass": 100.0,
                        "order": 4,
                        "window": ("hann", 1024)
                    }
                }
            })
            
            base_group.store.close()
            
            # Reload and verify complex structure
            reloaded_group = zarr.open_group(f"{tmpdir}/complex_experiment.zarr", mode="r")
            
            # Verify main experiment info
            exp_info = reloaded_group.attrs["experiment_info"]
            assert exp_info["version"] == (3, 0, 1)
            assert isinstance(exp_info["version"], tuple)
            
            coords = exp_info["coordinates"]
            assert coords["origin"] == (0.0, 0.0, 0.0)
            assert isinstance(coords["origin"], tuple)
            assert coords["extent"] == (100.0, 200.0, 50.0)
            assert isinstance(coords["extent"], tuple)
            assert coords["resolution"] == (0.1, 0.1, 0.5)
            assert isinstance(coords["resolution"], tuple)