# engine/tests/test_hugo_renderer.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from pathlib import Path
import re
from ude.interfaces import BaseRenderer, RendererError
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity, MethodEntity, ParameterField

# We import the to-be-implemented class. It should fail to import initially (RED phase).
try:
    from ude.renderers.hugo_markdown import HugoMarkdownRenderer
except ImportError:
    HugoMarkdownRenderer = None


def parse_simple_yaml(yaml_str: str) -> dict:
    """Helper to parse very simple YAML front-matter without third-party dependencies."""
    data = {}
    for line in yaml_str.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.isdigit():
                val = int(val)
            elif val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val.lower() in ("null", "none", "~"):
                val = None
            data[key] = val
    return data


def test_hugo_renderer_import():
    """Verify that we can import HugoMarkdownRenderer or handle it in the RED phase."""
    assert HugoMarkdownRenderer is not None, "HugoMarkdownRenderer is not implemented yet."


def test_invalid_language():
    """Verify that instantiating with an unsupported language raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        HugoMarkdownRenderer(language="invalid")
    assert "Unsupported language" in str(excinfo.value)


@pytest.mark.parametrize(
    "language, api_path, entity_type, expected_filename",
    [
        # C++ Tests
        ("cpp", "FacetModeler::Body::faceCount", "variable", "variable_FacetModeler__Body__faceCount.md"),
        ("cpp", "FacetModeler::Traits<Type>::method", "method", "method_FacetModeler__Traits_lt_Type_gt___method.md"),
        ("cpp", "FacetModeler::Body::draw@int*,float&", "method", "method_FacetModeler__Body__draw@int_ptr_float_ref.md"),
        
        # C# Tests
        ("csharp", "Namespace.SubNamespace.Class.NestedClass.Method@int", "method", "method_Namespace__SubNamespace__Class__NestedClass__Method@int.md"),
        
        # Java Tests
        ("java", "org.example.pkg.Class.NestedClass.method@int", "method", "method_org_example_pkg_Class__NestedClass__method@int.md"),
        
        # Python Tests
        ("python", "ude.parsers.doxygen.DoxygenXmlParser.parse_file@str", "method", "method_ude_parsers_doxygen_DoxygenXmlParser__parse_file@str.md"),
        ("python", "package.module.func", "method", "method_package_module__func.md"),
    ],
)
def test_resolve_filename(language, api_path, entity_type, expected_filename):
    """Verify logical-to-physical flat-mapping rules across all supported languages.
    
    Satisfies REQ-FUN-03, REQ-FUN-04, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32
    """
    renderer = HugoMarkdownRenderer(language=language)
    assert renderer.resolve_filename(api_path, entity_type=entity_type) == expected_filename


def test_angle_bracket_escaping():
    """Verify template angle brackets escaping to MDX entities outside code blocks."""
    renderer = HugoMarkdownRenderer(language="cpp")
    
    # 1. Prose outside of code blocks must be escaped
    prose = "An instance of std::vector<int> and std::map<string, float> templates."
    expected_escaped = "An instance of std::vector&lt;int&gt; and std::map&lt;string, float&gt; templates."
    assert renderer._escape_angle_brackets(prose) == expected_escaped
    
    # 2. Inside backticks/inline code blocks must NOT be escaped
    inline_code = "Use the `std::vector<int>` container."
    assert renderer._escape_angle_brackets(inline_code) == inline_code
    
    # 3. Inside fenced code blocks must NOT be escaped
    fenced_code = "```cpp\nstd::vector<int> vec;\n```"
    assert renderer._escape_angle_brackets(fenced_code) == fenced_code
    
    # 4. Mixed content
    mixed = "A template std::vector<int> like `std::vector<int>` inside ```\nvector<T>\n```."
    expected_mixed = "A template std::vector&lt;int&gt; like `std::vector<int>` inside ```\nvector<T>\n```."
    assert renderer._escape_angle_brackets(mixed) == expected_mixed


def test_yaml_front_matter_and_rendering(tmp_path):
    """Verify full ProjectCatalog rendering to disk with YAML metadata headers.
    
    Satisfies REQ-FUN-03, REQ-FUN-32
    """
    renderer = HugoMarkdownRenderer(language="cpp")
    
    # Create mock ProjectCatalog
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="FacetModeler",
                classes=[
                    ClassEntity(
                        name="Body",
                        fully_qualified_name="FacetModeler::Body",
                        docstring="A representation of a 3D topological body in FacetModeler<Type>.",
                        fields=["faceCount", "edgeCount"],
                        methods=[
                            MethodEntity(
                                name="draw",
                                signature="void draw(int* count, float& scale)",
                                parameters=[
                                    ParameterField(name="count", type="int*", description="Number of elements"),
                                    ParameterField(name="scale", type="float&", description="Scale factor"),
                                ],
                                return_type="void",
                                docstring="Draws the body using a std::vector<Face> container.",
                            )
                        ]
                    )
                ]
            )
        ]
    )
    
    output_dir = tmp_path / "docs"
    renderer.render(catalog, str(output_dir))
    
    # Check that class-level documentation file was written to disk
    class_file = output_dir / "class_FacetModeler__Body.md"
    assert class_file.exists()
    
    content = class_file.read_text(encoding="utf-8")
    
    # Verify Front-Matter exists and is valid YAML
    assert content.startswith("---")
    parts = content.split("---")
    assert len(parts) >= 3
    
    front_matter_str = parts[1]
    metadata = parse_simple_yaml(front_matter_str)
    
    assert metadata["title"] == "Body"
    assert metadata["sidebar_position"] is not None
    assert metadata["parent"] == "FacetModeler"
    
    # Verify Body/Docstring Rendering (with Escaped Angle Brackets)
    assert "A representation of a 3D topological body in FacetModeler&lt;Type&gt;." in content
    
    # Verify Methods Rendering inside Class File
    assert "### draw" in content
    assert "void draw(int* count, float& scale)" in content
    # Inside method docstring, template brackets are also escaped
    assert "Draws the body using a std::vector&lt;Face&gt; container." in content


def test_edge_cases_and_coverage():
    """Verify rare branches, empty values, and edge cases to reach 100% statement coverage."""
    # 1. Java path with no package component
    renderer_java = HugoMarkdownRenderer(language="java")
    assert renderer_java.resolve_filename("MyClass") == "class_MyClass.md"
    assert renderer_java.resolve_filename("MyClass.NestedClass") == "class_MyClass__NestedClass.md"
    # Java path with only package component (no capitalized class)
    assert renderer_java.resolve_filename("org.example.pkg") == "class_org_example_pkg.md"

    # 2. Python path with no method (just class)
    renderer_py = HugoMarkdownRenderer(language="python")
    assert renderer_py.resolve_filename("my_module.MyClass") == "class_my_module_MyClass.md"
    # Python path with single component function
    assert renderer_py.resolve_filename("my_func") == "class_my_func.md"

    # 3. Escape empty or None text
    renderer_cpp = HugoMarkdownRenderer(language="cpp")
    assert renderer_cpp._escape_angle_brackets("") == ""
    assert renderer_cpp._escape_angle_brackets(None) is None


def test_rendering_languages_and_namespaces(tmp_path):
    """Verify rendering of catalogs for C++/Python/Java and when namespace is empty."""
    # Render with Python to cover other language branches in render()
    renderer_py = HugoMarkdownRenderer(language="python")
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="ude.parsers",
                classes=[
                    ClassEntity(
                        name="Parser",
                        fully_qualified_name="ude.parsers.Parser",
                        docstring="Python parser class.",
                    )
                ]
            )
        ]
    )
    output_dir_py = tmp_path / "docs_py"
    renderer_py.render(catalog, str(output_dir_py))
    assert (output_dir_py / "class_ude_parsers_Parser.md").exists()

    # Render without namespace name
    renderer_cpp = HugoMarkdownRenderer(language="cpp")
    catalog_no_ns = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="",
                classes=[
                    ClassEntity(
                        name="GlobalClass",
                        fully_qualified_name="GlobalClass",
                        docstring="Global utility class.",
                    )
                ]
            )
        ]
    )
    output_dir_no_ns = tmp_path / "docs_no_ns"
    renderer_cpp.render(catalog_no_ns, str(output_dir_no_ns))
    assert (output_dir_no_ns / "class_GlobalClass.md").exists()


def test_renderer_io_error_raises_renderer_error(tmp_path):
    """Verify that any physical disk writing error is cleanly wrapped in RendererError."""
    renderer = HugoMarkdownRenderer(language="cpp")
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="NS",
                classes=[ClassEntity(name="A", fully_qualified_name="NS::A")]
            )
        ]
    )
    
    # Create a physical file. Attempting to make a directory with this name will fail.
    conflict_file = tmp_path / "conflict_file"
    conflict_file.write_text("already exists", encoding="utf-8")
    
    with pytest.raises(RendererError) as excinfo:
        renderer.render(catalog, str(conflict_file))
    assert "Failed to render Markdown output" in str(excinfo.value)


def test_unreachable_language_fallback(tmp_path):
    """Verify fallback class path resolution when language validation is bypassed."""
    renderer = HugoMarkdownRenderer(language="cpp")
    renderer.language = "unsupported"  # Forcefully bypass init validation
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="NS",
                classes=[ClassEntity(name="A", fully_qualified_name="CustomName")]
            )
        ]
    )
    output_dir = tmp_path / "docs_fallback"
    renderer.render(catalog, str(output_dir))
    # It should fall back to using cls.fully_qualified_name
    assert (output_dir / "class_CustomName.md").exists()
