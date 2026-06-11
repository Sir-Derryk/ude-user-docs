---
title: "BaseCollector"
sidebar_position: 1
parent: "ude::interfaces"
---

# BaseCollector

Abstract base class establishing the contract for all documentation pre-processing collectors.

Collectors trigger code extraction tools (such as Doxygen) to generate raw structure representations (e.g. XML)
and guarantee safe, robust environment verification and workspace cleanup.

Satisfies REQ-FUN-01, REQ-FUN-22

## Methods

### validate_environment
`None ude.interfaces.BaseCollector.validate_environment(self, Path config_path)`

Validates that all external dependencies, compilers, and paths are correct and available.

Args:
    config_path: Path to the target configurations (e.g., ude_config.json).

Raises:
    CollectorError: If any of the required tools or templates are missing.

Satisfies REQ-FUN-01

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| config_path | `Path` |  |

### collect
`Path ude.interfaces.BaseCollector.collect(self, Path config_path)`

Executes the Doxygen process or native metadata collector to extract structural information.

Args:
    config_path: Path to the configurations directory or file.

Returns:
    The Path to the directory containing raw generated XML elements.

Raises:
    CollectorError: If process execution fails.

Satisfies REQ-FUN-01

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| config_path | `Path` |  |

### cleanup
`None ude.interfaces.BaseCollector.cleanup(self, Path temp_path)`

Safely and recursively removes temporary workspace directories.

Args:
    temp_path: Path to the directory to clean up.

Raises:
    ValueError: If path is empty, is a system root, or lies outside safe boundaries.
    CollectorError: If cleanup fails.

Satisfies REQ-FUN-22

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| temp_path | `Path` |  |

