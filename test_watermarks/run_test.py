#!/usr/bin/env python3
"""
CIAF Watermarks Test Runner

Convenient script to run all watermarks tests with various options.
Automatically cleans pytest cache to avoid module import conflicts.

Usage:
    python run_test.py                      # Run all watermarks tests
    python run_test.py --module text        # Run specific module tests
    python run_test.py --coverage           # Run with coverage report
    python run_test.py --verbose            # Verbose output
    python run_test.py --failfast           # Stop on first failure
    python run_test.py --module images -v   # Run image tests with verbose output
    python run_test.py --no-clean           # Skip cache cleanup (not recommended)

Created: 2026-04-05
Version: 1.0.0
"""

import sys
import subprocess
import argparse
import shutil
from pathlib import Path


def clean_cache(directory=None):
    """Remove all __pycache__ directories and .pyc files to avoid import conflicts."""
    if directory is None:
        directory = Path(__file__).parent
    else:
        directory = Path(directory)

    total_cleaned = 0

    # Clean current directory and all subdirectories
    directories_to_clean = [directory]

    # Also clean parent test directory to catch any cached imports there
    parent_tests = directory.parent
    if parent_tests.exists():
        directories_to_clean.append(parent_tests)

    for dir_to_clean in directories_to_clean:
        # Remove __pycache__ directories
        pycache_dirs = list(dir_to_clean.rglob("__pycache__"))
        for pycache in pycache_dirs:
            if pycache.is_dir():
                try:
                    shutil.rmtree(pycache)
                    total_cleaned += 1
                except Exception as e:
                    print(f"⚠️  Could not remove {pycache}: {e}")

        # Remove .pyc files
        pyc_files = list(dir_to_clean.rglob("*.pyc"))
        for pyc_file in pyc_files:
            try:
                pyc_file.unlink()
                total_cleaned += 1
            except Exception as e:
                print(f"⚠️  Could not remove {pyc_file}: {e}")

        # Remove .pytest_cache in this directory
        pytest_cache = dir_to_clean / ".pytest_cache"
        if pytest_cache.exists():
            try:
                shutil.rmtree(pytest_cache)
                total_cleaned += 1
            except Exception as e:
                print(f"[!] Could not remove {pytest_cache}: {e}")

    if total_cleaned > 0:
        print(f"[*] Cleaned {total_cleaned} cache items\n")
    else:
        print("[*] Cache already clean\n")


def run_command(cmd):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)
    # Run from the test_watermarks directory
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run CIAF Watermarks tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_test.py                    # Run all watermarks tests (auto-clean cache)
  python run_test.py --module text      # Run text watermarking tests only
  python run_test.py --module images -v # Run image tests with verbose output
  python run_test.py --coverage         # Run with coverage report
  python run_test.py --failfast         # Stop on first failure
  python run_test.py --no-clean         # Skip cache cleanup (not recommended)
        """,
    )

    parser.add_argument(
        "--module",
        choices=[
            "text",
            "images",
            "audio",
            "video",
            "pdf",
            "binary",
            "gpu",
            "models",
            "all",
        ],
        default="all",
        help="Test module to run (default: all)",
    )

    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    parser.add_argument(
        "--failfast",
        "-x",
        action="store_true",
        help="Stop on first failure",
    )

    parser.add_argument(
        "--markers",
        "-m",
        type=str,
        help="Run tests matching given mark expression (e.g., 'not slow')",
    )

    parser.add_argument(
        "--keyword",
        "-k",
        type=str,
        help="Run tests matching given keyword expression",
    )

    parser.add_argument(
        "--last-failed",
        "--lf",
        action="store_true",
        help="Rerun only tests that failed last time",
    )

    parser.add_argument(
        "--pdb",
        action="store_true",
        help="Drop into debugger on failures",
    )

    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip automatic cache cleanup (not recommended)",
    )

    args = parser.parse_args()

    # Clean cache by default to avoid pytest import conflicts
    # (multiple test files with same name in different subdirs)
    if not args.no_clean:
        print("=" * 80)
        print("[*] Cleaning pytest cache to avoid import conflicts...")
        print("=" * 80)
        clean_cache()

    # Build pytest command
    cmd = ["pytest"]

    # Always clear pytest cache to avoid import conflicts
    cmd.append("--cache-clear")

    # Use importlib mode to handle duplicate test file names in different dirs
    cmd.append("--import-mode=importlib")

    # Select test files based on module
    if args.module == "all":
        # Run all tests in test_watermarks folder
        cmd.append(".")
    elif args.module == "text":
        cmd.append("test_text/")
    elif args.module == "images":
        cmd.append("test_images/")
    elif args.module == "audio":
        cmd.append("test_audio/")
    elif args.module == "video":
        cmd.append("test_video/")
    elif args.module == "pdf":
        cmd.append("test_pdf/")
    elif args.module == "binary":
        cmd.append("test_binary/")
    elif args.module == "gpu":
        cmd.append("test_gpu/")
    elif args.module == "models":
        cmd.append("test_models.py")

    # Add options
    if args.verbose:
        cmd.append("-v")

    if args.failfast:
        cmd.append("-x")

    if args.markers:
        cmd.extend(["-m", args.markers])

    if args.keyword:
        cmd.extend(["-k", args.keyword])

    if args.last_failed:
        cmd.append("--lf")

    if args.pdb:
        cmd.append("--pdb")

    if args.coverage:
        cmd.extend(
            [
                "--cov=ciaf.watermarks",
                "--cov-report=html:htmlcov_watermarks",
                "--cov-report=term",
            ]
        )

    # Run tests
    return_code = run_command(cmd)

    if return_code == 0:
        print("\n" + "=" * 80)
        print("[+] [SUCCESS] All watermarks tests passed!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("\n[-] [FAILURE] Some watermarks tests failed!")
        print("=" * 80)

    if args.coverage:
        print("\n[*] [REPORT] Coverage report generated: htmlcov_watermarks/index.html")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
