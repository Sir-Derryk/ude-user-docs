# engine/tests/test_doxygen_parser.py
# All documentation, docstrings, and code comments are strictly in English.

import inspect
import pytest
from pathlib import Path
from tests.utils import MockAssetLoader
from ude.interfaces import BaseParser, ParserError
from ude.parsers.doxygen import DoxygenXmlParser, strip_export_macros
from ude.models import ProjectCatalog

def test_inheritance_and_traceability():
    """Verify that DoxygenXmlParser inherits from BaseParser and includes traceability.
    
    Satisfies REQ-FUN-02, REQ-FUN-19, REQ-FUN-20
    """
    parser = DoxygenXmlParser()
    assert isinstance(parser, BaseParser)
    
    # Check docstrings for traceability
    doc = DoxygenXmlParser.__doc__
    assert doc is not None
    assert "Satisfies REQ-FUN-02, REQ-FUN-19, REQ-FUN-20" in doc
    
    doc_parse = DoxygenXmlParser.parse.__doc__
    assert doc_parse is not None
    assert "Satisfies REQ-FUN-02" in doc_parse

def test_strip_export_macros_helper():
    """Verify the utility function to strip compiler-specific export macros.
    
    Satisfies REQ-FUN-19
    """
    assert strip_export_macros("NWDBEXPORT MyClass") == "MyClass"
    assert strip_export_macros("void MAPEXPORT render") == "void render"
    assert strip_export_macros("MyClass") == "MyClass"
    assert strip_export_macros(None) is None

def test_parser_with_standard_class(tmp_path):
    """Verify parsing of a standard class with mock index and definition.
    
    Satisfies REQ-FUN-02
    """
    loader = MockAssetLoader()
    
    # Write mock index.xml and class_my_class.xml to tmp_path
    index_xml = loader.load_xml("index.xml")
    class_def = loader.load_xml("class_definition.xml")
    
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_my_class.xml").write_text(class_def, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    assert isinstance(catalog, ProjectCatalog)
    assert len(catalog.namespaces) == 1
    
    ns = catalog.namespaces[0]
    assert ns.name == "" # MyClass is global in the mock
    assert len(ns.classes) == 1
    
    cls = ns.classes[0]
    assert cls.name == "MyClass"
    assert cls.fully_qualified_name == "MyClass"
    assert "Does something useful." in cls.methods[0].docstring
    assert cls.methods[0].name == "doSomething"
    assert cls.methods[0].return_type == "void"
    assert cls.methods[0].signature == "void MyClass::doSomething()"

def test_parser_with_macros(tmp_path):
    """Verify that compiler-specific export macros are stripped during parsing.
    
    Satisfies REQ-FUN-02, REQ-FUN-19
    """
    loader = MockAssetLoader()
    
    # We will create an index mapping to the class with macros
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_my_exported_class" kind="class">
    <name>NWDBEXPORT MyExportedClass</name>
  </compound>
</doxygenindex>
"""
    class_macros = loader.load_xml("class_with_macros.xml")
    
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_my_exported_class.xml").write_text(class_macros, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    assert len(ns.classes) == 1
    
    cls = ns.classes[0]
    assert cls.name == "MyExportedClass"
    assert cls.fully_qualified_name == "MyExportedClass"
    
    assert len(cls.methods) == 1
    method = cls.methods[0]
    assert method.name == "render"
    assert method.return_type == "void"
    assert "MAPEXPORT" not in method.signature
    assert method.signature == "void MyExportedClass::render()"

def test_parser_with_swig_internals_enabled(tmp_path):
    """Verify that SWIG wrapper internals are filtered out when config is set.
    
    Satisfies REQ-FUN-02, REQ-FUN-20
    """
    loader = MockAssetLoader()
    
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_swig_class" kind="class">
    <name>SwigClass</name>
  </compound>
</doxygenindex>
"""
    class_swig = loader.load_xml("class_swig_wrapper.xml")
    
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_swig_class.xml").write_text(class_swig, encoding="utf-8")
    
    # With SWIG filtering enabled
    parser = DoxygenXmlParser(exclude_swig_internals=True)
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    cls = ns.classes[0]
    
    # SwigClass should have 0 methods (Dispose is filtered) and 0 fields (swigCPtr is filtered)
    assert len(cls.methods) == 0
    assert len(cls.fields) == 0

def test_parser_with_swig_internals_disabled(tmp_path):
    """Verify that SWIG wrapper internals are preserved when config is unset.
    
    Satisfies REQ-FUN-02, REQ-FUN-20
    """
    loader = MockAssetLoader()
    
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_swig_class" kind="class">
    <name>SwigClass</name>
  </compound>
</doxygenindex>
"""
    class_swig = loader.load_xml("class_swig_wrapper.xml")
    
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_swig_class.xml").write_text(class_swig, encoding="utf-8")
    
    # With SWIG filtering disabled
    parser = DoxygenXmlParser(exclude_swig_internals=False)
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    cls = ns.classes[0]
    
    # SwigClass should preserve fields and methods
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "Dispose"
    assert len(cls.fields) == 1
    assert "swigCPtr" in cls.fields[0]

def test_parser_missing_files_or_malformed(tmp_path):
    """Verify that ParserError is raised under error conditions.
    
    Satisfies REQ-FUN-02
    """
    parser = DoxygenXmlParser()
    
    # Non-existent path
    with pytest.raises(ParserError):
        parser.parse("non_existent_directory_12345")
        
    # Empty directory (missing index.xml)
    with pytest.raises(ParserError):
        parser.parse(str(tmp_path))
        
    # Malformed index.xml
    (tmp_path / "index.xml").write_text("not-even-xml", encoding="utf-8")
    with pytest.raises(ParserError):
        parser.parse(str(tmp_path))

def test_parser_nested_structures_and_templates(tmp_path):
    """Verify namespace reconstruction and template bracket handling.
    
    Satisfies REQ-FUN-02
    """
    # Create an index with nested classes and templates
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_traits" kind="class">
    <name>MyNamespace::Traits&lt;Type::Value&gt;</name>
  </compound>
</doxygenindex>
"""
    class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_traits" kind="class" language="C++" prot="public">
    <compoundname>MyNamespace::Traits&lt;Type::Value&gt;</compoundname>
    <sectiondef kind="public-func">
      <memberdef kind="function" id="class_traits_1a1" prot="public" static="no" const="no" explicit="no" inline="no" virt="normal">
        <type></type>
        <definition>MyNamespace::Traits&lt;Type::Value&gt;::Traits</definition>
        <argsstring>()</argsstring>
        <name>Traits</name>
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_traits.xml").write_text(class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    assert ns.name == "MyNamespace"
    assert len(ns.classes) == 1
    
    cls = ns.classes[0]
    assert cls.name == "Traits<Type::Value>"
    assert cls.fully_qualified_name == "MyNamespace::Traits<Type::Value>"
    
    # Constructor check: no return type, signature built
    assert len(cls.methods) == 1
    method = cls.methods[0]
    assert method.name == "Traits"
    assert method.return_type == ""
    assert method.signature == "MyNamespace::Traits<Type::Value>::Traits()"

def test_parser_with_various_kinds_and_missing_files(tmp_path):
    """Verify handling of non-class compounds, missing compounddefs, and fallback fields.
    
    Satisfies REQ-FUN-02
    """
    # 1. Non-class compound (e.g. namespace compound in index.xml) should be skipped
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="namespace_foo" kind="namespace">
    <name>Foo</name>
  </compound>
  <compound refid="class_my_class" kind="class">
    <name>MyClass</name>
  </compound>
</doxygenindex>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    
    # 2. If file doesn't exist and scanning also finds nothing
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    assert len(catalog.namespaces) == 0  # skipped because class file not found anywhere
    
    # 3. Now write a file that has a different name but contains the correct id (triggers scanning)
    # We also write an invalid XML file to ensure scanning handles exception during ET.parse gracefully
    class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_my_class" kind="class" language="C++">
    <compoundname>MyClass</compoundname>
    <sectiondef kind="public-attrib">
      <memberdef kind="variable" id="var1">
        <type>int</type>
        <name>my_var</name>
        <!-- missing definition to trigger fallback field parser -->
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "different_name.xml").write_text(class_xml, encoding="utf-8")
    (tmp_path / "aaaa_invalid.xml").write_text("<invalid>xml syntax", encoding="utf-8")
    catalog = parser.parse(str(tmp_path))
    assert len(catalog.namespaces) == 1
    cls = catalog.namespaces[0].classes[0]
    assert cls.name == "MyClass"
    assert len(cls.fields) == 1
    assert cls.fields[0] == "int my_var"

def test_parser_malformed_compound(tmp_path):
    """Verify that malformed compound files raise ParserError.
    
    Satisfies REQ-FUN-02
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_malformed" kind="class">
    <name>Malformed</name>
  </compound>
</doxygenindex>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_malformed.xml").write_text("invalid xml text", encoding="utf-8")
    
    parser = DoxygenXmlParser()
    with pytest.raises(ParserError):
        parser.parse(str(tmp_path))

def test_parser_empty_compounddef(tmp_path):
    """Verify handling when compounddef is missing in compound file.
    
    Satisfies REQ-FUN-02
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_empty" kind="class">
    <name>Empty</name>
  </compound>
</doxygenindex>
"""
    class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <!-- missing compounddef -->
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_empty.xml").write_text(class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    # Since compounddef is missing, it returns None, so class_empty is not added
    assert len(catalog.namespaces) == 0

def test_parser_method_fallbacks_and_params(tmp_path):
    """Verify method fallback signature parsing and parameter extraction.
    
    Satisfies REQ-FUN-02
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_fallback" kind="class">
    <name>Fallback</name>
  </compound>
</doxygenindex>
"""
    class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_fallback" kind="class" language="C++">
    <compoundname>Fallback</compoundname>
    <sectiondef kind="public-func">
      <memberdef kind="function" id="f1" static="yes">
        <!-- missing type entirely -->
        <!-- missing definition to trigger fallback signature -->
        <name>compute</name>
        <param>
          <type>int</type>
          <declname>a</declname>
        </param>
        <param>
          <type>double</type>
          <declname>b</declname>
        </param>
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_fallback.xml").write_text(class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    cls = catalog.namespaces[0].classes[0]
    method = cls.methods[0]
    assert method.name == "compute"
    assert method.return_type == ""
    assert len(method.parameters) == 2
    assert method.parameters[0].name == "a"
    assert method.parameters[0].type == "int"
    assert method.parameters[1].name == "b"
    assert method.parameters[1].type == "double"
    # fallback signature check
    assert method.signature == "static compute(int a, double b)"

def test_parser_with_completely_empty_field(tmp_path):
    """Verify field parser returns None for empty memberdef.
    
    Satisfies REQ-FUN-02
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_empty_field" kind="class">
    <name>EmptyField</name>
  </compound>
</doxygenindex>
"""
    class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_empty_field" kind="class" language="C++">
    <compoundname>EmptyField</compoundname>
    <sectiondef kind="public-attrib">
      <memberdef kind="variable" id="var1">
        <!-- missing definition, type, and name completely -->
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_empty_field.xml").write_text(class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    cls = catalog.namespaces[0].classes[0]
    assert len(cls.fields) == 0
