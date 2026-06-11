---
title: "CommentNormalizer"
sidebar_position: 17
parent: "ude::normalizer"
---

# CommentNormalizer

Normalizes legacy and modern code comments/docstrings to CommonMark.

Extracts parameter, return, author, and version tags as metadata,
and returns a clean, compliant Markdown body.

Satisfies REQ-FUN-14

## Fields

- `ude.normalizer.CommentNormalizer::_param_re`
- `ude.normalizer.CommentNormalizer::_return_re`
- `ude.normalizer.CommentNormalizer::_author_re`
- `ude.normalizer.CommentNormalizer::_version_re`
- `ude.normalizer.CommentNormalizer::_brief_re`
- `ude.normalizer.CommentNormalizer::_google_param_line_re`

## Methods

### __init__
`None ude.normalizer.CommentNormalizer.__init__(self)`

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |

### normalize_comment
`Tuple[str, Dict[str, Any]] ude.normalizer.CommentNormalizer.normalize_comment(self, Optional[str] raw_comment)`

Cleans and standardizes raw docstring/comment blocks to CommonMark.

Args:
    raw_comment: The raw string of the docstring/comment block from source code.

Returns:
    A tuple containing:
        - The cleaned docstring body (CommonMark Markdown string).
        - A dictionary containing extracted metadata:
            {
                "params": Dict[str, str],   # parameter_name -&gt; description
                "returns": Optional[str],   # return description
                "author": Optional[str],    # author description
                "version": Optional[str],   # version description
            }

Satisfies REQ-FUN-14

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| raw_comment | `Optional` |  |

### _strip_decorations
`list[str] ude.normalizer.CommentNormalizer._strip_decorations(self, str text)`

Strips Javadoc block comment formatting and Doxygen comment markers.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| text | `str` |  |

### _standardize_markdown
`str ude.normalizer.CommentNormalizer._standardize_markdown(self, list[str] lines)`

Post-processes docstring lines to create a clean, uniform CommonMark block.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| lines | `list` |  |

