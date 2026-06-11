---
title: "BuildCacheManager"
sidebar_position: 9
parent: "ude::storage"
---

# BuildCacheManager

Two-Level Incremental Build Cache Manager.

L1 Parsing Cache: skips processing unchanged XML source files by validating file metadata
(size/mtime) and content checksum.

L2 Rendering Cache: skips writing identical generated markdown/HTML targets to disk to avoid
triggering SSG livereload cascades.

## Fields

- `ude.storage.BuildCacheManager::product_dir`
- `ude.storage.BuildCacheManager::cache_path`
- `ude.storage.BuildCacheManager::_cache`

## Methods

### __init__
`None ude.storage.BuildCacheManager.__init__(self, Union[str, Path] product_dir)`

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| product_dir | `Union` |  |

### save
`None ude.storage.BuildCacheManager.save(self)`

Saves and compresses the current cache database state to disk.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |

### get_l1_entry
`Optional[ProjectCatalog] ude.storage.BuildCacheManager.get_l1_entry(self, Union[str, Path] xml_path)`

Returns cached ProjectCatalog if XML source file is unchanged, else None.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| xml_path | `Union` |  |

### set_l1_entry
`None ude.storage.BuildCacheManager.set_l1_entry(self, Union[str, Path] xml_path, ProjectCatalog catalog)`

Saves ProjectCatalog metadata into the Level 1 parsing cache database.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| xml_path | `Union` |  |
| catalog | `ProjectCatalog` |  |

### check_l2_hit
`bool ude.storage.BuildCacheManager.check_l2_hit(self, Union[str, Path] target_path, str entity_signature, str template_content)`

Returns True if Level 2 cache hits and target output file physically exists on disk.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| target_path | `Union` |  |
| entity_signature | `str` |  |
| template_content | `str` |  |

### set_l2_entry
`None ude.storage.BuildCacheManager.set_l2_entry(self, Union[str, Path] target_path, str entity_signature, str template_content)`

Records rendering target signatures inside Level 2 rendering cache database.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| target_path | `Union` |  |
| entity_signature | `str` |  |
| template_content | `str` |  |

### write_if_changed
`bool ude.storage.BuildCacheManager.write_if_changed(self, Union[str, Path] target_path, str content, str entity_signature, str template_content)`

Writes content to disk only if Level 2 rendering signatures differ, preventing redundant I/O.

Returns:
    True if write was executed, False if skipped.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| target_path | `Union` |  |
| content | `str` |  |
| entity_signature | `str` |  |
| template_content | `str` |  |

### _load_cache
`BuildCache ude.storage.BuildCacheManager._load_cache(self)`

Loads and decompresses the persistent cache database from disk.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |

