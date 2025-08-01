import argparse
import asyncio

from lib.core_utils.config_loader import ConfigLoader

# import logging
from lib.core_utils.logging_utils import configure_logging, custom_logger
from lib.core_utils.ygg_session import YggSession
from lib.core_utils.yggdrasil_core import YggdrasilCore
from yggdrasil.logo_utils import print_logo

try:
    from yggdrasil import __version__
except ImportError:
    __version__ = "unknown"

configure_logging(debug=True)
logging = custom_logger("Yggdrasil")


def main():
    parser = argparse.ArgumentParser(prog="yggdrasil")
    # Global flags
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable development mode (sets debug logging, dev-mode behavior)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information",
    )

    sub = parser.add_subparsers(dest="mode", required=False)

    # Daemon mode
    sub.add_parser("daemon", help="Start the long-running service")

    # One‑off mode
    run = sub.add_parser("run-doc", help="Run exactly one project-doc and exit")
    run.add_argument("doc_id", help="Project document ID to process")
    run.add_argument(
        "-m",
        "--manual-submit",
        action="store_true",
        help="Force manual HPC submission for this run-doc invocation",
    )

    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        print_logo(version=__version__)
        return

    # Handle case where no subcommand is provided (show help)
    if args.mode is None:
        parser.print_help()
        return

    # 1) Initialize dev mode early (affects config loader, logging, etc.)
    YggSession.init_dev_mode(args.dev)

    # 2) Adjust root logger
    # logging.basicConfig(
    #     level=logging.DEBUG if args.dev else logging.INFO,
    #     format="[%(name)s] %(message)s",
    #     handlers=[RichHandler(show_time=True, show_level=True, markup=True)],
    # )
    # os.environ["PREFECT_LOGGING_LEVEL"] = "DEBUG" if args.dev else "INFO"

    logging.debug("Yggdrasil: Starting up...")

    # 3) Prepare core (load config, init core, register handlers)
    config = ConfigLoader().load_config("config.json")
    core = YggdrasilCore(config)
    core.setup_handlers()

    if args.mode == "daemon":
        if getattr(args, "manual_submit", False):
            parser.error("The --manual-submit flag is only valid in run-doc mode.")

        # (future)Daemon: set up watchers and run forever
        core.setup_watchers()
        try:
            asyncio.run(core.start())
        except KeyboardInterrupt:
            logging.warning("[bold red blink] Shutting down Yggdrasil daemon... [/]")
            asyncio.run(core.stop())

    elif args.mode == "run-doc":
        # One‑off run
        # Initialize manual-submit policy for this invocation
        YggSession.init_manual_submit(args.manual_submit)

        # Run once and exit
        core.run_once(doc_id=args.doc_id)


if __name__ == "__main__":
    main()
