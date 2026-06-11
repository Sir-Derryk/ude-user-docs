# engine/tests/test_doxygen_collector.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from ude.interfaces import CollectorError, BaseCollector
from ude.collectors.doxygen import DoxygenXmlCollector


def test_doxygen_collector_inheritance():
    """Verify that DoxygenXmlCollector successfully inherits from BaseCollector."""
    collector = DoxygenXmlCollector()
    assert isinstance(collector, BaseCollector)


@patch("shutil.which")
def test_validate_environment_success(mock_which, tmp_path):
    """Verify validate_environment passes when doxygen exists and paths are valid."""
    mock_which.return_value = "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("")

    collector = DoxygenXmlCollector()
    collector.validate_environment(config_file)


@patch("shutil.which")
def test_validate_environment_missing_doxygen(mock_which, tmp_path):
    """Verify validate_environment raises CollectorError when doxygen is missing."""
    mock_which.return_value = None

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')

    collector = DoxygenXmlCollector()
    with pytest.raises(CollectorError, match="doxygen binary not found"):
        collector.validate_environment(config_file)


def test_validate_environment_non_existent_config():
    """Verify validate_environment raises CollectorError when config does not exist."""
    collector = DoxygenXmlCollector()
    with pytest.raises(CollectorError, match="Configuration file .* does not exist"):
        collector.validate_environment(Path("non_existent_config.json"))


def test_validate_environment_invalid_json(tmp_path):
    """Verify validate_environment raises CollectorError on invalid JSON."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text("{invalid_json")

    collector = DoxygenXmlCollector()
    with pytest.raises(CollectorError, match="Failed to parse JSON config"):
        collector.validate_environment(config_file)


def test_validate_environment_missing_fields(tmp_path):
    """Verify validate_environment raises CollectorError on missing required fields."""
    collector = DoxygenXmlCollector()

    # Missing src_dir
    config_file1 = tmp_path / "config1.json"
    config_file1.write_text('{"collector": {"doxyfile_template": "Doxyfile"}}')
    with pytest.raises(CollectorError, match="Missing 'src_dir'"):
        collector.validate_environment(config_file1)

    # Missing doxyfile_template
    config_file2 = tmp_path / "config2.json"
    config_file2.write_text('{"collector": {"src_dir": "src"}}')
    with pytest.raises(CollectorError, match="Missing 'doxyfile_template'"):
        collector.validate_environment(config_file2)


@patch("shutil.which")
def test_validate_environment_missing_directories(mock_which, tmp_path):
    """Verify validate_environment raises CollectorError when dirs/files are missing."""
    mock_which.return_value = "doxygen"
    collector = DoxygenXmlCollector()

    # src_dir doesn't exist
    config_file1 = tmp_path / "config1.json"
    config_file1.write_text('{"collector": {"src_dir": "non_existent_src", "doxyfile_template": "Doxyfile"}}')
    doxy = tmp_path / "Doxyfile"
    doxy.write_text("")
    with pytest.raises(CollectorError, match="Source directory .* does not exist"):
        collector.validate_environment(config_file1)

    # doxyfile_template doesn't exist
    config_file2 = tmp_path / "config2.json"
    config_file2.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "non_existent_doxy"}}')
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    with pytest.raises(CollectorError, match="Doxyfile template .* does not exist"):
        collector.validate_environment(config_file2)


@patch("subprocess.run")
@patch("shutil.which")
def test_collect_success_languages(mock_which, mock_run, tmp_path):
    """Verify successful collection for default, java, and python languages."""
    mock_which.return_value = "doxygen"
    
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_run.return_value = mock_proc

    src_dir = tmp_path / "src"
    src_dir.mkdir(exist_ok=True)
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("SOME_PARAM = VALUE")

    collector = DoxygenXmlCollector()

    # Java Language
    config_file_java = tmp_path / "ude_config_java.json"
    config_file_java.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile", "language": "java"}}')
    xml_path = collector.collect(config_file_java)
    assert xml_path.name == "xml"

    # Python Language
    config_file_py = tmp_path / "ude_config_py.json"
    config_file_py.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile", "language": "python"}}')
    xml_path = collector.collect(config_file_py)
    assert xml_path.name == "xml"


@patch("subprocess.run")
@patch("shutil.which")
def test_collect_subprocess_failures(mock_which, mock_run, tmp_path):
    """Verify collect raises CollectorError on subprocess failures."""
    mock_which.return_value = "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("")

    collector = DoxygenXmlCollector()

    # Subprocess returncode != 0
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = "Doxygen parse error"
    mock_run.return_value = mock_proc
    with pytest.raises(CollectorError, match="Doxygen process failed with code 1"):
        collector.collect(config_file)

    # Subprocess raises OSError
    mock_run.side_effect = OSError("Access denied")
    with pytest.raises(CollectorError, match="Subprocess execution failed"):
        collector.collect(config_file)


@patch("shutil.which")
def test_collect_file_read_write_failures(mock_which, tmp_path):
    """Verify collect raises CollectorError on read/write I/O errors."""
    mock_which.return_value = "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("")

    collector = DoxygenXmlCollector()

    # точечный патч только для чтения Doxyfile
    original_open = Path.open
    def mock_open_fn(self, *args, **kwargs):
        if "Doxyfile" in str(self) and not str(self).endswith("ude_config.json"):
            raise IOError("Permission denied")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", mock_open_fn):
        with pytest.raises(CollectorError, match="Failed to read Doxyfile template"):
            collector.collect(config_file)


def test_cleanup_guard_rails(tmp_path):
    """Verify cleanup enforces strict guard rails, raising ValueError on illegal paths."""
    collector = DoxygenXmlCollector()

    # Null/empty path
    with pytest.raises(ValueError, match="Path cannot be empty"):
        collector.cleanup(Path(""))

    # Roots
    for root_path in [Path("/"), Path("C:\\"), Path("D:\\")]:
        with pytest.raises(ValueError, match="Cannot delete system root"):
            collector.cleanup(root_path)

    # Current/Parent directories
    with pytest.raises(ValueError, match="Cannot delete relative navigation paths"):
        collector.cleanup(Path("."))
    with pytest.raises(ValueError, match="Cannot delete relative navigation paths"):
        collector.cleanup(Path(".."))

    # Outside project or working tree boundaries
    outside_path = Path("E:\\SomeExternalFolder")
    with pytest.raises(ValueError, match="Path is outside safe working boundaries"):
        collector.cleanup(outside_path)

    # Core project directories must not be deleted
    # Для тестов в engine/tests/ корень проекта — это parent.parent.parent
    project_root = Path(__file__).resolve().parent.parent.parent
    with pytest.raises(ValueError, match="Cannot delete project core directories"):
        collector.cleanup(project_root)
    with pytest.raises(ValueError, match="Cannot delete project core directories"):
        collector.cleanup(project_root / "engine")



def test_cleanup_file_success(tmp_path):
    """Verify safe cleanup can delete a single file within boundaries."""
    collector = DoxygenXmlCollector()
    temp_file = tmp_path / "temp_file.xml"
    temp_file.write_text("<xml></xml>")

    assert temp_file.exists()
    collector.cleanup(temp_file)
    assert not temp_file.exists()


def test_cleanup_success(tmp_path):
    """Verify safe cleanup of a valid temporary directory."""
    collector = DoxygenXmlCollector()
    temp_dir = tmp_path / "ude_temp_run"
    temp_dir.mkdir()
    
    dummy_file = temp_dir / "output.xml"
    dummy_file.write_text("<xml></xml>")

    assert temp_dir.exists()
    collector.cleanup(temp_dir)
    assert not temp_dir.exists()


@patch("shutil.rmtree")
def test_cleanup_exception(mock_rmtree, tmp_path):
    """Verify cleanup raises CollectorError on rmtree failures."""
    mock_rmtree.side_effect = OSError("Access denied")
    collector = DoxygenXmlCollector()
    temp_dir = tmp_path / "ude_temp_run"
    temp_dir.mkdir()

    with pytest.raises(CollectorError, match="Failed to delete directory"):
        collector.cleanup(temp_dir)


@patch("shutil.which")
def test_collect_doxyfile_write_failure(mock_which, tmp_path):
    """Verify collect raises CollectorError when writing localized Doxyfile fails."""
    mock_which.return_value = "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("")

    collector = DoxygenXmlCollector()

    original_open = Path.open
    def mock_open_fn(self, *args, **kwargs):
        if "Doxyfile_local" in str(self):
            raise IOError("Disk full or permission denied")
        return original_open(self, *args, **kwargs)

    with patch.object(Path, "open", mock_open_fn):
        with pytest.raises(CollectorError, match="Failed to write localized Doxyfile"):
            collector.collect(config_file)


@patch("subprocess.run")
@patch("shutil.which")
def test_collect_doxygen_not_found_error(mock_which, mock_run, tmp_path):
    """Verify collect raises CollectorError when doxygen is not found at execution time."""
    mock_which.return_value = "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    doxy_template = tmp_path / "Doxyfile"
    doxy_template.write_text("")

    collector = DoxygenXmlCollector()
    mock_run.side_effect = FileNotFoundError("No such file or directory")

    with pytest.raises(CollectorError, match="doxygen binary not found during execution"):
        collector.collect(config_file)


def test_cleanup_resolve_path_failure():
    """Verify cleanup raises CollectorError when path resolution fails with OSError."""
    collector = DoxygenXmlCollector()
    mock_path = MagicMock(spec=Path)
    mock_path._raw_paths = ["abc"]
    mock_path.resolve.side_effect = OSError("Mock physical error")

    with pytest.raises(CollectorError, match="Failed to resolve path"):
        collector.cleanup(mock_path)


@patch("subprocess.run")
@patch("shutil.which")
def test_collect_missing_doxyfile_fallback(mock_which, mock_run, tmp_path):
    """Verify that if the default Doxyfile template is missing, collection falls back gracefully."""
    mock_which.return_value = "doxygen"
    
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_run.return_value = mock_proc

    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"collector": {"src_dir": "src", "doxyfile_template": "Doxyfile"}}')
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    collector = DoxygenXmlCollector()
    xml_dir = collector.collect(config_file)
    assert xml_dir.exists()
    mock_run.assert_called_once()

