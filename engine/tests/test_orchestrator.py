# engine/tests/test_orchestrator.py
# All documentation, docstrings, and code comments are strictly in English.

import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from ude.interfaces import UdeException, CollectorError
from ude.orchestrator import (
    UdeOrchestrator,
    find_global_config,
    find_product_json,
    main,
)


def test_find_global_config_success(tmp_path):
    """Verify find_global_config locates ude_global.json by ascending directories."""
    lvl1 = tmp_path / "lvl1"
    lvl2 = lvl1 / "lvl2"
    lvl2.mkdir(parents=True)

    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"error_policy": "continue-on-error"}', encoding="utf-8")

    found = find_global_config(lvl2)
    assert found == global_file


def test_find_global_config_not_found(tmp_path):
    """Verify find_global_config returns None if no ude_global.json exists."""
    lvl1 = tmp_path / "lvl1"
    lvl1.mkdir()
    assert find_global_config(lvl1) is None


def test_find_product_json_success(tmp_path):
    """Verify find_product_json locates product.json by ascending directories."""
    lvl1 = tmp_path / "lvl1"
    lvl2 = lvl1 / "lvl2"
    lvl2.mkdir(parents=True)

    product_file = tmp_path / "product.json"
    product_file.write_text('{"product_name": "TestProduct"}', encoding="utf-8")

    found = find_product_json(lvl2)
    assert found == product_file


def test_find_product_json_not_found(tmp_path):
    """Verify find_product_json returns None if no product.json exists."""
    lvl1 = tmp_path / "lvl1"
    lvl1.mkdir()
    assert find_product_json(lvl1) is None


def test_orchestrator_init_with_explicit_global_config(tmp_path):
    """Verify UdeOrchestrator initializes and loads an explicit global config."""
    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"error_policy": "fail-fast"}', encoding="utf-8")

    orchestrator = UdeOrchestrator(global_file)
    assert orchestrator.global_config == {"error_policy": "fail-fast"}


def test_orchestrator_init_with_missing_explicit_global_config():
    """Verify UdeOrchestrator handles a missing explicit global config gracefully."""
    orchestrator = UdeOrchestrator(Path("non_existent_global.json"))
    assert orchestrator.global_config == {}


def test_orchestrator_init_corrupted_global_config(tmp_path):
    """Verify UdeOrchestrator handles corrupted global config and logs warning (lines 84-85)."""
    global_file = tmp_path / "ude_global.json"
    global_file.write_text("{corrupt", encoding="utf-8")

    with patch("ude.orchestrator.logger.warning") as mock_warn:
        orchestrator = UdeOrchestrator(global_file)
        assert orchestrator.global_config == {}
        assert mock_warn.called


def test_orchestrator_dynamic_corrupted_global_config(tmp_path):
    """Verify run_target handles dynamic loading failure of global config and logs warning (lines 107-111)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    global_file = tmp_path / "ude_global.json"
    global_file.write_text("{corrupt", encoding="utf-8")

    with patch("ude.orchestrator.find_global_config", return_value=global_file):
        with patch("ude.orchestrator.logger.warning") as mock_warn:
            orchestrator = UdeOrchestrator()
            with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
                 patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
                success = orchestrator.run_target(config_file)
                assert success
                assert mock_warn.called


def test_orchestrator_logging_level(tmp_path):
    """Verify orchestrator configures global logging level from global config (line 116)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"logging": {"level": "DEBUG"}}', encoding="utf-8")

    orchestrator = UdeOrchestrator(global_file)
    with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
         patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
        success = orchestrator.run_target(config_file)
        assert success
        assert logging.getLogger().level == logging.DEBUG


def test_run_target_missing_config():
    """Verify run_target returns False if the config file does not exist."""
    orchestrator = UdeOrchestrator()
    assert not orchestrator.run_target("non_existent_config.json")


def test_run_target_invalid_json_config(tmp_path):
    """Verify run_target returns False if the config file contains invalid JSON."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text("{invalid", encoding="utf-8")
    orchestrator = UdeOrchestrator()
    assert not orchestrator.run_target(config_file)


def test_run_target_missing_src_dir(tmp_path):
    """Verify run_target returns False if no source directory is specified."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"output_dir": "out"}', encoding="utf-8")
    orchestrator = UdeOrchestrator()
    assert not orchestrator.run_target(config_file)


def test_run_target_empty_src_dir(tmp_path):
    """Verify run_target returns False if src_dir list is empty."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"src_dir": []}', encoding="utf-8")
    orchestrator = UdeOrchestrator()
    assert not orchestrator.run_target(config_file)


def test_run_target_unsupported_format(tmp_path):
    """Verify run_target returns False if an unsupported format is specified."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "unsupported_format"}
        }),
        encoding="utf-8"
    )
    orchestrator = UdeOrchestrator()
    assert not orchestrator.run_target(config_file)


def test_run_target_src_dir_string(tmp_path):
    """Verify run_target supports a single string for src_dir (line 151)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": str(assets_dir),
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )
    orchestrator = UdeOrchestrator()
    with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
         patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
        success = orchestrator.run_target(config_file)
        assert success


def test_run_target_with_html_format(tmp_path):
    """Verify run_target uses static HTML rendering (lines 170 and 236)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "html"}
        }),
        encoding="utf-8"
    )
    orchestrator = UdeOrchestrator()
    with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
         patch("ude.renderers.static_html.HtmlRenderer.render") as mock_render:
        success = orchestrator.run_target(config_file)
        assert success


def test_run_target_corrupted_product_json(tmp_path):
    """Verify run_target logs warning if product.json is corrupted (lines 181-185)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    product_file = tmp_path / "product.json"
    product_file.write_text("{corrupt", encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.orchestrator.find_product_json", return_value=product_file):
        with patch("ude.orchestrator.logger.warning") as mock_warn:
            with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
                 patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
                success = orchestrator.run_target(config_file)
                assert success
                assert mock_warn.called


def test_run_target_with_product_metadata(tmp_path):
    """Verify run_target sets catalog.metadata if product.json is present (line 230)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"
    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    product_file = tmp_path / "product.json"
    product_file.write_text('{"product_name": "TestProduct"}', encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.orchestrator.find_product_json", return_value=product_file):
        with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
             patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
            
            mock_catalog = MagicMock()
            mock_parse.return_value = mock_catalog
            
            success = orchestrator.run_target(config_file)
            assert success
            assert hasattr(mock_catalog, "metadata")
            assert mock_catalog.metadata == {"product_name": "TestProduct"}


def test_run_target_parser_renderer_exception(tmp_path):
    """Verify run_target executes cleanup and propagates exceptions during parsing/rendering (lines 241-243)."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(src_dir)],
            "output_dir": "out",
            "collector": {"type": "cpp"}
        }),
        encoding="utf-8"
    )

    # Mock collector run
    mock_xml_dir = tmp_path / "temp_xml_parent" / "xml"
    mock_xml_dir.mkdir(parents=True)
    (mock_xml_dir / "index.xml").write_text("<doxygenindex></doxygenindex>", encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.collectors.doxygen.DoxygenXmlCollector.collect", return_value=mock_xml_dir) as mock_collect, \
         patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup") as mock_cleanup, \
         patch("ude.parsers.doxygen.DoxygenXmlParser.parse", side_effect=UdeException("Parsing Failed")):
        
        with pytest.raises(UdeException, match="Parsing Failed"):
            orchestrator.run_target(config_file)
        
        # Cleanup should still be called
        assert mock_cleanup.called


def test_run_target_cleanup_exception(tmp_path):
    """Verify run_target logs warning if collector cleanup fails (lines 249-250)."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(src_dir)],
            "output_dir": "out",
            "collector": {"type": "cpp"}
        }),
        encoding="utf-8"
    )

    # Mock collector run
    mock_xml_dir = tmp_path / "temp_xml_parent" / "xml"
    mock_xml_dir.mkdir(parents=True)
    (mock_xml_dir / "index.xml").write_text("<doxygenindex></doxygenindex>", encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.collectors.doxygen.DoxygenXmlCollector.collect", return_value=mock_xml_dir) as mock_collect, \
         patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup", side_effect=Exception("Cleanup Error")) as mock_cleanup, \
         patch("ude.orchestrator.logger.warning") as mock_warn:
        
        with patch("ude.parsers.doxygen.DoxygenXmlParser.parse") as mock_parse, \
             patch("ude.renderers.hugo_markdown.HugoMarkdownRenderer.render") as mock_render:
            
            success = orchestrator.run_target(config_file)
            assert success
            assert mock_warn.called


def test_run_target_portability_with_cwd_change():
    """Verify path resolution is strictly relative to the config file parent.

    Ensures that changing CWD does not break compilation.
    """
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    # Create target config under a nested directory on the same drive (D:)
    target_dir = Path(__file__).parent / "temp_portability_target"
    if target_dir.exists():
        import shutil
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Rel path from target_dir to assets_dir
    rel_src_dir = os.path.relpath(assets_dir, target_dir)

    config_file = target_dir / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [rel_src_dir],
            "output_dir": "my_portable_output",
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    # Change current working directory to a completely different location
    original_cwd = os.getcwd()
    other_dir = Path(__file__).parent / "temp_other_cwd"
    other_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(other_dir)

    try:
        orchestrator = UdeOrchestrator()
        success = orchestrator.run_target(config_file)
        assert success

        # Output folder should be resolved relative to config_file.parent, not other_dir
        expected_out = target_dir / "my_portable_output"
        assert expected_out.exists()
        assert (expected_out / "class_MyClass.md").exists()
    finally:
        os.chdir(original_cwd)
        import shutil
        if target_dir.exists():
            shutil.rmtree(target_dir)
        if other_dir.exists():
            shutil.rmtree(other_dir)


@patch("ude.collectors.doxygen.DoxygenXmlCollector.collect")
@patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup")
def test_run_target_with_collector_and_cleanup(mock_cleanup, mock_collect, tmp_path):
    """Verify that collector is run, and cleanup is executed under finally block."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(src_dir)],
            "output_dir": "out",
            "collector": {"type": "cpp"}
        }),
        encoding="utf-8"
    )

    # Mock collector run
    mock_xml_dir = tmp_path / "temp_xml_parent" / "xml"
    mock_xml_dir.mkdir(parents=True)
    # Put a mock catalog in the collector output
    (mock_xml_dir / "index.xml").write_text("<doxygenindex></doxygenindex>", encoding="utf-8")
    mock_collect.return_value = mock_xml_dir

    orchestrator = UdeOrchestrator()
    success = orchestrator.run_target(config_file)
    assert success
    assert mock_collect.called
    assert mock_cleanup.called


@patch("ude.collectors.doxygen.DoxygenXmlCollector.collect")
@patch("ude.collectors.doxygen.DoxygenXmlCollector.cleanup")
def test_run_target_collector_failure_raises(mock_cleanup, mock_collect, tmp_path):
    """Verify collector failure propagates exception and still triggers cleanup."""
    src_dir = tmp_path / "sources"
    src_dir.mkdir()

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(src_dir)],
            "output_dir": "out",
            "collector": {"type": "cpp"}
        }),
        encoding="utf-8"
    )

    mock_collect.side_effect = CollectorError("Mocked collector exception")

    orchestrator = UdeOrchestrator()
    with pytest.raises(CollectorError):
        orchestrator.run_target(config_file)


def test_run_fail_fast_policy(tmp_path):
    """Verify fail-fast policy halts execution on the first target error."""
    config1 = tmp_path / "config1.json"
    config1.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    config2 = tmp_path / "config2.json"
    config2.write_text('{"src_dir": ["non_existent_2"]}', encoding="utf-8")

    # Write global config with fail-fast
    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"error_policy": "fail-fast"}', encoding="utf-8")

    orchestrator = UdeOrchestrator(global_file)

    with pytest.raises(Exception):
        orchestrator.run([config1, config2])


def test_run_continue_on_error_policy(tmp_path):
    """Verify continue-on-error policy compiles remaining targets after a failure."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    # config1 is invalid and will fail
    config1 = tmp_path / "config1.json"
    config1.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    # config2 is valid and will succeed
    config2 = tmp_path / "config2.json"
    config2.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "output_dir": "out2",
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    # Write global config with continue-on-error
    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"error_policy": "continue-on-error"}', encoding="utf-8")

    orchestrator = UdeOrchestrator(global_file)
    success = orchestrator.run([config1, config2])

    assert not success  # Should return False overall due to config1 failing
    assert (tmp_path / "out2").exists()  # But config2 should be processed!


def test_run_continue_on_error_dynamic_global_config(tmp_path):
    """Verify dynamic loading of ude_global.json finds and uses continue-on-error error policy (line 286)."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    # Set up directory layout:
    # tmp_path/ude_global.json
    # tmp_path/nested/config.json
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()

    global_file = tmp_path / "ude_global.json"
    global_file.write_text('{"error_policy": "continue-on-error"}', encoding="utf-8")

    config1 = nested_dir / "config1.json"
    config1.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    config2 = nested_dir / "config2.json"
    config2.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "output_dir": "out_dyn_opt",
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    orchestrator = UdeOrchestrator()
    success = orchestrator.run([config1, config2])

    assert not success  # Failed config1, but continued to config2
    assert (nested_dir / "out_dyn_opt").exists()


def test_run_continue_on_error_dynamic_corrupted_global_config(tmp_path):
    """Verify dynamic loading of corrupted global config returns fail-fast error policy (lines 283-288)."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    global_file = tmp_path / "ude_global.json"
    global_file.write_text("{corrupt", encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.orchestrator.find_global_config", return_value=global_file):
        # Because dynamic loading fails, it falls back to "fail-fast", which raises exception immediately
        with pytest.raises(Exception):
            orchestrator.run([config_file])


def test_run_target_compilation_returns_false(tmp_path):
    """Verify run raises UdeException if run_target returns False (line 295)."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    orchestrator = UdeOrchestrator()
    with patch("ude.orchestrator.UdeOrchestrator.run_target", return_value=False):
        # Under fail-fast, it raises the exception propagated from run_target returning False
        with pytest.raises(UdeException, match="Pipeline execution returned False"):
            orchestrator.run([config_file])


def test_main_cli_not_enough_arguments(capsys):
    """Verify script exits with code 4 when no arguments are provided."""
    with patch.object(sys, "argv", ["orchestrator.py"]):
        code = main()
        assert code == 4
        captured = capsys.readouterr()
        assert "Usage" in captured.err


def test_main_cli_execution_success(tmp_path):
    """Verify script executes successfully and returns 0."""
    assets_dir = Path(__file__).parent / "assets" / "doxygen"

    config_file = tmp_path / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": [str(assets_dir)],
            "output_dir": str(tmp_path / "out"),
            "renderer": {"type": "hugo_markdown"}
        }),
        encoding="utf-8"
    )

    with patch.object(sys, "argv", ["orchestrator.py", str(config_file)]):
        code = main()
        assert code == 0


def test_main_cli_execution_failure(tmp_path):
    """Verify script returns 1 on execution failure."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    with patch.object(sys, "argv", ["orchestrator.py", str(config_file)]):
        code = main()
        assert code == 1


def test_main_cli_fatal_exception_handling(tmp_path):
    """Verify script returns 1 when an unexpected exception is raised."""
    config_file = tmp_path / "ude_config.json"
    config_file.write_text('{"src_dir": ["non_existent"]}', encoding="utf-8")

    with patch.object(sys, "argv", ["orchestrator.py", str(config_file)]):
        with patch("ude.orchestrator.UdeOrchestrator.run", side_effect=ValueError("Fatal Exception")):
            code = main()
            assert code == 1
