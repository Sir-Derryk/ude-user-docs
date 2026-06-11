---
title: "BaseRenderer"
sidebar_position: 3
parent: "ude::interfaces"
---

# BaseRenderer

Abstract base class establishing the contract for all document renderers.

Renderers ingest a structured ProjectCatalog and output formatted Markdown or HTML files.

Satisfies REQ-FUN-03

## Methods

### render
`None ude.interfaces.BaseRenderer.render(self, ProjectCatalog catalog, str output_path)`

Renders the ProjectCatalog documentation into the specified output path.

Args:
    catalog: The Intermediate Representation (IR) containing documentation entities.
    output_path: Path to the output directory or target file on disk.

Raises:
    RendererError: If rendering fails due to missing templates or I/O issues.

Satisfies REQ-FUN-03

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| catalog | `ProjectCatalog` |  |
| output_path | `str` |  |

