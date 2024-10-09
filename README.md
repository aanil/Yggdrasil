# Yggdrasil :deciduous_tree:

Yggdrasil is a data processing framework designed to manage and automate workflows for various genomic sequencing projects (currently including TenX and SmartSeq3 modules). It provides a unified interface to handle data ingestion, processing, result generation, and ultimately project packing and delivery, streamlining the analysis pipeline for sequencing data.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development Guidelines](#development-guidelines)
  - [Setting Up the Development Environment](#setting-up-the-development-environment)
  - [Pre-Commit Hooks](#pre-commit-hooks)
  - [Code Formatting, Linting and Type Checking](#code-formatting-linting-and-type-checking)
  - [VSCode Integration](#vscode-integration)
  - [Git Blame Configuration](#git-blame-configuration)
  - [Continuous Integration](#continuous-integration)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Python 3.11** or higher
- [Conda](https://docs.conda.io/en/latest/) for environment management
- [Git](https://git-scm.com/) for version control
- [VSCode](https://code.visualstudio.com/) (recommended) for development

## Installation

To get started with the Yggdrasil Project, you need to set up the necessary dependencies. Follow the instructions below:

1. **Clone the Repository**:

```bash
git clone https://github.com/NationalGenomicsInfrastructure/Yggdrasil.git
cd Yggdrasil
```

2. **Create and Activate a Conda Environment**:

It is recommended to use a conda environment to manage dependencies. You can set up the environment using `conda`:

```bash
conda create --name yggdrasil-env python=3.11
conda activate yggdrasil-env
```

3. **Install Required Packages**:

```bash
pip install -r requirements.txt
```

## Project Structure

Brief overview of the main components and directories:

```text
Yggdrasil/
├── lib/
│   ├── base/
│   ├── core_utils/
│   ├── couchdb/
│   ├── module_utils/
│   ├── realms/
│   │   ├── tenx/
│   │   └── smartseq3/
├── tests/
├── .github/
│   └── workflows/
├── ygg_trunk.py
├── ygg-mule.py
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

*	**lib/**: Core library containing base classes and utilities.
    *	**base/**: Abstract base classes and interfaces.
    *   **core_utils/**: Utility modules for the Yggdrasil core functionalities.
    *   **couchdb/**: Classes specific for Yggdrasil - CouchDB interactions.
    *	**module_utils/**: Utility modules for various Yggdrasil module functionalities.
    *	**realms/**: Modules specific to different sequencing technologies (e.g. TenX, SmartSeq3, etc.)
*	**tests/**: Test cases for the application.
*	**.github/workflows/**: GitHub Actions workflows for CI/CD.

## Usage

### Ygg-Mule

To run Yggdrasil manually, use the manual core script `ygg-mule.py`. It is used for processing documents manually by providing a CouchDB document ID.

**Usage**:

```bash
python ygg-mule.py <doc_id>
```

Replace <doc_id> with the actual CouchDB document ID you wish to process.

## Configuration

Yggdrasil uses a configuration loader to manage settings. Configuration files should be placed in the `yggdrasil_workspace/common/configurations` directory. This directory path can be adjusted in the `lib/core_utils/common.py` script if needed.

### Configuration Files

**config.json**: This file contains global settings for Yggdrasil.

Fields:

    - yggdrasil_log_dir: Directory where logs will be stored.
    - couchdb_url: URL of the CouchDB server. Example: "http://localhost:5984"
    - couchdb_database: Name of the CouchDB project database.
    - couchdb_status_tracking: Name of the CouchDB yggdrasil database for project status tracking.
    - couchdb_poll_interval: Interval (in seconds) for polling CouchDB for changes.
    - job_monitor_poll_interval: Interval (in seconds) for polling the job monitor.
    - activate_ngi_cmd: Command to activate NGI environment

Example Configuration File (config.json)

```json
{
    "yggdrasil_log_dir": "yggdrasil_workspace/logs",
    "couchdb_url": "http://localhost:5984",
    "couchdb_database": "my_project_db",
    "couchdb_status_tracking": "my_ygg_status_db",
    "couchdb_poll_interval": 3,
    "job_monitor_poll_interval": 60,
    "activate_ngi_cmd": "source sourceme_sthlm.sh && source activate NGI"
}
```

**module_registry.json**: This file maps different library construction methods to their respective processing modules. The modules specified here will be dynamically loaded and executed based on the entire name of a `library_prep_method` specified in the CouchDB document, or a designated prefix of them.

This file maps different library construction methods to their respective processing modules. The modules specified here will be dynamically loaded and executed based on the library construction method specified in the CouchDB document.

Example:

```json
{
    "SmartSeq 3": {
        "module": "lib.realms.smartseq3.smartseq3.SmartSeq3"
    },
    "10X": {
        "module": "lib.realms.tenx.tenx_project.TenXProject",
        "prefix": true
    }
}
```

- **SmartSeq 3**:
    - module: The path to the module handling SmartSeq 3 library data.
- **10X**:
    - module: The path to the module handling 10X-prefixed library data.

### Environment Variables

Ensure the following environment variables are set:

    - COUCH_USER: Your CouchDB username.
    - COUCH_PASS: Your CouchDB password.

### Logging

Yggdrasil uses a custom logging utility to manage logs. Logs are stored in the directory specified by the yggdrasil_log_dir configuration.

**Enabling Debug Logging**: To enable debug logging, modify the `configure_logging` call in your script:

```python
from lib.utils.logging_utils import configure_logging
configure_logging(debug=True)
```

## Development Guidelines

### Setting Up the Development Environment

Ensure you have activated the Conda environment and installed all required packages as per the [Installation](#installation) section.

### Pre-Commit Hooks

Use [pre-commit](https://pre-commit.com/) to automate code formatting and linting on each commit.

* **Install pre-commit hooks**:

```bash
pre-commit install
```

* **Run pre-commit hooks manually**:

```bash
pre-commit run --all-files
```

### Code Formatting, Linting and Type Checking

Use `black` for code formatting, `ruff` for linting and `mypy` for static type checking. It is recommended to have these tools set as extensions on your editor (e.g. [VSCode](#vscode-integration)) too, for a more seamless, automated experience. But if you preffer running them manually in cmd:

* **Format code with Black**:

```bash
black .
```

* **Lint code with Ruff**:

```bash
ruff check .
```

* **Run type checks**:

```bash
mypy .
```

### VSCode Integration

For an optimal development experience, we recommend using VSCode with the following extensions:

* Python (by Microsoft)
* Ruff (by Astral Software)
* Black Formatter (by Microsoft)
* Mypy Type Checker (by Microsoft)

**VSCode Settings**

Make sure your (user)`settings.json` contains the following settings to integrate the tools:

```json
{
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "ruff.lint.args": [ "--config=pyproject.toml" ],
    "mypy-type-checker.args": [ "--config-file=pyproject.toml" ]
}
```

### Git Blame Configuration

To ensure git blame ignores bulk formatting commits.

* **Configure Git**:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

* **Add Formatting Commits to `.git-blame-ignore-revs`**:

Add the commit (full) hashes of your formatting commits to the `.git-blame-ignore-revs` file, one per line, e.g.:

```text
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0
```

### Continuous Integration

GitHub Actions are set up to automatically run `ruff`, `black`, and `mypy` on pushes and pull requests.

* Workflow File: .github/workflows/lint.yml
* Separate Jobs: Each tool runs in its own job for clear feedback.

## Contributing

Contributions are very welcome! To have as smooth of an experience as possible, the following guidelines are recommended:

* **Branching**: Use feature branches and submit pull requests for review.
* **Code Style**: Format with `black` and lint with `ruff`.
* **Type Annotations**: If you use type annotations make sure to set (and pass) mypy checks.
* **Documentation**: Documented contributions are easier to understand and review.

Suggested contributions: Tests, Bug Fixes, Code Optimization, New Modules (reach out to Anastasios if you don't know where to start with developing a new module).

## License

Yggdrasil is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.