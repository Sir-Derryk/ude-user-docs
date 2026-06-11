# Target Configurations Reference

To compile documentation for your specific products, UDE utilizes a decentralized target configuration schema defined inside localized files named `ude_config.json`.

---

## 📋 Understanding target_config.json

Every code project or module (such as our sub-products BimNv, Map, FacetModeler, or IGES) maintains its own target configuration file. This allows developers to compile and test documentation locally without modifying system settings or global pipelines.

> [!IMPORTANT]
> **Path Portability Rule**:
> All file and folder paths defined within a `ude_config.json` file must be specified **relative** to the configuration file's physical directory. The orchestrator dynamically resolves these into system-agnostic absolute paths during execution. This complies with Functional Specification **[REQ-FUN-12: Configuration Portability Resolution](https://Sir-Derryk.github.io/ude-design-docs/docs/srs/functional#req-fun-12)**.

---

## ⚙️ Configuration Properties Breakdown

A standard `ude_config.json` file is split into three main object sectors:

```json
{
  "product": {
    "name": "BimNv API C++",
    "version": "1.0.0"
  },
  "collector": {
    "xml_dir": "./xml-out/",
    "doxygen_flags": ["-q"]
  },
  "parser": {
    "exclude_namespaces": ["std", "swig"],
    "filter_wrappers": true
  },
  "renderer": {
    "output_dir": "./docs/api/",
    "format": "hugo-markdown",
    "templates_dir": "./templates/"
  }
}
```

### 1. `product` Block
*   `name`: The display name of the software product.
*   `version`: Product release version (included in compiled layouts).

### 2. `collector` Block
*   `xml_dir`: Destination directory where Doxygen generates its raw XML outputs.
*   `doxygen_flags`: Custom command-line flags passed directly to Doxygen preprocessors.

### 3. `parser` Block
*   `exclude_namespaces`: Structural namespaces to entirely filter out during compilation.
*   `filter_wrappers`: Automatically prunes language helper classes (e.g. SWIG helpers).

### 4. `renderer` Block
*   `output_dir`: Physical path on disk where compiled static assets are written.
*   `format`: Compilation target (`hugo-markdown`, `standalone-html`, or `rag-json`).
*   `templates_dir`: Relative path pointing to custom Jinja2 layout templates.

---

## 🚀 Running the Orchestrator

Once you have written a local `ude_config.json` configuration file, compile your documentation using the UDE multi-target CLI executor:

```bash
python -m ude.cli --config ./ude_config.json
```

The orchestrator will automatically execute the pipeline:
1.  **Collect**: Verifies paths and executes Doxygen over code headers.
2.  **Parse**: Converts XML blocks into compressed `.json.gz` Intermediate Representation (IR).
3.  **Render**: Compiles the IR into high-aesthetic static website catalogs.
