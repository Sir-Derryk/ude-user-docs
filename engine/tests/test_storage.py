# engine/tests/test_storage.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from pathlib import Path
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity
from ude.storage import save_compressed_ir, load_compressed_ir

def test_gzip_compression_transparent_io(tmp_path):
    """Verify that save_compressed_ir and load_compressed_ir work transparently with Gzip.
    
    This includes checking the Gzip magic header bytes to ensure compression actually occurred.
    """
    # Create a simple test catalog
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="TestNamespace",
                classes=[
                    ClassEntity(
                        name="TestClass",
                        fully_qualified_name="TestNamespace::TestClass",
                        docstring="A test class for Gzip storage testing."
                    )
                ]
            )
        ]
    )
    
    temp_file = tmp_path / "temp_ir.json.gz"
    
    # Save the catalog
    save_compressed_ir(catalog, temp_file)
    
    # Verify file existence and Gzip magic number (1f 8b)
    assert temp_file.exists()
    with open(temp_file, "rb") as f:
        magic_bytes = f.read(2)
        assert magic_bytes == b"\x1f\x8b", "File is not a valid Gzip archive (missing magic bytes)"
        
    # Load it back
    loaded_catalog = load_compressed_ir(temp_file)
    
    # Verify equivalence
    assert len(loaded_catalog.namespaces) == 1
    assert loaded_catalog.namespaces[0].name == "TestNamespace"
    assert len(loaded_catalog.namespaces[0].classes) == 1
    assert loaded_catalog.namespaces[0].classes[0].name == "TestClass"
    assert loaded_catalog.namespaces[0].classes[0].fully_qualified_name == "TestNamespace::TestClass"

def test_load_non_existent_file_raises_error(tmp_path):
    """Verify that loading a non-existent file raises FileNotFoundError."""
    non_existent_file = tmp_path / "does_not_exist.json.gz"
    with pytest.raises(FileNotFoundError):
        load_compressed_ir(non_existent_file)
