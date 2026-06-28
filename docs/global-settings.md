# Global System Configurations

The Universal Document Engine uses a centralized configuration file named `ude_global.json` to control system-wide behaviors, establish security guard rails, and configure high-performance caching strategies.

---

## 📋 File Schema Overview

The `ude_global.json` file resides in the global system app data directory or the root directory of your enterprise runner. It establishes the global environment settings that apply to all target compilation pipelines.

A standard global configurations schema contains three primary blocks:
```json
{
  "logging": {
    "level": "INFO",
    "log_file": "./logs/ude.log"
  },
  "caching": {
    "enable_l1": true,
    "enable_l2": true,
    "cache_dir": "./.build_cache/"
  },
  "guards": {
    "safe_cleanup": true,
    "protected_dirs": ["/", "/home", "C:\\", "D:\\"]
  }
}
```

---

## ⚙️ Configuration Properties

### 1. Logging and Verbosity (`logging`)
Controls how UDE reports execution diagnostics and pipeline warnings.
*   `level`: Establishes the verbosity threshold (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
*   `log_file`: Path to write the diagnostic log stream (defaults to standard output if not specified).

### 2. Cache Databases (`caching`)
Enables extreme performance for incremental documentation builds:
*   `enable_l1`: Toggles the L1 Parser Cache, skipping compilation of unchanged Doxygen XML inputs.
*   `enable_l2`: Toggles the L2 Renderer Cache, avoiding writing files on disk if the Intermediate Representation (IR) signatures and templates remain unchanged.
*   `cache_dir`: Relative or absolute path where compiled `.build_cache.json.gz` files are persisted.

### 3. Directory Guard Rails (`guards`)
Protects your filesystem during automated cleanups of intermediate folders:
*   `safe_cleanup`: When true, restricts deletion commands to safe subdirectories.
*   `protected_dirs`: A strict list of critical directories that UDE will *never* delete or clean, preventing disastrous wildcard deletions.

> [!CAUTION]
> **Safety Guard Rails**:
> The safe directory validator will raise an immediate fatal exception if the compiler attempts to run cleanup routines over a protected system path, satisfying **[REQ-FUN-22: Safe Directories Cleanup Guard Rails](https://Sir-Derryk.github.io/ude-design-docs/docs/srs/functional#req-fun-22)**.

---

## 📂 Default Configuration File Example

Below is the standard, documented configuration template for `ude_global.json` recommended for production runner deployments:

```json
{
  "logging": {
    "level": "INFO",
    "log_file": "./logs/ude_orchestrator.log"
  },
  "caching": {
    "enable_l1": true,
    "enable_l2": true,
    "cache_dir": "./.ude_cache"
  },
  "guards": {
    "safe_cleanup": true,
    "protected_dirs": [
      "/",
      "/usr",
      "/var",
      "C:\\",
      "C:\\Windows",
      "D:\\"
    ]
  }
}
```
