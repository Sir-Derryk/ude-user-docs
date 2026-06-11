---
title: "HugoMarkdownRenderer"
sidebar_position: 21
parent: "ude::renderers::hugo_markdown"
---

# HugoMarkdownRenderer

Renderer to convert ProjectCatalog IR into Markdown documentation with YAML front-matter.

Satisfies REQ-FUN-03

## Fields

- `ude.renderers.hugo_markdown.HugoMarkdownRenderer::language`

## Methods

### __init__
`ude.renderers.hugo_markdown.HugoMarkdownRenderer.__init__(self, str language)`

Initializes the HugoMarkdownRenderer with a specific target language.

Args:
    language: The language mapping rules to use ('cpp', 'python', 'java', 'csharp').

Raises:
    ValueError: If the language is unsupported.

Satisfies REQ-FUN-03

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| language | `str` |  |

### resolve_filename
`str ude.renderers.hugo_markdown.HugoMarkdownRenderer.resolve_filename(self, str api_path, str entity_type="class")`

Translates a logical API path to a safe, physical, flat disk filename on Hugo/Docusaurus.

Satisfies REQ-FUN-03, REQ-FUN-04, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| api_path | `str` |  |
| entity_type | `str` |  |

### render
`None ude.renderers.hugo_markdown.HugoMarkdownRenderer.render(self, ProjectCatalog catalog, str output_path)`

Renders the ProjectCatalog documentation into Hugo-compatible Markdown files.

Args:
    catalog: The Intermediate Representation (IR) catalog containing entities.
    output_path: Path to the output directory on disk.

Raises:
    RendererError: If rendering fails due to I/O issues.

Satisfies REQ-FUN-03

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| catalog | `ProjectCatalog` |  |
| output_path | `str` |  |

### _escape_angle_brackets
`str ude.renderers.hugo_markdown.HugoMarkdownRenderer._escape_angle_brackets(self, str text)`

Escapes template angle brackets outside code blocks to avoid MDX parsing issues.

Satisfies REQ-FUN-32

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| text | `str` |  |

