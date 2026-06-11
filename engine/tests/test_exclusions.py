# engine/tests/test_exclusions.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from pathlib import Path
from ude.interfaces import ParserError
from ude.parsers.doxygen import DoxygenXmlParser
from ude.models import ProjectCatalog

def test_class_enclosed_in_dom_ignore(tmp_path):
    """Verify that a class enclosed in DOM-IGNORE-BEGIN and DOM-IGNORE-END is omitted.
    
    Satisfies REQ-FUN-13
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <!-- DOM-IGNORE-BEGIN -->
  <compound refid="class_hidden_class" kind="class">
    <name>HiddenClass</name>
  </compound>
  <!-- DOM-IGNORE-END -->
  <compound refid="class_visible_class" kind="class">
    <name>VisibleClass</name>
  </compound>
</doxygenindex>
"""
    visible_class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_visible_class" kind="class" language="C++">
    <compoundname>VisibleClass</compoundname>
  </compounddef>
</doxygen>
"""
    hidden_class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_hidden_class" kind="class" language="C++">
    <compoundname>HiddenClass</compoundname>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_visible_class.xml").write_text(visible_class_xml, encoding="utf-8")
    (tmp_path / "class_hidden_class.xml").write_text(hidden_class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    assert len(ns.classes) == 1
    assert ns.classes[0].name == "VisibleClass"


def test_members_enclosed_in_dom_ignore(tmp_path):
    """Verify that methods and fields enclosed in DOM-IGNORE-BEGIN and DOM-IGNORE-END are omitted.
    
    Satisfies REQ-FUN-13
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_test_class" kind="class">
    <name>TestClass</name>
  </compound>
</doxygenindex>
"""
    test_class_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_test_class" kind="class" language="C++">
    <compoundname>TestClass</compoundname>
    <sectiondef kind="public-func">
      <memberdef kind="function" id="f_visible">
        <name>visibleMethod</name>
        <type>void</type>
      </memberdef>
      <!-- DOM-IGNORE-BEGIN -->
      <memberdef kind="function" id="f_hidden">
        <name>hiddenMethod</name>
        <type>void</type>
      </memberdef>
      <!-- DOM-IGNORE-END -->
    </sectiondef>
    <sectiondef kind="public-attrib">
      <memberdef kind="variable" id="v_visible">
        <name>visibleVar</name>
        <type>int</type>
      </memberdef>
      <!-- DOM-IGNORE-BEGIN -->
      <memberdef kind="variable" id="v_hidden">
        <name>hiddenVar</name>
        <type>int</type>
      </memberdef>
      <!-- DOM-IGNORE-END -->
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_test_class.xml").write_text(test_class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    cls = catalog.namespaces[0].classes[0]
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "visibleMethod"
    assert len(cls.fields) == 1
    assert cls.fields[0] == "int visibleVar"


def test_conditional_blocks_cond_directive(tmp_path):
    """Verify that conditional blocks wrapped in cond/endcond directives are omitted.
    
    Satisfies REQ-FUN-13
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_test_class" kind="class">
    <name>TestClass</name>
  </compound>
</doxygenindex>
"""
    test_class_xml = r"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_test_class" kind="class" language="C++">
    <compoundname>TestClass</compoundname>
    <sectiondef kind="public-func">
      <!-- \cond -->
      <memberdef kind="function" id="f_cond1">
        <name>condMethod1</name>
        <type>void</type>
      </memberdef>
      <!-- \endcond -->
      <!-- @cond -->
      <memberdef kind="function" id="f_cond2">
        <name>condMethod2</name>
        <type>void</type>
      </memberdef>
      <!-- @endcond -->
      <memberdef kind="function" id="f_visible">
        <name>visibleMethod</name>
        <type>void</type>
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_test_class.xml").write_text(test_class_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    cls = catalog.namespaces[0].classes[0]
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "visibleMethod"


def test_internal_tag_exclusions_in_docstrings(tmp_path):
    """Verify that code entities containing internal tag in docstrings are omitted.
    
    Satisfies REQ-FUN-13
    """
    index_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygenindex version="1.9.8">
  <compound refid="class_visible_class" kind="class">
    <name>VisibleClass</name>
  </compound>
  <compound refid="class_internal_class1" kind="class">
    <name>InternalClass1</name>
  </compound>
  <compound refid="class_internal_class2" kind="class">
    <name>InternalClass2</name>
  </compound>
</doxygenindex>
"""
    visible_class_xml = r"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_visible_class" kind="class" language="C++">
    <compoundname>VisibleClass</compoundname>
    <sectiondef kind="public-func">
      <memberdef kind="function" id="f_visible">
        <name>visibleMethod</name>
        <type>void</type>
        <briefdescription>
          <para>Standard visible method.</para>
        </briefdescription>
      </memberdef>
      <memberdef kind="function" id="f_internal">
        <name>internalMethod</name>
        <type>void</type>
        <detaileddescription>
          <para>Do not use this. \internal This is an internal detail.</para>
        </detaileddescription>
      </memberdef>
    </sectiondef>
    <sectiondef kind="public-attrib">
      <memberdef kind="variable" id="v_visible">
        <name>visibleVar</name>
        <type>int</type>
      </memberdef>
      <memberdef kind="variable" id="v_internal">
        <name>internalVar</name>
        <type>int</type>
        <briefdescription>
          <para>@internal Some internal field detail</para>
        </briefdescription>
      </memberdef>
    </sectiondef>
  </compounddef>
</doxygen>
"""
    internal_class1_xml = r"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_internal_class1" kind="class" language="C++">
    <compoundname>InternalClass1</compoundname>
    <briefdescription>
      <para>\internal This class is for internal use only.</para>
    </briefdescription>
  </compounddef>
</doxygen>
"""
    internal_class2_xml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<doxygen xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.9.8">
  <compounddef id="class_internal_class2" kind="class" language="C++">
    <compoundname>InternalClass2</compoundname>
    <detaileddescription>
      <para>@internal This class is also internal.</para>
    </detaileddescription>
  </compounddef>
</doxygen>
"""
    (tmp_path / "index.xml").write_text(index_xml, encoding="utf-8")
    (tmp_path / "class_visible_class.xml").write_text(visible_class_xml, encoding="utf-8")
    (tmp_path / "class_internal_class1.xml").write_text(internal_class1_xml, encoding="utf-8")
    (tmp_path / "class_internal_class2.xml").write_text(internal_class2_xml, encoding="utf-8")
    
    parser = DoxygenXmlParser()
    catalog = parser.parse(str(tmp_path))
    
    assert len(catalog.namespaces) == 1
    ns = catalog.namespaces[0]
    assert len(ns.classes) == 1
    cls = ns.classes[0]
    assert cls.name == "VisibleClass"
    
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "visibleMethod"
    
    assert len(cls.fields) == 1
    assert cls.fields[0] == "int visibleVar"
