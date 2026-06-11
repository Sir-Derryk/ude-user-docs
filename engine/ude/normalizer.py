# engine/ude/normalizer.py
# All documentation, docstrings, and code comments are strictly in English.

import re
from typing import Tuple, Dict, Any, Optional


class CommentNormalizer:
    """Normalizes legacy and modern code comments/docstrings to CommonMark.

    Extracts parameter, return, author, and version tags as metadata,
    and returns a clean, compliant Markdown body.

    Satisfies REQ-FUN-14
    """

    def __init__(self) -> None:
        # Pre-compile regular expressions for performance

        # Javadoc/Doxygen parameters: @param name desc or \param name desc
        self._param_re = re.compile(
            r"^[\\@]param\s+(?:\[[^\]]+\]\s+)?(\w+)\s+(.*)$",
            re.IGNORECASE
        )

        # Javadoc/Doxygen returns: @return desc or \return desc or @returns desc
        self._return_re = re.compile(
            r"^[\\@]returns?\s+(.*)$",
            re.IGNORECASE
        )

        # Author and version tags
        self._author_re = re.compile(
            r"^[\\@]author\s+(.*)$",
            re.IGNORECASE
        )
        self._version_re = re.compile(
            r"^[\\@]version\s+(.*)$",
            re.IGNORECASE
        )

        # Doxygen brief: \brief desc or @brief desc
        self._brief_re = re.compile(
            r"^[\\@]brief\s+(.*)$",
            re.IGNORECASE
        )

        # Google individual parameter: x (int): desc or x: desc
        self._google_param_line_re = re.compile(
            r"^\s*(\w+)(?:\s*\([^)]+\))?\s*:\s*(.*)$"
        )

    def normalize_comment(self, raw_comment: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        """Cleans and standardizes raw docstring/comment blocks to CommonMark.

        Args:
            raw_comment: The raw string of the docstring/comment block from source code.

        Returns:
            A tuple containing:
                - The cleaned docstring body (CommonMark Markdown string).
                - A dictionary containing extracted metadata:
                    {
                        "params": Dict[str, str],   # parameter_name -> description
                        "returns": Optional[str],   # return description
                        "author": Optional[str],    # author description
                        "version": Optional[str],   # version description
                    }

        Satisfies REQ-FUN-14
        """
        if not raw_comment:
            return "", {
                "params": {},
                "returns": None,
                "author": None,
                "version": None,
            }

        # 1. Clean the outer wrapping and block decorations
        lines = self._strip_decorations(raw_comment)

        # Metadata to populate
        params: Dict[str, str] = {}
        returns_desc: Optional[str] = None
        author_desc: Optional[str] = None
        version_desc: Optional[str] = None

        # Re-join lines for full string block analysis
        cleaned_block = "\n".join(lines)

        # 2. Extract Google-style sections before line-by-line tag cleaning
        # Args or Parameters section
        google_args_re = re.compile(
            r"^\s*(?:Args|Parameters):\s*\n(.*?)(?=(?:\s*(?:Returns|Raises|Yields|Example|Docstring)|\Z))",
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
        google_args_match = google_args_re.search(cleaned_block)
        if google_args_match:
            args_block = google_args_match.group(1)
            cleaned_block = google_args_re.sub("", cleaned_block)
            for line in args_block.splitlines():
                p_match = self._google_param_line_re.match(line)
                if p_match:
                    name, desc = p_match.groups()
                    params[name.strip()] = desc.strip()

        # Returns section
        google_returns_re = re.compile(
            r"^\s*Returns:\s*\n(.*?)(?=(?:\s*(?:Raises|Yields|Example|Docstring)|\Z))",
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
        google_returns_match = google_returns_re.search(cleaned_block)
        if google_returns_match:
            returns_block = google_returns_match.group(1)
            cleaned_block = google_returns_re.sub("", cleaned_block)
            lines_ret = [l.strip() for l in returns_block.splitlines() if l.strip()]
            if lines_ret:
                first_line = lines_ret[0]
                if ":" in first_line:
                    ret_type, ret_desc = first_line.split(":", 1)
                    returns_desc = f"{ret_type.strip()}: {ret_desc.strip()}"
                else:
                    returns_desc = first_line

        # 3. Analyze line-by-line for Javadoc/Doxygen tags
        final_body_lines = []
        for line in cleaned_block.splitlines():
            stripped_line = line.strip()

            # Parameter check
            if stripped_line.startswith(("@param", "\\param")):
                p_match = self._param_re.match(stripped_line)
                if p_match:
                    name, desc = p_match.groups()
                    params[name.strip()] = desc.strip()
                continue

            # Return check
            if stripped_line.startswith(("@return", "\\return", "@returns", "\\returns")):
                r_match = self._return_re.match(stripped_line)
                if r_match:
                    desc = r_match.group(1)
                    returns_desc = desc.strip()
                continue

            # Author check
            if stripped_line.startswith(("@author", "\\author")):
                a_match = self._author_re.match(stripped_line)
                if a_match:
                    desc = a_match.group(1)
                    author_desc = desc.strip()
                continue

            # Version check
            if stripped_line.startswith(("@version", "\\version")):
                v_match = self._version_re.match(stripped_line)
                if v_match:
                    desc = v_match.group(1)
                    version_desc = desc.strip()
                continue

            # Brief check
            if stripped_line.startswith(("@brief", "\\brief")):
                b_match = self._brief_re.match(stripped_line)
                if b_match:
                    desc = b_match.group(1)
                    final_body_lines.append(desc.strip())
                continue

            # Preserve other lines
            final_body_lines.append(line)

        # 4. Standardize the remaining docstring body
        clean_text = self._standardize_markdown(final_body_lines)

        metadata = {
            "params": params,
            "returns": returns_desc,
            "author": author_desc,
            "version": version_desc,
        }

        return clean_text, metadata

    def _strip_decorations(self, text: str) -> list[str]:
        """Strips Javadoc block comment formatting and Doxygen comment markers."""
        lines = []
        text = text.replace("\r\n", "\n")
        raw_lines = text.split("\n")

        for line in raw_lines:
            stripped = line.strip()

            # Skip start and end of blocks (do not skip bare '///' or '//!' as they represent blank lines)
            if stripped in ("/**", "/*", "*/", "/*!", "**/"):
                continue
            if stripped.startswith("/*") or stripped.endswith("*/"):
                stripped = re.sub(r"^/\*\*?\s*", "", stripped)
                stripped = re.sub(r"\s*\*+/$", "", stripped)
                if stripped:
                    lines.append(stripped)
                continue

            # Strip leading comment markers
            if stripped.startswith("*"):
                line_content = re.sub(r"^\*\s?", "", stripped)
                lines.append(line_content)
                continue

            if stripped.startswith("///") or stripped.startswith("//!"):
                line_content = re.sub(r"^///\s?|^//!\s?", "", stripped)
                lines.append(line_content)
                continue

            lines.append(line)

        return lines

    def _standardize_markdown(self, lines: list[str]) -> str:
        """Post-processes docstring lines to create a clean, uniform CommonMark block."""
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return ""

        non_empty_indents = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                non_empty_indents.append(indent)

        min_indent = min(non_empty_indents) if non_empty_indents else 0

        dedented_lines = []
        for line in lines:
            if line.strip():
                dedented_lines.append(line[min_indent:])
            else:
                dedented_lines.append("")

        body = "\n".join(dedented_lines)
        body = re.sub(r"\n{3,}", "\n\n", body)
        return body.strip()
