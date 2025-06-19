def test_zarrwlr_scenario():
    """
    Test the original zarrwlr problem is solved.
    
    This test verifies that tuple types are preserved when storing
    and retrieving metadata from Zarr arrays, eliminating the need
    for manual type conversion workarounds.
    """
    import tempfile
    import zarr
    import zarrcompatibility as zc
    
    # Enable universal serialization (with automatic tuple preservation)
    zc.enable_universal_serialization()
    
    # Simulate zarrwlr Config class
    class Config:
        original_audio_group_version = (1, 0)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Zarr group with tuple metadata
        audio_group = zarr.open_group(f"{tmpdir}/audio.zarr", mode="w")
        audio_group.attrs["version"] = Config.original_audio_group_version
        
        # Reload and test - should work without manual conversion
        reloaded = zarr.open_group(f"{tmpdir}/audio.zarr", mode="r")
        stored_version = reloaded.attrs["version"]
        
        # These assertions should now pass without workarounds
        assert isinstance(stored_version, tuple), f"Expected tuple, got {type(stored_version)}"
        assert stored_version == Config.original_audio_group_version
        
        # Test the comparison that was failing before
        if stored_version == Config.original_audio_group_version:
            print("✓ Version matches - no manual conversion needed!")
        else:
            raise AssertionError("Version comparison failed")
    
    print("✓ zarrwlr scenario test passed - tuple preservation working!")


def test_basic_tuple_roundtrip():
    """Test basic tuple serialization and deserialization."""
    import json
    import zarrcompatibility as zc
    
    zc.enable_universal_serialization()
    
    # Test simple tuple
    original = (1, 0)
    serialized = json.dumps(original)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized, tuple), f"Expected tuple, got {type(deserialized)}"
    assert deserialized == original
    print(f"✓ Basic tuple test: {original} -> {serialized} -> {deserialized}")
    
    # Test nested structure
    data = {
        "version": (1, 0),
        "coordinates": (10.5, 20.3),
        "items": [1, 2, 3]  # Should remain list
    }
    
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized["version"], tuple)
    assert isinstance(deserialized["coordinates"], tuple)
    assert isinstance(deserialized["items"], list)
    print("✓ Nested structure test passed")


if __name__ == "__main__":
    test_basic_tuple_roundtrip()
    test_zarrwlr_scenario()
    