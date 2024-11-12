import subprocess
from pathlib import Path
from typing import Optional

from lib.core_utils.config_loader import configs
from lib.core_utils.logging_utils import custom_logger

logging = custom_logger(__name__.split(".")[-1])


def transfer_report(
    report_path: Path, project_id: str, sample_id: Optional[str] = None
) -> bool:
    try:
        report_transfer_config = configs["report_transfer"]
        server = report_transfer_config["server"]
        user = report_transfer_config["user"]
        destination_path = report_transfer_config["destination"]
        ssh_key = report_transfer_config.get("ssh_key")
    except KeyError as e:
        missing_key = e.args[0]
        logging.error(f"Missing configuration for report transfer: '{missing_key}'")
        logging.warning("Report transfer will not be attempted. Handle manually...")
        return False

    if sample_id:
        remote_path = f"{user}@{server}:{destination_path}/{project_id}/{sample_id}/"
    else:
        remote_path = f"{user}@{server}:{destination_path}/{project_id}/"

    rsync_command = [
        "rsync",
        "-avz",
        "-e",
        f"ssh -i {ssh_key}" if ssh_key else "ssh",
        str(report_path),
        remote_path,
    ]

    try:
        # Execute the rsync command
        result = subprocess.run(
            rsync_command,
            check=True,
            text=True,
            capture_output=True,
        )

        logging.info(f"Report transferred successfully to {remote_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to transfer report:\n{e.stderr.strip()}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during report transfer: {e}")
        logging.error(f"RSYNC output: {result.stdout}")
        return False
