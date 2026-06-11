# engine/tests/utils.py
# All documentation, docstrings, and code comments are strictly in English.

from pathlib import Path

class MockAssetLoader:
    """Helper class to load static Doxygen XML assets for testing.
    
    This class dynamically resolves paths relative to the current file position,
    ensuring 100% portability across environments.
    """
    
    def __init__(self) -> None:
        # Resolve the tests/assets/doxygen directory relative to this file's directory
        self.doxygen_assets_dir = Path(__file__).parent / "assets" / "doxygen"
        
    def load_xml(self, filename: str) -> str:
        """Loads a mock Doxygen XML asset by filename and returns its content as a string.
        
        Args:
            filename: The name of the XML file under tests/assets/doxygen/ (e.g. 'index.xml').
            
        Returns:
            The string content of the XML file.
            
        Raises:
            FileNotFoundError: If the asset file cannot be located.
        """
        file_path = self.doxygen_assets_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Mock asset file not found: {file_path}")
            
        return file_path.read_text(encoding="utf-8")
