"""GroupAlarm TUI — CLI entry point.

Usage::

    python groupalarm_cli.py [--org-id ORG_ID] [--dry-run] [--verbose]
"""

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive TUI for managing GroupAlarm appointments",
    )
    parser.add_argument("--org-id", type=int, default=None, help="Override organization ID for this session")
    parser.add_argument("--dry-run", action="store_true", help="Prevent all server mutations, log payloads")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG-level logging")
    args = parser.parse_args()

    api_key = os.environ.get("GROUPALARM_API_KEY")
    if not api_key:
        print("ERROR: GROUPALARM_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    from framework import configure_logging
    from framework.config import load_config

    log_level = "DEBUG" if args.verbose else "INFO"
    configure_logging(level=log_level, logfile="groupalarm_cli.log")

    # Install API-key sanitizer
    from framework.log_sanitizer import install_api_key_sanitizer
    install_api_key_sanitizer(api_key)

    config = load_config()
    org_id = args.org_id or config.organization_id

    from framework.client import GroupAlarmClient
    client = GroupAlarmClient(token=api_key, dry_run=args.dry_run)

    from cli.app import GroupAlarmApp
    app = GroupAlarmApp(client=client, config=config, org_id=org_id, dry_run=args.dry_run)
    app.run()


if __name__ == "__main__":
    main()
