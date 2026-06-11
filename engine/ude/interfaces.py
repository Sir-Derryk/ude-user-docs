# engine/ude/interfaces.py
# All documentation, docstrings, and code comments are strictly in English.

from abc import ABC, abstractmethod
from pathlib import Path
from ude.models import ProjectCatalog


class UdeException(Exception):
    """Base exception for all Universal Documentation Engine (UDE) custom errors."""

    pass


class ParserError(UdeException):
    """Raised when an error occurs during Doxygen XML or native AST parsing.

    Satisfies REQ-FUN-02
    """

    pass


class RendererError(UdeException):
    """Raised when an error occurs during document rendering (Markdown or static HTML).

    Satisfies REQ-FUN-03
    """

    pass


class CollectorError(UdeException):
    """Raised when an error occurs during environment validation, execution, or cleanup of the collector.

    Satisfies REQ-FUN-01, REQ-FUN-22
    """

    pass


class BaseParser(ABC):
    """Abstract base class establishing the contract for all documentation parsers.

    Parsers ingest raw metrics and code structures from XML directories or code files and
    map them into the language-agnostic Intermediate Representation (IR).

    Satisfies REQ-FUN-02
    """

    @abstractmethod
    def parse(self, input_path: str) -> ProjectCatalog:
        """Parses the input path and returns a validated ProjectCatalog instance.

        Args:
            input_path: Path to the target Doxygen XML directory, file, or native source file.

        Returns:
            A populated ProjectCatalog representing the code structures.

        Raises:
            ParserError: If parsing fails or input is malformed.

        Satisfies REQ-FUN-02
        """


class BaseRenderer(ABC):
    """Abstract base class establishing the contract for all document renderers.

    Renderers ingest a structured ProjectCatalog and output formatted Markdown or HTML files.

    Satisfies REQ-FUN-03
    """

    @abstractmethod
    def render(self, catalog: ProjectCatalog, output_path: str) -> None:
        """Renders the ProjectCatalog documentation into the specified output path.

        Args:
            catalog: The Intermediate Representation (IR) containing documentation entities.
            output_path: Path to the output directory or target file on disk.

        Raises:
            RendererError: If rendering fails due to missing templates or I/O issues.

        Satisfies REQ-FUN-03
        """


class BaseCollector(ABC):
    """Abstract base class establishing the contract for all documentation pre-processing collectors.

    Collectors trigger code extraction tools (such as Doxygen) to generate raw structure representations (e.g. XML)
    and guarantee safe, robust environment verification and workspace cleanup.

    Satisfies REQ-FUN-01, REQ-FUN-22
    """

    @abstractmethod
    def validate_environment(self, config_path: Path) -> None:
        """Validates that all external dependencies, compilers, and paths are correct and available.

        Args:
            config_path: Path to the target configurations (e.g., ude_config.json).

        Raises:
            CollectorError: If any of the required tools or templates are missing.

        Satisfies REQ-FUN-01
        """
        pass  # pragma: no cover

    @abstractmethod
    def collect(self, config_path: Path) -> Path:
        """Executes the Doxygen process or native metadata collector to extract structural information.

        Args:
            config_path: Path to the configurations directory or file.

        Returns:
            The Path to the directory containing raw generated XML elements.

        Raises:
            CollectorError: If process execution fails.

        Satisfies REQ-FUN-01
        """
        pass  # pragma: no cover

    @abstractmethod
    def cleanup(self, temp_path: Path) -> None:
        """Safely and recursively removes temporary workspace directories.

        Args:
            temp_path: Path to the directory to clean up.

        Raises:
            ValueError: If path is empty, is a system root, or lies outside safe boundaries.
            CollectorError: If cleanup fails.

        Satisfies REQ-FUN-22
        """
        pass  # pragma: no cover


