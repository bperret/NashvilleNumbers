#!/usr/bin/env python3
"""
Vercel Configuration Validator

This script validates vercel.json to ensure there are no configuration conflicts.

According to Vercel's documentation:
- If `rewrites`, `redirects`, `headers`, `cleanUrls` or `trailingSlash` are used,
  then `routes` (legacy property) cannot be present.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def validate_vercel_config(config_path: Path = Path("vercel.json")) -> tuple[bool, List[str]]:
    """
    Validate Vercel configuration for conflicts.

    Args:
        config_path: Path to vercel.json file

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check if file exists
    if not config_path.exists():
        return True, []  # No config file means no validation needed

    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {config_path}: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Error reading {config_path}: {e}")
        return False, errors

    # Check for routes + modern properties conflict
    modern_properties = ['rewrites', 'redirects', 'headers', 'cleanUrls', 'trailingSlash']
    has_routes = 'routes' in config
    has_modern = [prop for prop in modern_properties if prop in config]

    if has_routes and has_modern:
        errors.append(
            f"Configuration conflict in {config_path}:\n"
            f"  - The legacy 'routes' property cannot be used with: {', '.join(has_modern)}\n"
            f"  - Solution: Replace 'routes' with 'rewrites' for routing rules\n"
            f"  - See: https://vercel.com/docs/projects/project-configuration#legacy-routes"
        )
        return False, errors

    # Warn if using legacy routes
    if has_routes and not has_modern:
        print(f"⚠️  Warning: {config_path} uses legacy 'routes' property.", file=sys.stderr)
        print(f"   Consider migrating to 'rewrites' for better compatibility.", file=sys.stderr)

    return True, errors


def main():
    """Main entry point for the validation script."""
    config_path = Path("vercel.json")

    print(f"🔍 Validating {config_path}...")

    is_valid, errors = validate_vercel_config(config_path)

    if is_valid:
        print(f"✅ Configuration is valid!")
        return 0
    else:
        print(f"❌ Configuration validation failed:\n")
        for error in errors:
            print(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
