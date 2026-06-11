# engine/ude/orchestrator.py
# All documentation, docstrings, and code comments are strictly in English.

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Union

from ude.interfaces import UdeException
from ude.collectors.doxygen import DoxygenXmlCollector
from ude.parsers.doxygen import DoxygenXmlParser
from ude.renderers.hugo_markdown import HugoMarkdownRenderer
from ude.renderers.static_html import HtmlRenderer

# Configure logger for orchestrator
logger = logging.getLogger("ude.orchestrator")


def find_global_config(start_dir: Path) -> Optional[Path]:
    """Walks the directory tree upwards to locate ude_global.json.

    Args:
        start_dir: Directory to start the search from.

    Returns:
        Path to ude_global.json if found, otherwise None.
    """
    current_dir = start_dir.resolve()
    while True:
        global_file = current_dir / "ude_global.json"
        if global_file.exists() and global_file.is_file():
            return global_file
        parent_dir = current_dir.parent
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return None


def find_product_json(start_dir: Path) -> Optional[Path]:
    """Ascends the directory tree starting from start_dir to find product.json.

    Args:
        start_dir: Directory to start searching from.

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


class UdeOrchestrator:
    """Orchestrates the entire multi-target document generation pipeline.

    Loads global and local settings, resolves portable paths, coordinates
    collectors, parsers, and renderers, and enforces error-handling policies.

    Satisfies REQ-FUN-23, REQ-FUN-24, REQ-FUN-25, REQ-FUN-28, REQ-FUN-29
    """

    def __init__(self, global_config_path: Optional[Union[str, Path]] = None) -> None:
        """Initializes the orchestrator.

        Args:
            global_config_path: Optional path to the global configuration. If not
                specified, the orchestrator will resolve it dynamically from the target directories.
        """
        self.global_config_path = Path(global_config_path) if global_config_path else None
        self.global_config = {}
        if self.global_config_path and self.global_config_path.exists():
            try:
                with self.global_config_path.open("r", encoding="utf-8") as f:
                    self.global_config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load global config {global_config_path}: {e}")

    def run_target(self, config_path: Union[str, Path]) -> bool:
        """Runs the pipeline for a single target configuration.

        Args:
            config_path: Path to the local target configuration file.

        Returns:
            True on success, False on failure.
        """
        config_file_path = Path(config_path).resolve()
        if not config_file_path.exists():
            logger.error(f"Configuration file {config_file_path} does not exist.")
            return False

        # If global config was not explicitly provided, try to find it relative to target config
        target_dir = config_file_path.parent
        resolved_global_config = dict(self.global_config)
        if not self.global_config_path:
            global_path = find_global_config(target_dir)
            if global_path:
                try:
                    with global_path.open("r", encoding="utf-8") as f:
                        resolved_global_config = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load dynamically found global config {global_path}: {e}")

        # Set up logging if specified in global configuration
        log_cfg = resolved_global_config.get("logging", {})
        if "level" in log_cfg:
            logging.getLogger().setLevel(log_cfg["level"].upper())

        try:
            with config_file_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse target JSON config {config_file_path}: {e}")
            return False

        config_dir = config_file_path.parent

        # Determine language
        collector_cfg = config.get("collector", {})
        lang_raw = collector_cfg.get("type") or collector_cfg.get("language") or "cpp"
        lang_raw = str(lang_raw).lower()
        
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
        src_dirs_raw = config.get("src_dir")
        if not src_dirs_raw:
            src_dirs_raw = collector_cfg.get("src_dir")
        if not src_dirs_raw:
            logger.error(f"No source directory specified in target config {config_file_path}.")
            return False

        if isinstance(src_dirs_raw, str):
            src_dirs_raw = [src_dirs_raw]

        # Resolve relative src_dir strictly relative to the config file's physical directory
        src_paths = [(config_dir / p).resolve() for p in src_dirs_raw]
        src_path = src_paths[0]

        # Determine output_dir
        out_dir_raw = config.get("output_dir", "output")
        out_dir = (config_dir / out_dir_raw).resolve()

        # Determine format
        renderer_cfg = config.get("renderer", {})
        fmt = renderer_cfg.get("type", "hugo_markdown").lower()

        if fmt in ("html", "static_html"):
            renderer_type = "html"
        elif fmt in ("hugo_markdown", "markdown", "hugo"):
            renderer_type = "hugo_markdown"
        else:
            logger.error(f"Unsupported format '{fmt}' in target config {config_file_path}.")
            return False

        # Ascend tree to find product.json
        product_json_path = find_product_json(config_dir)
        product_metadata = {}
        if product_json_path:
            try:
                with product_json_path.open("r", encoding="utf-8") as pf:
                    product_metadata = json.load(pf)
            except Exception as e:
                logger.warning(f"Failed to parse product.json: {e}")

        # Execute Collection (if applicable)
        xml_dir: Path = src_path
        collector_run_needed = True

        # If the src_path is already a directory with index.xml, skip collector run
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
            except Exception as e:
                logger.error(f"Collector stage failed: {e}")
                raise
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

        except Exception as e:
            logger.error(f"Parsing/Rendering stage failed: {e}")
            raise
        finally:
            # Safe Cleanup inside finally block
            if collector and temp_xml_dir:
                try:
                    collector.cleanup(temp_xml_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory '{temp_xml_dir}': {e}")

        return True

    def run(self, config_paths: List[Union[str, Path]]) -> bool:
        """Runs the pipeline sequentially for multiple target configurations.

        Enforces the error_policy:
        - 'fail-fast' halts on the first error.
        - 'continue-on-error' logs errors, skips the failed target, compiles the remainder,
          and returns False if any failures occurred.

        Args:
            config_paths: A list of target configuration paths.

        Returns:
            True if all targets succeeded, False if any failed.
        """
        success = True
        failed_targets = []

        for path in config_paths:
            resolved_path = Path(path).resolve()
            # Resolve error policy dynamically
            target_dir = resolved_path.parent
            error_policy = "fail-fast"  # default fallback
            
            # Find closest error_policy
            if self.global_config_path and "error_policy" in self.global_config:
                error_policy = self.global_config["error_policy"]
            else:
                global_path = find_global_config(target_dir)
                if global_path:
                    try:
                        with global_path.open("r", encoding="utf-8") as f:
                            g_cfg = json.load(f)
                            error_policy = g_cfg.get("error_policy", "fail-fast")
                    except Exception:
                        pass

            logger.info(f"Orchestrating target: {resolved_path} with error_policy: {error_policy}")

            try:
                target_success = self.run_target(resolved_path)
                if not target_success:
                    raise UdeException(f"Pipeline execution returned False for target {resolved_path}")
            except Exception as e:
                success = False
                failed_targets.append((resolved_path, str(e)))
                logger.error(f"Error during execution of {resolved_path}: {e}")
                
                if error_policy == "fail-fast":
                    logger.error("Error policy is 'fail-fast'. Halting execution.")
                    raise

        if failed_targets:
            logger.error(f"Orchestration completed with errors. Failed targets:")
            for pt, err in failed_targets:
                logger.error(f"  - {pt}: {err}")
            return False

        return success


def main() -> int:
    """Primary execution entry point when run as a script."""
    if len(sys.argv) < 2:
        print("Usage: python -m ude.orchestrator <config_path1> [<config_path2> ...]", file=sys.stderr)
        return 4

    config_paths = sys.argv[1:]
    orchestrator = UdeOrchestrator()
    try:
        success = orchestrator.run(config_paths)
        return 0 if success else 1
    except Exception as e:
        print(f"Orchestration failed with fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
