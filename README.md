# Yggdrasil :deciduous_tree:

[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/2fa79bea21b142d9a75d0951ec2803dd)](https://app.codacy.com/gh/glrs/Yggdrasil/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)

Yggdrasil is an in-house orchestration framework designed to automate well-defined workflows. It watches directories, CouchDB
changes, etc., then calls **realm modules** (external or internal packages) to do the heavy lifting. Example realms today:

* `tenx` (internal)         - 10x Genomics best practice analysis
* `smartseq3` (internal)    - Smart-seq3 best practice analysis
* `dataflow-dmx` (external) - [under developmennt] Demultiplexing pipeline for Illumina / Aviti / ONT
* *(more to come)*

External realms self-register through the entry-point group **`ygg.handler`**.

---

## Table of Contents

- [Installation](#installation)
- [Install External Realms](#install-an-external-realm-(example:-dataflow-dmx))
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


## Installation

### 1. Developers / Contributors

```bash
# Clone & create an isolated env
git clone https://github.com/NationalGenomicsInfrastructure/Yggdrasil.git
cd Yggdrasil
conda create -n ygg-dev python=3.11 pip
conda activate ygg-dev

# Editable install with dev extras (ruff, mypy, ...)
pip install -e .[dev]

# Run Yggdrasil
python yggdrasil.py
```

* Runtime dependencies come from `[project] dependencies` in `pyproject.toml`.
* Dev tooling is pulled from `[project.optional-dependencies] dev`.

### 2. Production / CI runners

```bash
# 1. Clone & create an isolated env
git clone https://github.com/NationalGenomicsInfrastructure/Yggdrasil.git
cd Yggdrasil
conda create -n ygg python=3.11 pip
conda activate ygg

# 2. Install locked runtime stack
pip install -r requirements/lock.txt

# 3. Install Yggdrasil itself (no dev extras)
pip install -e .
```

`requirements/lock.txt` is generated from the dependency list with `pip-compile --strip-extras`


## Install an external realm (example: dataflow-dmx)
```bash
# Clone next to Yggdrasil or organize in a `realms` dir (any folder works)
git clone https://github.com/NationalGenomicsInfrastructure/dmx.git
pip install -e ./dmx
```

Restart Yggdrasil so it re-scans entry-points. Startup log shows the handler is active:
```
✓  registered external handler flowcell-dmx for FLOWCELL_READY
```

When a new event is detected, Yggdrasil schedules the appropriate handler as an
async background task in its event loop.


## Project Structure

Brief overview of the main components and directories:

```text
Yggdrasil/
├── lib/
│   ├── base/
│   ├── core_utils/
│   ├── couchdb/
│   ├── handlers/
│   ├── module_utils/
│   ├── realms/
│   │   ├── tenx/
│   │   └── smartseq3/
│   └── watchers/
├── tests/
├── .github/
│   └── workflows/
├── requirements/
├── yggdrasil.py
├── ygg_trunk.py (depr)
├── ygg-mule.py (depr)
├── pyproject.toml
├── LICENSE
└── README.md
```

*	**lib/**: Core library containing base classes and utilities.
    *	**base/**: Abstract base classes and interfaces.
    *   **core_utils/**: Utility modules for Yggdrasil core functionalities.
    *   **couchdb/**: Classes specific for Yggdrasil-CouchDB interactions and document management.
    *   **handlers/**: Base classes and built-in event/data handlers for processing and workflow orchestration.
    *	**module_utils/**: Utility modules for various Yggdrasil module functionalities.
    *	**realms/**: Internal modules specific to different sequencing technologies (e.g. TenX, SmartSeq3, etc.)
    *   **watchers/**: File system and CouchDB watchers for monitoring and triggering events.
*	**tests/**: Test cases for the application.
*	**.github/workflows/**: GitHub Actions workflows for CI/CD.
*   **requirements/**: Dependency lock files and requirements management for reproducible environments.


---

## Usage

### Command-line interface

Yggdrasil has a single entry-point for both daemon operation (background watchers + handlers) and one-off project processing.
After you installed Yggdrasil in an environment, call it in the following way:

```bash
yggdrasil [--dev] {daemon | run-doc} [OPTIONS]
```

| Global flag | Description                                                                                                       |
| ----------- | ----------------------------------------------------------------------------------------------------------------- |
| `--dev`     | Turns on *development mode*: <br>• DEBUG-level logging<br>• Dev-mode configuration overrides (useful on a laptop) |

You can also run the CLI via `python -m yggdrasil` or `python -m yggdrasil.cli` if you prefer.


### 1. `daemon` mode
Starts the long-running service:
* instantiates all configured watchers (file-system, CouchDB, ...);
* auto-registers built-in and external handlers;
* processes events until you stop it with **Ctrl-C**.

```bash
# production-style run
yggdrasil daemon

# verbose local run
yggdrasil --dev daemon
```

Logs are written to the directory set in `yggdrasil_workspace/common/configurations/config.json` → `yggdrasil_log_dir`.

### 2. One-off mode run-doc
Processes **exactly one** CouchDB project document and then exits. Useful for manual re-processing or debugging.

```bash
yggdrasil run-doc DOC_ID [--manual-submit]
```

| Option            | Meaning                                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------------------------- |
| `--manual-submit` | Force **manual** HPC submission for this invocation (handlers check a session flag instead of auto‐calling `sbatch`). |

#### Example:
__Objective__: Rerun project N.Surname (CouchDB doc_id: a1b2c3d4e5f), but stop before Slurm submission because we need to manually edit the project's configurations.
```bash
# Initially run
yggdrasil run-doc a1b2c3d4e5f --manual-submit
```

After you run this, manually edit the project as needed and submit to Slurm. Copy the Slurm `job_id` to the respective field in the project's CouchDB doc, and re-run the same command:
```bash
yggdrasil run-doc a1b2c3d4e5f --manual-submit`
```

Yggdrasil will pick up the running Slurm job and wait for it until it finishes, to continue with post-processing.

### Invocation summary
| You want to…                              | Command                                      |
| ----------------------------------------- | -------------------------------------------- |
| Run Yggdrasil as a background service     | `yggdrasil daemon`                           |
| Same, but with dev logging & dev servers  | `yggdrasil --dev daemon`                     |
| (re)Process one document                  | `yggdrasil run-doc <DOC_ID>`                 |
| (re)Process with manual Slurm submission  | `yggdrasil run-doc <DOC_ID> --manual-submit` |
| Use module form instead of console-script | `python -m yggdrasil ...`                    |


---

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

**module_registry.json**: This file maps different library construction methods to their respective internal processing modules. The modules specified here will be dynamically loaded and executed based on the entire name of a `library_prep_method` specified in the CouchDB document, or a designated prefix of them.

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
    "ruff.configuration": "pyproject.toml",
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

* **Forking**: Fork the main repository to your personal GitHub account. Develop your changes and submit pull requests to the main repository for review.
* **Code Style**: Format with `black` and lint with `ruff`.
* **Type Annotations**: If you use type annotations make sure to set (and pass) `mypy` checks.
* **Documentation**: Documented contributions are easier to understand and review.

**Suggested contributions**: Tests, Bug Fixes, Code Optimization, New Modules (reach out to Anastasios if you don't know where to start with developing a new module).

## License

Yggdrasil is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.