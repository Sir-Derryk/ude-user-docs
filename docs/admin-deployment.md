# Admin & Automated CI/CD Deployment

This operator guide details how system administrators and DevOps engineers deploy the Universal Document Engine (UDE) inside secure, automated high-performance enterprise CI/CD environments.

---

## 🛠️ Admin Installation Specs

UDE is distributed as an enterprise-grade Python package. It can be installed in production runners using any of the following standard methods:

### Method 1: Python Pip
```bash
pip install universal-document-engine
```

### Method 2: Pipenv Environment
```bash
pipenv install universal-document-engine
```

### Method 3: Poetry Dependency Manager
```bash
poetry add universal-document-engine --group dev
```

---

## 🤖 Continuous Integration Workflow

The automated compilation and publication pipeline is managed via GitHub Actions inside `.github/workflows/deploy.yml`. Let's break down each step of the pipeline:

### Step 1: Submodule Checkouts & Authorization
```yaml
- name: Checkout Code and Submodules
  uses: actions/checkout@v4
  with:
    token: ${{ secrets.PIPELINE_GITHUB_TOKEN }}
    submodules: 'recursive'
```
*Uses secure Git credentials to recursively check out our linked private submodules (`engine`, `design-docs`, `user-docs`) to build the complete, multi-layered portal.*

### Step 2: Runner Environment Setup
```yaml
- name: Install System Dependencies
  run: |
    sudo apt-get update
    sudo apt-get install -y doxygen
```
*Installs the Doxygen preprocessor directly onto the standard Ubuntu runner host machine.*

### Step 3: Python & Node.js Cache Strategies
To guarantee rapid builds (completing in **under 30 seconds**), we cache local packages and dependencies:
```yaml
- name: Setup Node Cache
  uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

### Step 4: Multi-Engine Compilations
Once the environment is validated, the runner executes the compilation sequence:
```bash
# 1. Build VitePress manual guides
npm run docs:build

# 2. Compile UDE API Reference via Python orchestrator
python -m ude.cli --config ./user-docs/ude_config_self.json
```

---

## 🌐 GitHub Pages Deployment

After the build stages complete successfully, the runner uploads the combined compiled directory `.vitepress/dist/` directly to GitHub Pages:

```yaml
- name: Deploy to GitHub Pages
  uses: actions/deploy-pages@v4
```

This updates the live developer portal instantly at the public address with zero downtime.

---

## 📂 Multi-Tenant Hosting & SSO Options

For secure enterprise projects, public hosting via standard GitHub Pages might not be suitable. Administrators can configure custom deployment environments:

*   **Cloudflare Zero Trust**: Wrap the compiled static site behind OIDC/OAuth single sign-on (SSO) gateways to restrict access to authorized engineering teams.
*   **Nginx Private Server**: Deploy the static assets folder into a private, internal Nginx server residing within your corporate VPN.
*   **Docker Container**: Package `.vitepress/dist/` into a lightweight alpine-based Nginx container for simple deployments across Kubernetes clusters.
