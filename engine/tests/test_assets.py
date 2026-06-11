# engine/tests/test_assets.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from tests.utils import MockAssetLoader

def test_mock_asset_loader_xml_loading():
    """Verify that MockAssetLoader successfully loads the mock XML assets."""
    loader = MockAssetLoader()
    
    # Assert loading of the primary index and class files
    index_xml = loader.load_xml("index.xml")
    assert isinstance(index_xml, str)
    assert len(index_xml) > 0
    assert "<doxygenindex" in index_xml
    
    class_def = loader.load_xml("class_definition.xml")
    assert isinstance(class_def, str)
    assert len(class_def) > 0
    assert "<compounddef" in class_def

def test_mock_asset_loader_special_assets():
    """Verify loading of newer assets for macros and SWIG filters."""
    loader = MockAssetLoader()
    
    class_macros = loader.load_xml("class_with_macros.xml")
    assert "NWDBEXPORT" in class_macros
    
    class_swig = loader.load_xml("class_swig_wrapper.xml")
    assert "swigCPtr" in class_swig
