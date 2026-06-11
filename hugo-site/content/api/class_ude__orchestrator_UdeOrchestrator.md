---
title: "UdeOrchestrator"
sidebar_position: 22
parent: "ude::orchestrator"
---

# UdeOrchestrator

Orchestrates the entire multi-target document generation pipeline.

Loads global and local settings, resolves portable paths, coordinates
collectors, parsers, and renderers, and enforces error-handling policies.

Satisfies REQ-FUN-23, REQ-FUN-24, REQ-FUN-25, REQ-FUN-28, REQ-FUN-29

## Fields

- `ude.orchestrator.UdeOrchestrator::global_config_path`
- `ude.orchestrator.UdeOrchestrator::global_config`

## Methods

### __init__
`None ude.orchestrator.UdeOrchestrator.__init__(self, Optional[Union[str, Path]] global_config_path=None)`

Initializes the orchestrator.

Args:
    global_config_path: Optional path to the global configuration. If not
        specified, the orchestrator will resolve it dynamically from the target directories.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| global_config_path | `Optional]` |  |

### run_target
`bool ude.orchestrator.UdeOrchestrator.run_target(self, Union[str, Path] config_path)`

Runs the pipeline for a single target configuration.

Args:
    config_path: Path to the local target configuration file.

Returns:
    True on success, False on failure.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| config_path | `Union` |  |

### run
`bool ude.orchestrator.UdeOrchestrator.run(self, List[Union[str, Path]] config_paths)`

Runs the pipeline sequentially for multiple target configurations.

Enforces the error_policy:
- 'fail-fast' halts on the first error.
- 'continue-on-error' logs errors, skips the failed target, compiles the remainder,
  and returns False if any failures occurred.

Args:
    config_paths: A list of target configuration paths.

Returns:
    True if all targets succeeded, False if any failed.

| Parameter | Type | Description |
| --- | --- | --- |
|  | `self` |  |
| config_paths | `List]` |  |

