# Admin & Installation Guide

This guide is intended for system administrators and DevOps engineers who want to deploy and manage **Universal Document Engine (UDE)** in their CI/CD pipelines.

## 🛠️ Installation

UDE requires **Python 3.12+**. Install the package and its dependencies using:

```bash
pip install universal-document-engine
```

## 🌐 CI/CD Integration

To integrate UDE into your GitHub Actions workflow, add the following step:

```yaml
- name: Run Universal Document Engine
  run: |
    python -m ude.cli --input ./xml/ --output ./docs/api/
```

---

*Detailed orchestration guides for Docusaurus, VitePress, and Hugo integration will be added here.*
