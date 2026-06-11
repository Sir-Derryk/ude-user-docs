# engine/tests/test_cli.py
# All documentation, docstrings, and code comments are strictly in English.

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from ude.cli import main, find_product_json, run_pipeline
from ude.interfaces import ParserError


def test_find_product_json_success(tmp_path):
    """Verify find_product_json successfully locates product.json by ascending directories."""
    lvl1 = tmp_path / "lvl1"
    lvl2 = lvl1 / "lvl2"
    lvl2.mkdir(parents=True)

    product_file = tmp_path / "product.json"
    product_file.write_text('{"product_name": "TestProduct"}', encoding="utf-8")

    found = find_product_json(lvl2)
    assert found == product_file


def test_find_product_json_not_found(tmp_path):
    """Verify find_product_json returns None if no product.json exists in parents."""
    lvl1 = tmp_path / "lvl1"
    lvl1.mkdir()
    found = find_product_json(lvl1)
    assert found is None


def test_cli_help():
    """Verify CLI prints help and exits with code 0 on --help."""
    code = main(["--help"])
    assert code == 0


def test_cli_missing_config():
    """Verify CLI exits with non-zero on missing required --config argument."""
    code = main([])
    assert code != 0


def test_cli_config_not_found(tmp_path, capsys):
    """Verify CLI returns non-zero when config file does not exist."""
    non_existent = tmp_path / "missing_config.json"
    code = main(["--config", str(non_existent)])
    assert code != 0
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_cli_invalid_json_config(tmp_path, capsys):
    """Verify CLI returns non-zero when config file contains invalid JSON."""
    config_file = tmp_path / "invalid_config.json"
    config_file.write_text("{invalid", encoding="utf-8")
    code = main(["--config", str(config_file)])
    assert code != 0
    captured = capsys.readouterr()
    assert "Failed to parse JSON config" in captured.err


def test_cli_missing_src_dir(tmp_path, capsys):
    """Verify CLI returns non-zero when no source directory is specified."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"output_dir": "out"}', encoding="utf-8")
    code = main(["--config", str(config_file)])
    assert code != 0
    captured = capsys.readouterr()
    assert "No source directory specified" in captured.err


def test_cli_invalid_format(tmp_path, capsys):
    """Verify CLI returns non-zero on unsupported format overrides."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"src_dir": ".", "output_dir": "out"}', encoding="utf-8")
    code = main(["--config", str(config_file), "--format", "unsupported_fmt"])
    assert code != 0
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err


def test_cli_pipeline_success_with_direct_xml(tmp_path):
    """Verify end-to-end pipeline success using pre-existing XML directory."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": str(assets_dir.resolve()),
            "output_dir": "my_output",
            "collector": {
                "type": "cpp"
            },
            "renderer": {
                "type": "hugo_markdown"
            }
        }),
        encoding="utf-8"
    )

    product_file = tmp_path / "product.json"
    product_file.write_text('{"product_name": "MyAwesomeProduct"}', encoding="utf-8")

    output_dir = tmp_path / "my_output"

    code = main(["--config", str(config_file)])
    assert code == 0

    assert output_dir.exists()
    my_class_file = output_dir / "class_MyClass.md"
    assert my_class_file.exists()



def test_cli_pipeline_html_and_overrides(tmp_path):
    """Verify pipeline output with format override to html and output override."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": str(assets_dir.resolve()),
            "output_dir": "temp_out",
        }),
        encoding="utf-8"
    )

    override_out = tmp_path / "override_html_out"

    code = main([
        "--config", str(config_file),
        "--output", str(override_out),
        "--format", "html"
    ])
    assert code == 0

    assert override_out.exists()
    assert (override_out / "index.html").exists()


@patch("ude.collectors.doxygen.DoxygenXmlCollector.collect")
@patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup")
def test_cli_pipeline_with_collector_run(mock_cleanup, mock_collect, tmp_path):
    """Verify pipeline triggers collector run when src_dir doesn't contain index.xml."""
    src_dir = tmp_path / "code"
    src_dir.mkdir()
    (src_dir / "main.cpp").write_text("void foo();", encoding="utf-8")

    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    mock_collect.return_value = assets_dir

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": "code",
            "output_dir": "out",
            "collector": {
                "type": "cpp"
            }
        }),
        encoding="utf-8"
    )

    code = main(["--config", str(config_file)])
    assert code == 0

    mock_collect.assert_called_once()
    mock_cleanup.assert_called_once()


def test_cli_compilation_error_handling(tmp_path, capsys):
    """Verify compilation exceptions are caught, printed, and process exits with 1."""
    empty_dir = tmp_path / "empty_assets"
    empty_dir.mkdir()

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": str(empty_dir.resolve()),
            "output_dir": "out",
            "collector": {
                "doxyfile_template": "non_existent_doxy"
            }
        }),
        encoding="utf-8"
    )

    code = main(["--config", str(config_file)])
    assert code == 1
    captured = capsys.readouterr()
    assert "Compilation error" in captured.err or "Error" in captured.err


def test_cli_input_override(tmp_path):
    """Verify that specifying --input override sets the src_dir correctly."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": "non_existent_placeholder",
            "output_dir": "my_output",
        }),
        encoding="utf-8"
    )
    code = main([
        "--config", str(config_file),
        "--input", str(assets_dir.resolve())
    ])
    assert code == 0
    assert (tmp_path / "my_output").exists()


def test_cli_empty_src_dir_list(tmp_path, capsys):
    """Verify that an empty list for src_dir returns error status 1."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"src_dir": [], "output_dir": "out"}), encoding="utf-8")
    code = main(["--config", str(config_file)])
    assert code == 1
    captured = capsys.readouterr()
    assert "No source directory specified in configuration or overrides." in captured.err


def test_cli_unsupported_format_in_config(tmp_path, capsys):
    """Verify that an unsupported renderer type in config file returns error status 1."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": ".",
            "output_dir": "out",
            "renderer": {"type": "unsupported_fmt"}
        }),
        encoding="utf-8"
    )
    code = main(["--config", str(config_file)])
    assert code == 1
    captured = capsys.readouterr()
    assert "Unsupported format 'unsupported_fmt'" in captured.err


def test_cli_malformed_product_json(tmp_path, capsys):
    """Verify malformed product.json emits warning but compilation succeeds."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": str(assets_dir.resolve()),
            "output_dir": "out",
        }),
        encoding="utf-8"
    )
    product_file = tmp_path / "product.json"
    product_file.write_text("{malformed", encoding="utf-8")

    code = main(["--config", str(config_file)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Warning: Failed to parse product.json" in captured.err


@patch("ude.collectors.doxygen.DoxygenXmlCollector.collect")
@patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup")
def test_cli_cleanup_exception(mock_cleanup, mock_collect, tmp_path, capsys):
    """Verify that an exception in collector cleanup outputs a warning and exits with 0."""
    src_dir = tmp_path / "code"
    src_dir.mkdir()
    (src_dir / "main.cpp").write_text("void foo();", encoding="utf-8")

    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    mock_collect.return_value = assets_dir
    mock_cleanup.side_effect = Exception("Mock cleanup failure")

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": "code",
            "output_dir": "out",
            "collector": {
                "type": "cpp"
            }
        }),
        encoding="utf-8"
    )

    code = main(["--config", str(config_file)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Warning: Failed to clean up temporary directory" in captured.err

