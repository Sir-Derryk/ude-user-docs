# engine/ude/cli.py
# All documentation, docstrings, and code comments are strictly in English.

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Union, List

from ude.interfaces import UdeException, CollectorError, ParserError, RendererError
from ude.collectors.doxygen import DoxygenXmlCollector
from ude.parsers.doxygen import DoxygenXmlParser
from ude.renderers.hugo_markdown import HugoMarkdownRenderer
from ude.renderers.static_html import HtmlRenderer


def find_product_json(start_dir: Path) -> Optional[Path]:
    """Ascends the directory tree starting from start_dir to find product.json.

    Args:
        start_dir: Path to start searching from.

    Returns:
        The Path to product.json if found, otherwise None.
    """
    current_dir = start_dir.resolve()
    while True:
        product_file = current_dir / "product.json"
        if product_file.exists() and product_file.is_file():
            return product_file
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return None


def run_pipeline(
    config_path: Path,
    input_override: Optional[str] = None,
    output_override: Optional[str] = None,
    format_override: Optional[str] = None,
) -> int:
    """Executes the complete documentation compilation pipeline based on configuration.

    Args:
        config_path: Path to the target project configuration file (e.g. ude_config.json).
        input_override: Optional override path for the source directory.
        output_override: Optional override path for the output directory.
        format_override: Optional override format ('hugo_markdown' or 'html').

    Returns:
        Exit code: 0 on success, non-zero on failure.
    """
    if not config_path.exists():
        print(f"Error: Configuration file '{config_path}' does not exist.", file=sys.stderr)
        return 1

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse JSON config: {e}", file=sys.stderr)
        return 1

    config_dir = config_path.parent

    # Determine language
    collector_cfg = config.get("collector", {})
    lang_raw = collector_cfg.get("type") or collector_cfg.get("language") or "cpp"
    lang_raw = str(lang_raw).lower()
    
    # Normalize language mapping
    lang_map = {
        "cpp": "cpp",
        "cs": "csharp",
        "csharp": "csharp",
        "java": "java",
        "py": "python",
        "python": "python"
    }
    language = lang_map.get(lang_raw, "cpp")

    # Determine src_dir
    if input_override:
        src_dirs_raw = [input_override]
    else:
        src_dirs_raw = config.get("src_dir")
        if not src_dirs_raw:
            src_dirs_raw = collector_cfg.get("src_dir")
        if not src_dirs_raw:
            print("Error: No source directory specified in configuration or overrides.", file=sys.stderr)
            return 1

    if isinstance(src_dirs_raw, str):
        src_dirs_raw = [src_dirs_raw]

    # Resolve relative src_dir strictly relative to the config file's physical directory
    src_paths = [(config_dir / p).resolve() for p in src_dirs_raw]

    src_path = src_paths[0]

    # Determine output_dir
    if output_override:
        out_dir_raw = output_override
    else:
        out_dir_raw = config.get("output_dir", "output")
    out_dir = (config_dir / out_dir_raw).resolve()

    # Determine format
    if format_override:
        fmt = format_override.lower()
    else:
        renderer_cfg = config.get("renderer", {})
        fmt = renderer_cfg.get("type", "hugo_markdown").lower()

    if fmt in ("html", "static_html"):
        renderer_type = "html"
    elif fmt in ("hugo_markdown", "markdown", "hugo"):
        renderer_type = "hugo_markdown"
    else:
        print(f"Error: Unsupported format '{fmt}'. Must be 'hugo_markdown' or 'html'.", file=sys.stderr)
        return 1

    # Ascend tree to find product.json
    product_json_path = find_product_json(config_dir)
    product_metadata = {}
    if product_json_path:
        try:
            with product_json_path.open("r", encoding="utf-8") as pf:
                product_metadata = json.load(pf)
        except Exception as e:
            print(f"Warning: Failed to parse product.json: {e}", file=sys.stderr)

    # Execute Collection (if applicable)
    xml_dir: Path = src_path
    collector_run_needed = True

    # If the src_path is already a directory with index.xml, we can skip collector run
    if src_path.is_dir() and (src_path / "index.xml").exists():
        xml_dir = src_path
        collector_run_needed = False

    temp_xml_dir: Optional[Path] = None
    collector: Optional[DoxygenXmlCollector] = None

    if collector_run_needed:
        if "src_dir" not in collector_cfg:
            collector_cfg["src_dir"] = src_dirs_raw[0]
        if "doxyfile_template" not in collector_cfg:
            collector_cfg["doxyfile_template"] = "Doxyfile"

        config["collector"] = collector_cfg

        # Save temporary modified configuration to trigger collector
        temp_config_path = config_dir / "ude_config_temp.json"
        try:
            with temp_config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f)
            
            collector = DoxygenXmlCollector()
            xml_dir = collector.collect(temp_config_path)
            temp_xml_dir = xml_dir.parent
        finally:
            if temp_config_path.exists():
                temp_config_path.unlink()

    try:
        # Execute Parsing
        parser = DoxygenXmlParser()
        catalog = parser.parse(str(xml_dir))

        # Enrich Catalog Metadata
        if product_metadata:
            setattr(catalog, "metadata", product_metadata)

        # Execute Rendering
        if renderer_type == "hugo_markdown":
            renderer = HugoMarkdownRenderer(language=language)
        else:
            renderer = HtmlRenderer(language=language)

        out_dir.mkdir(parents=True, exist_ok=True)
        renderer.render(catalog, str(out_dir))

    finally:
        # Safe Cleanup
        if collector and temp_xml_dir:
            try:
                collector.cleanup(temp_xml_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary directory '{temp_xml_dir}': {e}", file=sys.stderr)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Primary entry point for the command-line interface.

    Args:
        argv: Optional list of command-line arguments to parse. Defaults to sys.argv[1:].

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Universal Documentation Engine (UDE) Non-Interactive CLI Compiler Interface",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to target project configuration template (e.g. ude_config.json).",
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Override value for source paths defined in configurations as src_dir.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Override value for destination targets defined in configurations as output_dir.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["hugo_markdown", "html"],
        help="Override value for output format: hugo_markdown or html.",
    )

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit as se:
        return se.code

    try:
        config_path = Path(args.config)
        return run_pipeline(
            config_path=config_path,
            input_override=args.input,
            output_override=args.output,
            format_override=args.format,
        )
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
