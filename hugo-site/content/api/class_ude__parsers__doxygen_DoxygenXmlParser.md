---
title: "DoxygenXmlParser"
sidebar_position: 19
parent: "ude::parsers::doxygen"
---

# DoxygenXmlParser

Doxygen XML parser mapping nested C++, C#, Java, and Python structures.

This parser ingests raw metrics and code structures from an index.xml catalog and
resolves the complete document graph into a language-agnostic Intermediate Representation.

Satisfies REQ-FUN-02, REQ-FUN-19, REQ-FUN-20

## Fields

- `ude.parsers.doxygen.DoxygenXmlParser::exclude_swig_internals`
- `ude.parsers.doxygen.DoxygenXmlParser::swig_fields`
- `ude.parsers.doxygen.DoxygenXmlParser::swig_methods`

## Methods

### __init__
`ude.parsers.doxygen.DoxygenXmlParser.__init__(self, bool exclude_swig_internals=False, **kwargs)`

Initializes the DoxygenXmlParser with configuration flags.

Args:
    exclude_swig_internals: If True, filters out SWIG specific members and fields.
    **kwargs: Additional configuration parameters.

Satisfies REQ-FUN-02, REQ-FUN-20

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| exclude_swig_internals | `bool` |  |
| kwargs | `**` |  |

### _filter_exclusions
`str ude.parsers.doxygen.DoxygenXmlParser._filter_exclusions(self, str xml_text)`

Filters out exclusion ranges from the raw XML text.

Removes anything between  and
between \ or .

Args:
    xml_text: Raw XML string content.

Returns:
    XML string content with excluded blocks stripped.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| xml_text | `str` |  |

