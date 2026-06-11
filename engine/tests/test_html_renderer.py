# engine/tests/test_html_renderer.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from pathlib import Path
import json
import re
from ude.interfaces import BaseRenderer, RendererError
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity, MethodEntity, ParameterField

try:
    from ude.renderers.static_html import HtmlRenderer
except ImportError:
    HtmlRenderer = None


def test_html_renderer_import():
    """Verify that we can import HtmlRenderer or handle it in the RED phase."""
    assert HtmlRenderer is not None, "HtmlRenderer is not implemented yet."


def test_invalid_language():
    """Verify that instantiating with an unsupported language raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        HtmlRenderer(language="invalid")
    assert "Unsupported language" in str(excinfo.value)


@pytest.mark.parametrize(
    "language, api_path, entity_type, expected_filename",
    [
        # C++ Tests
        ("cpp", "FacetModeler::Body::faceCount", "variable", "variable_FacetModeler__Body__faceCount.html"),
        ("cpp", "FacetModeler::Traits<Type>::method", "method", "method_FacetModeler__Traits_lt_Type_gt___method.html"),
        ("cpp", "FacetModeler::Body::draw@int*,float&", "method", "method_FacetModeler__Body__draw@int_ptr_float_ref.html"),
        
        # C# Tests
        ("csharp", "Namespace.SubNamespace.Class.NestedClass.Method@int", "method", "method_Namespace__SubNamespace__Class__NestedClass__Method@int.html"),
        
        # Java Tests
        ("java", "org.example.pkg.Class.NestedClass.method@int", "method", "method_org_example_pkg_Class__NestedClass__method@int.html"),
        
        # Python Tests
        ("python", "ude.parsers.doxygen.DoxygenXmlParser.parse_file@str", "method", "method_ude_parsers_doxygen_DoxygenXmlParser__parse_file@str.html"),
    ],
)
def test_resolve_filename(language, api_path, entity_type, expected_filename):
    """Verify logical-to-physical flat-mapping rules with .html extension.
    
    Satisfies REQ-FUN-03, REQ-FUN-30
    """
    renderer = HtmlRenderer(language=language)
    assert renderer.resolve_filename(api_path, entity_type=entity_type) == expected_filename


def test_html_rendering_output(tmp_path):
    """Verify full ProjectCatalog rendering to offline standalone HTML.
    
    Satisfies REQ-FUN-03, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32
    """
    renderer = HtmlRenderer(language="cpp")
    
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="FacetModeler",
                classes=[
                    ClassEntity(
                        name="Body",
                        fully_qualified_name="FacetModeler::Body",
                        docstring="A representation of a 3D topological body in FacetModeler.",
                        fields=["faceCount"],
                        methods=[
                            MethodEntity(
                                name="draw",
                                signature="void draw(int* count, float& scale)",
                                parameters=[
                                    ParameterField(name="count", type="int*", description="Number of elements"),
                                    ParameterField(name="scale", type="float&", description="Scale factor"),
                                ],
                                return_type="void",
                                docstring="Draws the body.",
                            )
                        ]
                    )
                ]
            )
        ]
    )
    
    output_dir = tmp_path / "html_docs"
    renderer.render(catalog, str(output_dir))
    
    # 1. Verify nav_data.js contains CORS-free window.UDE_NAV_DATA array
    nav_js_file = output_dir / "nav_data.js"
    assert nav_js_file.exists()
    nav_content = nav_js_file.read_text(encoding="utf-8")
    assert nav_content.startswith("window.UDE_NAV_DATA =") or nav_content.startswith("var UDE_NAV_DATA =")
    
    # Extract JSON content to validate correctness
    json_match = re.search(r"=\s*(.*);\s*$", nav_content, re.DOTALL)
    assert json_match is not None
    json_str = json_match.group(1)
    nav_data = json.loads(json_str)
    assert isinstance(nav_data, list)
    assert len(nav_data) > 0
    
    # 2. Verify HTML page is written with standard layouts
    class_html_file = output_dir / "class_FacetModeler__Body.html"
    assert class_html_file.exists()
    html_content = class_html_file.read_text(encoding="utf-8")
    
    # Assert layout structures
    assert "class=\"OdaDocBrief\"" in html_content or "class='OdaDocBrief'" in html_content
    assert "class=\"OdaDocContainerTable\"" in html_content or "class='OdaDocContainerTable'" in html_content
    assert "class=\"OdaDocCodeProto\"" in html_content or "class='OdaDocCodeProto'" in html_content
    assert "class=\"OdaDocSplitter\"" in html_content or "class='OdaDocSplitter'" in html_content
    assert "id=\"sidebarSearch\"" in html_content or "id='sidebarSearch'" in html_content
    
    # 3. Verify assets are automatically copied
    assert (output_dir / "main.css").exists()
    assert (output_dir / "logo.svg").exists()
    assert (output_dir / "sidebar.js").exists()
    assert (output_dir / "search.js").exists()


def test_renderer_io_error_raises_renderer_error(tmp_path):
    """Verify that I/O issues are wrapped in RendererError."""
    renderer = HtmlRenderer(language="cpp")
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="NS",
                classes=[ClassEntity(name="A", fully_qualified_name="NS::A")]
            )
        ]
    )
    
    # Create a conflicting file where the directory should be
    conflict_file = tmp_path / "conflict_file"
    conflict_file.write_text("already exists", encoding="utf-8")
    
    with pytest.raises(RendererError) as excinfo:
        renderer.render(catalog, str(conflict_file))
    assert "Failed to render HTML output" in str(excinfo.value)


def test_empty_values_and_edge_cases(tmp_path):
    """Verify rare branches, empty classes/methods to ensure high coverage."""
    renderer = HtmlRenderer(language="cpp")
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="",
                classes=[
                    ClassEntity(
                        name="GlobalClass",
                        fully_qualified_name="GlobalClass",
                        docstring="",
                        fields=[],
                        methods=[]
                    )
                ]
            )
        ]
    )
    output_dir = tmp_path / "empty_docs"
    renderer.render(catalog, str(output_dir))
    
    html_file = output_dir / "class_GlobalClass.html"
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert "GlobalClass" in content


def test_full_coverage(tmp_path):
    from unittest.mock import patch

    # 1. Java path with package and nested classes
    renderer_java = HtmlRenderer(language="java")
    assert renderer_java.resolve_filename("org.pkg.Class.Nested") == "class_org_pkg_Class__Nested.html"
    assert renderer_java.resolve_filename("MyClass") == "class_MyClass.html"
    assert renderer_java.resolve_filename("org.example.package") == "class_org_example_package.html"  # Line 76
    
    # 2. Python path with packages and class members
    renderer_py = HtmlRenderer(language="python")
    assert renderer_py.resolve_filename("module.MyClass.method") == "class_module_MyClass__method.html"
    assert renderer_py.resolve_filename("MyClass") == "class_MyClass.html"
    assert renderer_py.resolve_filename("module.submodule.func") == "class_module_submodule__func.html"
    assert renderer_py.resolve_filename("mymodule") == "class_mymodule.html"  # Line 100
    
    # 3. Forced unsupported language fallback
    renderer_cpp = HtmlRenderer(language="cpp")
    renderer_cpp.language = "unsupported"
    assert renderer_cpp.resolve_filename("some_path") == "class_some_path.html"
    
    # 4. Cover find_assets_source except block and RendererError
    with patch.object(Path, "resolve", side_effect=Exception("mocked error")):
        with pytest.raises(RendererError) as excinfo:
            renderer_cpp._find_assets_source()
        assert "Reference assets directory not found" in str(excinfo.value)
            
    # 5. Render with non-cpp language having named namespace
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="org.example",
                classes=[ClassEntity(name="MyClass", fully_qualified_name="org.example.MyClass")]
            )
        ]
    )
    renderer_java.render(catalog, str(tmp_path / "java_render"))
    assert (tmp_path / "java_render" / "class_org_example_MyClass.html").exists()
 
    # 6. Cover rendering using fallback template (layout_file.exists() returns False)
    original_exists = Path.exists
    def patched_exists(self_obj):
        if "class_layout.html" in str(self_obj):
            return False
        return original_exists(self_obj)
        
    with patch.object(Path, "exists", patched_exists):
        renderer_cpp_fall = HtmlRenderer(language="cpp")
        catalog_fall = ProjectCatalog(
            namespaces=[
                NamespaceEntity(
                    name="FacetModeler",
                    classes=[ClassEntity(name="Body", fully_qualified_name="FacetModeler::Body")]
                )
            ]
        )
        renderer_cpp_fall.render(catalog_fall, str(tmp_path / "fallback_render"))
        assert (tmp_path / "fallback_render" / "class_FacetModeler__Body.html").exists()

    # 7. Check custom assets_src_dir
    custom_assets = tmp_path / "custom_assets"
    custom_assets.mkdir()
    renderer_with_assets = HtmlRenderer(language="cpp", assets_src_dir=str(custom_assets))
    assert renderer_with_assets._find_assets_source() == custom_assets

    # Test non-existent custom assets_src_dir raises RendererError
    renderer_bad_assets = HtmlRenderer(language="cpp", assets_src_dir="non_existent_path")
    with pytest.raises(RendererError) as excinfo:
        renderer_bad_assets._find_assets_source()
    assert "Configured assets_src_dir does not exist" in str(excinfo.value)
