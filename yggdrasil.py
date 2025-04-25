import argparse
import asyncio
import logging

from lib.core_utils.config_loader import ConfigLoader
from lib.core_utils.ygg_session import YggSession
from lib.core_utils.yggdrasil_core import YggdrasilCore


def main():
    parser = argparse.ArgumentParser(prog="ygg")
    # Global flags
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Enable development mode (sets debug logging, dev-mode behavior)",
    )

    sub = parser.add_subparsers(dest="mode", required=True)

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

    # 1) Initialize dev mode early (affects config loader, logging, etc.)
    YggSession.init_dev_mode(args.dev)

    # 2) Adjust root logger
    logging.basicConfig(level=logging.DEBUG if args.dev else logging.INFO)

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
            asyncio.run(core.stop())

    elif args.mode == "run-doc":
        # One‑off run
        # Initialize manual-submit policy for this invocation
        YggSession.init_manual_submit(args.manual_submit)

        # Run once and exit
        core.run_once(doc_id=args.doc_id)


if __name__ == "__main__":
    main()


# import asyncio
# import logging

# from lib.core_utils.config_loader import ConfigLoader
# from lib.core_utils.yggdrasil_core import YggdrasilCore


# def main():
#     # Possibly load config
#     config = ConfigLoader().load_config("config.json")

#     # Create YggdrasilCore
#     core = YggdrasilCore(config, logger=logging.getLogger("YggdrasilCore"))

#     # Setup watchers & handlers
#     core.setup_watchers()
#     # core.setup_handlers()

#     # Start all watchers
#     try:
#         asyncio.run(core.start())
#     except KeyboardInterrupt:
#         print("Interrupted! Stopping YggdrasilCore...")
#         asyncio.run(core.stop())


# if __name__ == "__main__":
#     main()
