"""Command-line interface."""

import sys
import argparse
from .core import LinmonCore


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="linmon - Lightweight Linux monitoring tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Run monitoring check")
    check_parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration file",
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report to stdout",
    )
    
    # Legacy: support `linmon --config` without subcommand
    parser.add_argument(
        "--config",
        help="Path to configuration file (legacy format)",
    )
    
    args = parser.parse_args()
    
    # Handle legacy format: `linmon --config <path>`
    if args.config and not args.command:
        config_path = args.config
    elif args.command == "check" and args.config:
        config_path = args.config
    else:
        parser.print_help()
        sys.exit(1)
    
    try:
        core = LinmonCore(config_path)
        exit_code, text_report, json_report = core.run()
        
        if args.json:
            print(json_report)
        else:
            print(text_report)
        
        sys.exit(exit_code)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
