# engine/tests/test_harness.py
# All documentation, docstrings, and code comments are strictly in English.

import ude

def test_package_import_and_version():
    """Verify that the package can be successfully imported and has the correct version."""
    assert hasattr(ude, "__version__")
    assert ude.__version__ == "0.1.0"
