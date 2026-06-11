---
title: "HtmlRenderer"
sidebar_position: 20
parent: "ude::renderers::static_html"
---

# HtmlRenderer

Renderer to convert ProjectCatalog IR into offline-friendly standalone HTML.

Satisfies REQ-FUN-03, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32

## Fields

- `ude.renderers.static_html.HtmlRenderer::language`
- `ude.renderers.static_html.HtmlRenderer::assets_src_dir`
- `ude.renderers.static_html.HtmlRenderer::name`

## Methods

### __init__
`ude.renderers.static_html.HtmlRenderer.__init__(self, str language, str assets_src_dir=None)`

Initializes the HtmlRenderer with a specific target language mapping.

Raises:
    ValueError: If the language is unsupported.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| language | `str` |  |
| assets_src_dir | `str` |  |

### resolve_filename
`str ude.renderers.static_html.HtmlRenderer.resolve_filename(self, str api_path, str entity_type="class")`

Translates a logical API path to a safe, physical, flat disk filename with .html suffix.

Satisfies REQ-FUN-03, REQ-FUN-30

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| api_path | `str` |  |
| entity_type | `str` |  |

### render
`None ude.renderers.static_html.HtmlRenderer.render(self, ProjectCatalog catalog, str output_path)`

Renders the ProjectCatalog documentation into standalone offline HTML pages.

Satisfies REQ-FUN-03, REQ-FUN-30, REQ-FUN-31, REQ-FUN-32

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| catalog | `ProjectCatalog` |  |
| output_path | `str` |  |

### _find_assets_source
`Path ude.renderers.static_html.HtmlRenderer._find_assets_source(self)`

Finds the directory containing reference CSS and images.

Prioritizes the directory specified in the configuration, 
and falls back to dynamic parent search for testing.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |

