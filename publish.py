#!/usr/bin/env python3
"""
Publishing script for django-delete-all package.

Usage:
    python publish.py --test    # Upload to TestPyPI
    python publish.py --prod    # Upload to PyPI
    python publish.py --check   # Just check the build
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and handle errors."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def check_requirements():
    """Check if required tools are installed."""
    required_tools = ['twine', 'build']
    missing = []

    for tool in required_tools:
        if not run_command(f"which {tool}", check=False):
            missing.append(tool)

    if missing:
        print(f"Missing required tools: {', '.join(missing)}")
        print("Install with: pip install build twine")
        return False

    return True


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous builds...")
    for path in ["dist", "build", "*.egg-info"]:
        run_command(f"rm -rf {path}", check=False)


def build_package():
    """Build the package."""
    print("Building package...")
    return run_command("python -m build")


def check_package():
    """Check the built package."""
    print("Checking package...")
    return run_command("twine check dist/*")


def upload_to_testpypi():
    """Upload to TestPyPI."""
    print("Uploading to TestPyPI...")
    return run_command("twine upload --repository testpypi dist/*")


def upload_to_pypi():
    """Upload to PyPI."""
    print("Uploading to PyPI...")
    return run_command("twine upload dist/*")


def main():
    parser = argparse.ArgumentParser(description="Publish django-delete-all package")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI")
    parser.add_argument("--prod", action="store_true", help="Upload to PyPI")
    parser.add_argument("--check", action="store_true", help="Just check the build")

    args = parser.parse_args()

    if not any([args.test, args.prod, args.check]):
        parser.print_help()
        return 1

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("Error: pyproject.toml not found. Run from package root.")
        return 1

    # Check requirements
    if not check_requirements():
        return 1

    # Clean and build
    clean_build()
    if not build_package():
        print("Build failed!")
        return 1

    # Check package
    if not check_package():
        print("Package check failed!")
        return 1

    if args.check:
        print("✅ Package build and check successful!")
        return 0

    # Upload
    if args.test:
        if upload_to_testpypi():
            print("✅ Successfully uploaded to TestPyPI!")
            print("Install with: pip install -i https://test.pypi.org/simple/ django-delete-all")
        else:
            print("❌ Upload to TestPyPI failed!")
            return 1

    elif args.prod:
        confirm = input("Are you sure you want to upload to PyPI? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Upload cancelled.")
            return 0

        if upload_to_pypi():
            print("✅ Successfully uploaded to PyPI!")
            print("Install with: pip install django-delete-all")
        else:
            print("❌ Upload to PyPI failed!")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())