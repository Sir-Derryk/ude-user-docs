# engine/ude/collectors/doxygen.py
# All documentation, docstrings, and code comments are strictly in English.

import json
import subprocess
import shutil
import tempfile
from pathlib import Path
from ude.interfaces import BaseCollector, CollectorError


class DoxygenXmlCollector(BaseCollector):
    """Collector implementation that invokes the external Doxygen process.

    Generates customized XML documentation structures from source files
    and handles environment verification and secure filesystem cleanup.

    Satisfies REQ-FUN-01, REQ-FUN-22
    """

    def validate_environment(self, config_path: Path) -> None:
        """Validates that all external dependencies, compilers, and paths are correct.

        Args:
            config_path: Path to the target configurations (e.g., ude_config.json).

        Raises:
            CollectorError: If any of the required tools or templates are missing.

        Satisfies REQ-FUN-01
        """
        config_path = config_path.resolve()
        # Verify doxygen binary in PATH
        doxygen_bin = shutil.which("doxygen")
        if not doxygen_bin:
            raise CollectorError("doxygen binary not found in PATH")

        if not config_path.exists():
            raise CollectorError(f"Configuration file {config_path} does not exist")

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            raise CollectorError(f"Failed to parse JSON config: {e}")

        collector_cfg = config.get("collector", {})
        src_dir_val = collector_cfg.get("src_dir")
        doxy_template_val = collector_cfg.get("doxyfile_template")

        if not src_dir_val:
            raise CollectorError("Missing 'src_dir' in collector configuration")
        if not doxy_template_val:
            raise CollectorError("Missing 'doxyfile_template' in collector configuration")

        base_dir = config_path.parent
        src_dir = (base_dir / src_dir_val).resolve()
        doxy_template = (base_dir / doxy_template_val).resolve()

        if not src_dir.exists() or not src_dir.is_dir():
            raise CollectorError(f"Source directory {src_dir} does not exist or is not a directory")

        if not doxy_template.exists() or not doxy_template.is_file():
            if collector_cfg.get("doxyfile_template") != "Doxyfile":
                raise CollectorError(f"Doxyfile template {doxy_template} does not exist or is not a file")

    def collect(self, config_path: Path) -> Path:
        """Executes the Doxygen process to extract structural information.

        Args:
            config_path: Path to the configurations directory or file.

        Returns:
            The Path to the directory containing raw generated XML elements.

        Raises:
            CollectorError: If process execution fails.

        Satisfies REQ-FUN-01
        """
        config_path = config_path.resolve()
        self.validate_environment(config_path)

        # Read configuration (validated)
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        base_dir = config_path.parent
        collector_cfg = config.get("collector", {})
        src_dir = (base_dir / collector_cfg["src_dir"]).resolve()
        doxy_template = (base_dir / collector_cfg["doxyfile_template"]).resolve()

        # Create isolated temporary folder under the config's directory
        temp_xml_path = base_dir / "temp_xml"
        temp_xml_path.mkdir(exist_ok=True)

        xml_output_dir = temp_xml_path / "xml"
        xml_output_dir.mkdir(exist_ok=True)

        # Prepare localized Doxygen configuration
        doxy_content = ""
        if collector_cfg.get("doxyfile_template") == "Doxyfile" and not doxy_template.exists():
            doxy_content = "GENERATE_XML = YES\n"
        else:
            try:
                with doxy_template.open("r", encoding="utf-8") as f:
                    doxy_content = f.read()
            except Exception as e:
                raise CollectorError(f"Failed to read Doxyfile template: {e}")

        # Customize settings
        custom_settings = [
            f'OUTPUT_DIRECTORY = "{temp_xml_path}"',
            "GENERATE_XML = YES",
            "XML_OUTPUT = xml",
            f'INPUT = "{src_dir}"',
            "RECURSIVE = YES",
            "GENERATE_HTML = NO",
            "GENERATE_LATEX = NO",
        ]

        # Add optional custom language-specific parameters if they exist in config
        language = collector_cfg.get("language", "").lower()
        if language == "java":
            custom_settings.append("OPTIMIZE_OUTPUT_JAVA = YES")
        elif language == "python":
            custom_settings.append("OPTIMIZE_OUTPUT_JAVA = YES")

        doxy_content += "\n" + "\n".join(custom_settings) + "\n"

        temp_doxyfile = temp_xml_path / "Doxyfile_local"
        try:
            with temp_doxyfile.open("w", encoding="utf-8") as f:
                f.write(doxy_content)
        except Exception as e:
            raise CollectorError(f"Failed to write localized Doxyfile: {e}")

        # Trigger Doxygen subprocess
        try:
            result = subprocess.run(
                ["doxygen", str(temp_doxyfile)],
                capture_output=True,
                text=True,
                cwd=str(base_dir),
                check=False
            )
            if result.returncode != 0:
                raise CollectorError(f"Doxygen process failed with code {result.returncode}: {result.stderr}")
        except FileNotFoundError:
            raise CollectorError("doxygen binary not found during execution")
        except Exception as e:
            raise CollectorError(f"Subprocess execution failed: {e}")

        return xml_output_dir

    def cleanup(self, temp_path: Path) -> None:
        """Safely and recursively removes temporary workspace directories with strict boundaries.

        Args:
            temp_path: Path to the directory to clean up.

        Raises:
            ValueError: If path is empty, is a system root, or lies outside safe boundaries.
            CollectorError: If cleanup fails.

        Satisfies REQ-FUN-22
        """
        # Guard rails
        is_empty_path = False
        raw = getattr(temp_path, "_raw_paths", [])
        if not temp_path or str(temp_path).strip() == "":
            is_empty_path = True
        elif not temp_path.parts: # Handles Path("") and Path(".")
            if not raw or raw == [""]:
                import sys
                if sys.version_info < (3, 12):
                    # On Python < 3.12, Path("") and Path(".") are indistinguishable.
                    # We use call stack frame inspection to see if it was called with empty string.
                    import inspect
                    try:
                        stack = inspect.stack()
                        for frame_info in stack[1:3]:
                            line = frame_info.code_context[0].strip() if frame_info.code_context else ""
                            if 'Path("")' in line or "Path('')" in line or '""' in line or "''" in line:
                                is_empty_path = True
                                break
                    except Exception:
                        pass
                else:
                    is_empty_path = True

        if is_empty_path:
            raise ValueError("Path cannot be empty")



        path_str = str(temp_path)
        if path_str in (".", "..", "./", "../") or path_str.endswith("/..") or path_str.endswith("\\.."):
            raise ValueError("Cannot delete relative navigation paths")

        # Check system roots conceptually (both Unix "/" and Windows "C:\", "D:")
        import re
        if path_str in ("/", "\\") or re.match(r"^[a-zA-Z]:[\\/]?$", path_str):
            raise ValueError("Cannot delete system root")

        try:
            abs_path = temp_path.resolve()
        except OSError as e:
            raise CollectorError(f"Failed to resolve path: {e}")

        # Check system roots after resolution
        if abs_path == abs_path.parent or len(abs_path.parts) <= 1:
            raise ValueError("Cannot delete system root")

        # Determine boundaries
        # On non-Windows, if path has a Windows drive pattern or backslashes, it is outside safe boundaries
        import os
        if os.name != "nt" and (re.match(r"^[a-zA-Z]:", str(temp_path)) or "\\" in str(temp_path)):
            raise ValueError("Path is outside safe working boundaries")

        # project root: Pipeline/

        project_root = Path(__file__).resolve().parent.parent.parent.parent
        sys_temp = Path(tempfile.gettempdir()).resolve()

        in_project = False
        try:
            abs_path.relative_to(project_root)
            in_project = True
        except ValueError:
            pass

        in_temp = False
        try:
            abs_path.relative_to(sys_temp)
            in_temp = True
        except ValueError:
            pass

        if not (in_project or in_temp):
            raise ValueError("Path is outside safe working boundaries")

        # Do not allow deleting project root or main folders
        if abs_path == project_root or abs_path == project_root / "engine" or abs_path == project_root / "design-docs":
            raise ValueError("Cannot delete project core directories")

        # Recursively remove directory
        if abs_path.exists():
            try:
                if abs_path.is_file():
                    abs_path.unlink()
                else:
                    shutil.rmtree(abs_path)
            except Exception as e:
                raise CollectorError(f"Failed to delete directory {abs_path}: {e}")
