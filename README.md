# Yggdrasil

Welcome to the Yggdrasil Project repository. This repository hosts a middleware platform designed to aggregate sample-related metadata, manage the execution of various pipelines for single-cell data processing, and ultimately handle the delivery of analyzed data. It is designed to handle data processing tasks efficiently using CouchDB and various modules. Initially, it contains the core components, with plans to add more functionalities as development progresses.


## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

To get started with the Yggdrasil Project, you need to set up the necessary dependencies. Follow the instructions below:

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/NationalGenomicsInfrastructure/yggdrasil.git
    cd yggdrasil
    ```

2. **Install Dependencies**:

    It's recommended to use a conda environment to manage dependencies. You can set up the environment using `conda`:

    ```bash
    conda create --name yggdrasil-env python=3.11
    conda activate yggdrasil-env
    pip install -r requirements.txt
    ```

## Usage

### Ygg-Mule

To run Yggdrasil manually, use the manual core script `ygg-mule.py`. It is used for processing documents manually by providing a CouchDB document ID.

#### Usage

```bash
python ygg-mule.py <doc_id>
```

Replace <doc_id> with the actual CouchDB document ID you wish to process.

## Configuration

The project uses a configuration loader to manage settings.
The configuration files should be placed in the `yggdrasil_workspace/common/configurations` directory.
Currently, this can be adjusted in the `common.py` script, but this is likely to change in the future.

- **config.json** fields:
    - yggdrasil_log_dir: Directory where logs will be stored.
    - couchdb_url: URL of the CouchDB server. Example: "http://localhost:5984"
    - couchdb_database: Name of the CouchDB database.
    - couchdb_poll_interval: Interval (in seconds) for polling CouchDB for changes.
    - job_monitor_poll_interval: Interval (in seconds) for polling the job monitor.

Example Configuration File (config.json)

```json
{
    "yggdrasil_log_dir": "yggdrasil_workspace/logs",
    "couchdb_url": "http://localhost:5984",
    "couchdb_database": "my_database",
    "couchdb_poll_interval": 3,
    "job_monitor_poll_interval": 60
}
```

- **module_registry.json**:

This file maps different library construction methods to their respective processing modules. The modules specified here will be dynamically loaded and executed based on the library construction method specified in the CouchDB document.

Example:

```json
{
    "SmartSeq 3": {
        "module": "lib.realms.smartseq3.smartseq3.SmartSeq3"
    },
    "10X Chromium": {
        "module": "lib.realms.tenx.tenx.TenX"
    }
}
```

In this example the assumed modules registered are:
- SmartSeq 3:
    - module: The path to the module handling SmartSeq 3 data.
- 10X Chromium:
    - module: The path to the module handling 10X Chromium data.

## Environment Variables

Ensure the following environment variables are set:

    - COUCH_USER: Your CouchDB username.
    - COUCH_PASS: Your CouchDB password.

## Logging

The project uses a custom logging utility to manage logs. Logs are stored in the directory specified by the yggdrasil_log_dir configuration.

Enabling Debug Logging
To enable debug logging, modify the configure_logging call in your script:

```python
from lib.utils.logging_utils import configure_logging
configure_logging(debug=True)
```
