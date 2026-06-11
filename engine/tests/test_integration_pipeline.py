# engine/tests/test_integration_pipeline.py
# All documentation, docstrings, and code comments are strictly in English.

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from ude.orchestrator import UdeOrchestrator
from ude.storage import BuildCacheManager
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity
from tests.utils import MockAssetLoader

def test_e2e_pipeline_without_collector(tmp_path):
    """Verify the entire parsing and rendering flow when XML files are pre-generated.
    
    This avoids running the collector subprocess.
    """
    # 1. Set up product.json
    product_file = tmp_path / "product.json"
    product_file.write_text(
        json.dumps({"product_name": "TestE2EProduct", "version": "1.2.3"}),
        encoding="utf-8"
    )
    
    # 2. Set up global config
    global_file = tmp_path / "ude_global.json"
    global_file.write_text(
        json.dumps({"error_policy": "continue-on-error", "logging": {"level": "INFO"}}),
        encoding="utf-8"
    )
    
    # 3. Create target directory
    target_dir = tmp_path / "target_cpp"
    target_dir.mkdir()
    
    # 4. Copy XML mock assets to an xml_src directory under target_cpp
    xml_src_dir = target_dir / "xml_src"
    xml_src_dir.mkdir()
    
    loader = MockAssetLoader()
    (xml_src_dir / "index.xml").write_text(loader.load_xml("index.xml"), encoding="utf-8")
    (xml_src_dir / "class_my_class.xml").write_text(loader.load_xml("class_definition.xml"), encoding="utf-8")
    (xml_src_dir / "class_swig_wrapper.xml").write_text(loader.load_xml("class_swig_wrapper.xml"), encoding="utf-8")
    
    # 5. Create local target config
    config_file = target_dir / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": "xml_src",
            "output_dir": "html_out",
            "renderer": {"type": "html"},
            "collector": {"language": "cpp"}
        }),
        encoding="utf-8"
    )
    
    # 6. Run orchestration
    orchestrator = UdeOrchestrator()
    success = orchestrator.run([config_file])
    assert success is True
    
    # 7. Validate output HTML files
    html_out = target_dir / "html_out"
    assert html_out.exists()
    assert (html_out / "index.html").exists()
    assert (html_out / "class_MyClass.html").exists()
    
    # Check that Highlight.js and collapsible sidebars are present in the HTML
    html_content = (html_out / "class_MyClass.html").read_text(encoding="utf-8")
    assert "MyClass" in html_content
    assert "doSomething" in html_content
    assert "highlight.js" in html_content.lower()


@patch("subprocess.run")
@patch("shutil.which")
def test_e2e_pipeline_with_collector(mock_which, mock_run, tmp_path):
    """Verify the entire flow including dynamic DoxygenXmlCollector execution.
    
    Mocks subprocess.run to copy XML assets when doxygen is called.
    """
    mock_which.return_value = "doxygen"
    
    # Setup mock subprocess run to write XML files to the temporary xml directory
    def side_effect(args, **kwargs):
        doxyfile_path = Path(args[1])
        base_dir = doxyfile_path.parent  # temp_xml
        xml_out = base_dir / "xml"
        xml_out.mkdir(parents=True, exist_ok=True)
        
        # Write mock XML assets
        loader = MockAssetLoader()
        (xml_out / "index.xml").write_text(loader.load_xml("index.xml"), encoding="utf-8")
        (xml_out / "class_my_class.xml").write_text(loader.load_xml("class_definition.xml"), encoding="utf-8")
        (xml_out / "class_swig_wrapper.xml").write_text(loader.load_xml("class_swig_wrapper.xml"), encoding="utf-8")
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        return mock_proc
        
    mock_run.side_effect = side_effect
    
    # 1. Set up product.json
    product_file = tmp_path / "product.json"
    product_file.write_text(
        json.dumps({"product_name": "TestE2EProductCol", "version": "2.0.0"}),
        encoding="utf-8"
    )
    
    # 2. Create target directory
    target_dir = tmp_path / "target_cpp_col"
    target_dir.mkdir()
    
    # 3. Create dummy source folder & file
    src_dir = target_dir / "src"
    src_dir.mkdir()
    (src_dir / "dummy.cpp").write_text("// dummy source file", encoding="utf-8")
    
    # 4. Create dummy Doxyfile template
    doxyfile = target_dir / "Doxyfile"
    doxyfile.write_text("GENERATE_XML = YES", encoding="utf-8")
    
    # 5. Create local target config
    config_file = target_dir / "ude_config.json"
    config_file.write_text(
        json.dumps({
            "src_dir": "src",
            "output_dir": "hugo_out",
            "renderer": {"type": "hugo_markdown"},
            "collector": {
                "type": "cpp",
                "src_dir": "src",
                "doxyfile_template": "Doxyfile"
            }
        }),
        encoding="utf-8"
    )
    
    # 6. Run orchestration
    orchestrator = UdeOrchestrator()
    success = orchestrator.run([config_file])
    assert success is True
    
    # 7. Validate output Hugo Markdown files
    hugo_out = target_dir / "hugo_out"
    assert hugo_out.exists()
    assert (hugo_out / "class_MyClass.md").exists()
    
    # Check front-matter metadata in generated Hugo markdown
    md_content = (hugo_out / "class_MyClass.md").read_text(encoding="utf-8")
    assert "title: \"MyClass\"" in md_content or "title: MyClass" in md_content
    assert "MyClass" in md_content
    assert "doSomething" in md_content


def test_e2e_pipeline_with_two_level_cache(tmp_path):
    """Verify that BuildCacheManager integrates cleanly and tracks incremental updates.
    
    We run a simulated build pipeline, save its state into BuildCacheManager, and assert
    that consecutive runs identify unchanged resources.
    """
    # Create product directory for BuildCacheManager
    product_dir = tmp_path / "product_dir"
    product_dir.mkdir()
    
    cache_manager = BuildCacheManager(product_dir)
    
    # 1. Simulate Parsing (L1 Cache)
    xml_file = product_dir / "class_my_class.xml"
    loader = MockAssetLoader()
    xml_file.write_text(loader.load_xml("class_definition.xml"), encoding="utf-8")
    
    # Check parsing cache (L1) - initially a miss
    is_l1_hit = cache_manager.get_l1_entry(xml_file)
    assert is_l1_hit is None
    
    # Cache the file signature
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="TestNamespace",
                classes=[
                    ClassEntity(
                        name="TestClass",
                        fully_qualified_name="TestNamespace::TestClass",
                    )
                ],
            )
        ]
    )
    cache_manager.set_l1_entry(xml_file, catalog)
    cache_manager.save()
    
    # Second manager instance loads saved state and should report a hit (L1)
    new_cache_manager = BuildCacheManager(product_dir)
    cached_catalog = new_cache_manager.get_l1_entry(xml_file)
    assert cached_catalog is not None
    assert cached_catalog.namespaces[0].name == "TestNamespace"
    
    # Modify file contents and assert L1 cache miss
    xml_file.write_text("modified contents", encoding="utf-8")
    assert new_cache_manager.get_l1_entry(xml_file) is None
    
    # 2. Simulate Rendering (L2 Cache)
    target_file = product_dir / "output.md"
    entity_signature = "MyClass_signature_v1"
    template_content = "<html>{{ entity }}</html>"
    
    # Check rendering cache (L2) - initially a miss
    is_l2_hit = cache_manager.check_l2_hit(target_file, entity_signature, template_content)
    assert is_l2_hit is False
    
    # Cache the rendering signature by writing if changed
    wrote = cache_manager.write_if_changed(target_file, "content", entity_signature, template_content)
    assert wrote is True
    cache_manager.save()
    
    # Second manager instance should report a hit (L2)
    new_cache_manager_l2 = BuildCacheManager(product_dir)
    assert new_cache_manager_l2.check_l2_hit(target_file, entity_signature, template_content) is True
