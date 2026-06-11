# engine/tests/test_caching.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
import time
from pathlib import Path
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity
from ude.storage import BuildCacheManager, calculate_sha256


def test_level_1_xml_parsing_cache(tmp_path):
    """Test Level 1 Parsing Cache hit, miss, modifications, and path portability."""
    product_dir = tmp_path / "build"
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    xml_file = src_dir / "test_class.xml"
    xml_file.write_text(
        "<class name='Test'><method name='foo'/></class>", encoding="utf-8"
    )

    # Initialize cache manager
    manager = BuildCacheManager(product_dir)

    # Cache miss on first check
    assert manager.get_l1_entry(xml_file) is None

    # Simulate parser creating catalog and storing in cache
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
    manager.set_l1_entry(xml_file, catalog)
    manager.save()

    # Verify cache file exists
    cache_file = product_dir / ".build_cache.json.gz"
    assert cache_file.exists()

    # Create new manager and verify cache hit
    new_manager = BuildCacheManager(product_dir)
    cached_catalog = new_manager.get_l1_entry(xml_file)
    assert cached_catalog is not None
    assert cached_catalog.namespaces[0].name == "TestNamespace"

    # Modify XML file content (changes hash, size, and mtime)
    xml_file.write_text(
        "<class name='Test'><method name='foo'/><method name='bar'/></class>",
        encoding="utf-8",
    )

    # Cache miss after file modification
    assert new_manager.get_l1_entry(xml_file) is None


def test_level_2_rendering_cache(tmp_path):
    """Test Level 2 Rendering Cache write skip, miss, and file deletions."""
    product_dir = tmp_path / "build"
    target_file = product_dir / "output.md"

    manager = BuildCacheManager(product_dir)

    content = "# Document content"
    entity_sig = "class TestClass { void foo(); }"
    template = "Jinja2 template body text"

    # 1. Miss initially (since target file doesn't exist)
    assert manager.check_l2_hit(target_file, entity_sig, template) is False

    # 2. Write file
    wrote = manager.write_if_changed(target_file, content, entity_sig, template)
    assert wrote is True
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == content

    # Capture modification time
    first_mtime = target_file.stat().st_mtime_ns

    # Save cache state
    manager.save()

    # 3. Hit on second check with same signatures/templates
    new_manager = BuildCacheManager(product_dir)
    assert new_manager.check_l2_hit(target_file, entity_sig, template) is True

    # 4. Attempt to write again — should skip physical I/O
    # We can sleep a tiny bit to make sure mtime would change if written
    time.sleep(0.01)
    wrote = new_manager.write_if_changed(target_file, content, entity_sig, template)
    assert wrote is False

    # Verify file was NOT physically written (mtime remains identical)
    assert target_file.stat().st_mtime_ns == first_mtime

    # 5. Miss if template content changes
    new_template = "Modified Jinja2 template body"
    assert new_manager.check_l2_hit(target_file, entity_sig, new_template) is False
    wrote = new_manager.write_if_changed(target_file, content, entity_sig, new_template)
    assert wrote is True

    # 6. Miss if entity signature changes
    new_entity_sig = "class TestClass { void bar(); }"
    assert new_manager.check_l2_hit(target_file, new_entity_sig, new_template) is False
    wrote = new_manager.write_if_changed(
        target_file, content, new_entity_sig, new_template
    )
    assert wrote is True

    # 7. Miss if file physically deleted from disk
    target_file.unlink()
    assert new_manager.check_l2_hit(target_file, new_entity_sig, new_template) is False
    wrote = new_manager.write_if_changed(
        target_file, content, new_entity_sig, new_template
    )
    assert wrote is True
    assert target_file.exists()


def test_corrupted_cache_handles_gracefully(tmp_path):
    """Test that a corrupted cache database is ignored and gracefully replaced with an empty cache."""
    product_dir = tmp_path / "build"
    product_dir.mkdir()
    cache_file = product_dir / ".build_cache.json.gz"

    # Write invalid data to the cache file
    cache_file.write_text("invalid gzip or json content", encoding="utf-8")

    # Should load without exceptions and return empty cache
    manager = BuildCacheManager(product_dir)
    assert len(manager._cache.l1) == 0
    assert len(manager._cache.l2) == 0


def test_cache_edge_cases(tmp_path):
    """Test L1 and L2 caching lookup exceptions and missing cache records with existing files."""
    product_dir = tmp_path / "build"
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    xml_file = src_dir / "test.xml"
    xml_file.write_text("<xml/>", encoding="utf-8")

    manager = BuildCacheManager(product_dir)
    catalog = ProjectCatalog()

    # 1. Set L1 cache entry successfully
    manager.set_l1_entry(xml_file, catalog)
    assert manager.get_l1_entry(xml_file) is not None

    # 2. Delete XML file, then get_l1_entry should raise FileNotFoundError internally
    # and handle it gracefully by returning None (hitting except block)
    xml_file.unlink()
    assert manager.get_l1_entry(xml_file) is None

    # 3. Call set_l1_entry with a non-existent file, hitting the except block inside set_l1_entry
    manager.set_l1_entry(xml_file, catalog)

    # 4. Target file exists physically on disk, but there is no entry in Level 2 cache
    target_file = product_dir / "output.md"
    product_dir.mkdir(parents=True, exist_ok=True)
    target_file.write_text("manually written", encoding="utf-8")

    # check_l2_hit should return False because there is no cache entry, even though file exists
    assert manager.check_l2_hit(target_file, "signature", "template") is False
