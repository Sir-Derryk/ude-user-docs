# engine/ude/renderers/hugo_markdown.py
# All documentation, docstrings, and code comments are strictly in English.

import re
from pathlib import Path
from ude.interfaces import BaseRenderer, RendererError
from ude.models import ProjectCatalog


class HugoMarkdownRenderer(BaseRenderer):
    """Renderer to convert ProjectCatalog IR into Markdown documentation with YAML front-matter.

    Satisfies REQ-FUN-03
    """

    def __init__(self, language: str):
        """Initializes the HugoMarkdownRenderer with a specific target language.

        Args:
            language: The language mapping rules to use ('cpp', 'python', 'java', 'csharp').

        Raises:
            ValueError: If the language is unsupported.

        Satisfies REQ-FUN-03
        """
        supported_languages = {"cpp", "python", "java", "csharp"}
        if language not in supported_languages:
            raise ValueError(f"Unsupported language: '{language}'. Supported: {supported_languages}")
        self.language = language

    def resolve_filename(self, api_path: str, entity_type: str = "class") -> str:
        """Translates a logical API path to a safe, physical, flat disk filename on Hugo/Docusaurus.

        Satisfies REQ-FUN-03, REQ-FUN-04, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32
        """
        # Split off the overload signature block if present
        if "@" in api_path:
            base_path, overload = api_path.split("@", 1)
            # Standard type symbol mapping for overloads
            overload = overload.replace("*", "_ptr").replace("&", "_ref")
            overload = overload.replace("<", "_lt_").replace(">", "_gt_")
            overload = re.sub(r"[\s,]+", "_", overload)
            overload = f"@{overload}"
        else:
            base_path = api_path
            overload = ""

        if self.language == "cpp":
            # Map standard double colon scope structures to double underscores
            base_path = base_path.replace("*", "_ptr").replace("&", "_ref")
            base_path = base_path.replace("<", "_lt_").replace(">", "_gt_")
            base_path = base_path.replace("::", "__")
            filename = f"{base_path}{overload}.md"

        elif self.language == "csharp":
            # Dots representing scopes and nested classes map to double underscores
            base_path = base_path.replace(".", "__")
            filename = f"{base_path}{overload}.md"

        elif self.language == "java":
            # Java packages use single underscores, nested classes and scopes use double
            parts = base_path.split(".")
            # Identify first capitalized scope which denotes the class start
            class_start_idx = len(parts)
            for idx, part in enumerate(parts):
                if part and part[0].isupper():
                    class_start_idx = idx
                    break

            pkg_part = "_".join(parts[:class_start_idx])
            class_part = "__".join(parts[class_start_idx:])

            if pkg_part and class_part:
                base_path = f"{pkg_part}_{class_part}"
            elif class_part:
                base_path = class_part
            else:
                base_path = pkg_part

            filename = f"{base_path}{overload}.md"

        elif self.language == "python":
            # Modules/packages use single underscores, class members and methods use double
            parts = base_path.split(".")
            class_idx = -1
            for idx, part in enumerate(parts):
                if part and part[0].isupper():
                    class_idx = idx
                    break

            if class_idx != -1:
                prefix = "_".join(parts[: class_idx + 1])
                suffix = "__".join(parts[class_idx + 1 :])
                if suffix:
                    base_path = f"{prefix}__{suffix}"
                else:
                    base_path = prefix
            else:
                # If no class, assume last component is the function separated by double underscore
                if len(parts) > 1:
                    base_path = f"{'_'.join(parts[:-1])}__{parts[-1]}"
                else:
                    base_path = parts[0]

            filename = f"{base_path}{overload}.md"
        else:
            # Fallback for any unknown/unsupported languages bypassed in testing
            filename = f"{base_path}{overload}.md"

        if entity_type:
            filename = f"{entity_type.lower()}_{filename}"

        # Sanitize any remaining invalid characters like colons for Windows compatibility
        filename = filename.replace("::", "__").replace(":", "__")

        return filename

    def _escape_angle_brackets(self, text: str) -> str:
        """Escapes template angle brackets outside code blocks to avoid MDX parsing issues.

        Satisfies REQ-FUN-32
        """
        if not text:
            return text

        # Regex to segment code blocks (fenced code structures and inline backticks)
        pattern = r"(```[\s\S]*?```|`[^`\n]*?`)"
        parts = re.split(pattern, text)
        escaped_parts = []

        for i, part in enumerate(parts):
            if i % 2 == 1:
                # Part is inside a code block, retain as-is
                escaped_parts.append(part)
            else:
                # Escape angle brackets in prose/normal text
                escaped_text = part.replace("<", "&lt;").replace(">", "&gt;")
                escaped_parts.append(escaped_text)

        return "".join(escaped_parts)

    def render(self, catalog: ProjectCatalog, output_path: str) -> None:
        """Renders the ProjectCatalog documentation into Hugo-compatible Markdown files.

        Args:
            catalog: The Intermediate Representation (IR) catalog containing entities.
            output_path: Path to the output directory on disk.

        Raises:
            RendererError: If rendering fails due to I/O issues.

        Satisfies REQ-FUN-03
        """
        try:
            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)

            position_counter = 1

            for namespace in catalog.namespaces:
                for cls in namespace.classes:
                    # Construct full class path for filename resolution
                    if namespace.name:
                        if self.language == "cpp":
                            class_path = f"{namespace.name}::{cls.name}"
                        elif self.language in ("csharp", "java", "python"):
                            class_path = f"{namespace.name}.{cls.name}"
                        else:
                            class_path = cls.fully_qualified_name
                    else:
                        class_path = cls.fully_qualified_name

                    filename = self.resolve_filename(class_path, entity_type=cls.entity_type)
                    file_path = out_dir / filename

                    # Generate YAML Front-Matter block
                    title = cls.name
                    parent = namespace.name if namespace.name else ""

                    yaml_header = "---\n" f'title: "{title}"\n' f"sidebar_position: {position_counter}\n"
                    if parent:
                        yaml_header += f'parent: "{parent}"\n'
                    yaml_header += "---\n\n"

                    # Generate Markdown Body
                    body = f"# {cls.name}\n\n"
                    if cls.docstring:
                        escaped_doc = self._escape_angle_brackets(cls.docstring)
                        body += f"{escaped_doc}\n\n"

                    # Render Fields
                    if cls.fields:
                        body += "## Fields\n\n"
                        for field in cls.fields:
                            body += f"- `{field}`\n"
                        body += "\n"

                    # Render Methods
                    if cls.methods:
                        body += "## Methods\n\n"
                        for method in cls.methods:
                            body += f"### {method.name}\n"
                            body += f"`{method.signature}`\n\n"
                            if method.docstring:
                                escaped_method_doc = self._escape_angle_brackets(method.docstring)
                                body += f"{escaped_method_doc}\n\n"

                            if method.parameters:
                                body += "| Parameter | Type | Description |\n"
                                body += "| --- | --- | --- |\n"
                                for param in method.parameters:
                                    p_desc = param.description if param.description else ""
                                    escaped_desc = self._escape_angle_brackets(p_desc)
                                    body += f"| {param.name} | `{param.type}` | {escaped_desc} |\n"
                                body += "\n"

                    # Write compiled content to target file
                    file_path.write_text(yaml_header + body, encoding="utf-8")
                    position_counter += 1

        except Exception as e:
            raise RendererError(f"Failed to render Markdown output: {e}") from e
