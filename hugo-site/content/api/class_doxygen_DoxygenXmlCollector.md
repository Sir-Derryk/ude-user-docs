---
title: "DoxygenXmlCollector"
sidebar_position: 18
parent: "doxygen"
---

# DoxygenXmlCollector

Collector implementation that invokes the external Doxygen process.

Generates customized XML documentation structures from source files
and handles environment verification and secure filesystem cleanup.

Satisfies REQ-FUN-01, REQ-FUN-22

## Methods

### validate_environment
`None doxygen.DoxygenXmlCollector.validate_environment(self, Path config_path)`

Validates that all external dependencies, compilers, and paths are correct.

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
`Path doxygen.DoxygenXmlCollector.collect(self, Path config_path)`

Executes the Doxygen process to extract structural information.

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
`None doxygen.DoxygenXmlCollector.cleanup(self, Path temp_path)`

Safely and recursively removes temporary workspace directories with strict boundaries.

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

