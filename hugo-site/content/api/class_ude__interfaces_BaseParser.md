---
title: "BaseParser"
sidebar_position: 2
parent: "ude::interfaces"
---

# BaseParser

Abstract base class establishing the contract for all documentation parsers.

Parsers ingest raw metrics and code structures from XML directories or code files and
map them into the language-agnostic Intermediate Representation (IR).

Satisfies REQ-FUN-02

## Methods

### parse
`ProjectCatalog ude.interfaces.BaseParser.parse(self, str input_path)`

Parses the input path and returns a validated ProjectCatalog instance.

Args:
    input_path: Path to the target Doxygen XML directory, file, or native source file.

Returns:
    A populated ProjectCatalog representing the code structures.

Raises:
    ParserError: If parsing fails or input is malformed.

Satisfies REQ-FUN-02

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| input_path | `str` |  |

