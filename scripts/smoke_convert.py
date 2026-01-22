#!/usr/bin/env python3
"""
Smoke test for PDF conversion pipeline.

This script runs an end-to-end conversion test using a known fixture PDF,
validates the output, and logs structured JSONL output for CI/CD integration.

Exit codes:
  0 - Success
  1 - Failure

Output:
  - artifacts/output.pdf - Converted PDF
  - artifacts/smoke.log - JSONL structured logs
"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Add backend to Python path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.core.pdf_processor import PDFProcessor


class SmokeTestLogger:
    """Structured JSONL logger for smoke test."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, msg: str, **kwargs) -> None:
        """Write a JSONL log entry to both stdout and file."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "msg": msg,
            **kwargs
        }

        line = json.dumps(entry)
        print(line)  # Print to stdout

        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def info(self, msg: str, **kwargs) -> None:
        self.log("INFO", msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self.log("ERROR", msg, **kwargs)

    def success(self, msg: str, **kwargs) -> None:
        self.log("SUCCESS", msg, **kwargs)


def run_smoke_test() -> int:
    """
    Run the PDF conversion smoke test.

    Returns:
        0 on success, 1 on failure
    """
    # Configuration
    INPUT_PDF = REPO_ROOT / "testdata" / "input.pdf"
    OUTPUT_PDF = REPO_ROOT / "artifacts" / "output.pdf"
    LOG_FILE = REPO_ROOT / "artifacts" / "smoke.log"
    TEST_KEY = "C"
    TEST_MODE = "major"
    MIN_OUTPUT_SIZE = 100  # Minimum expected output size in bytes

    # Initialize logger
    logger = SmokeTestLogger(LOG_FILE)

    # Clear previous log file
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    # Create artifacts directory
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Log test start
        logger.info(
            "Starting smoke test",
            in_pdf=str(INPUT_PDF),
            out_pdf=str(OUTPUT_PDF),
            key=TEST_KEY,
            mode=TEST_MODE
        )

        # Check input PDF exists
        if not INPUT_PDF.exists():
            logger.error(
                "Input PDF not found",
                in_pdf=str(INPUT_PDF)
            )
            return 1

        input_size = INPUT_PDF.stat().st_size
        logger.info(
            "Input PDF found",
            in_pdf=str(INPUT_PDF),
            size_bytes=input_size
        )

        # Run actual conversion (production code path)
        logger.info("Running conversion")
        processor = PDFProcessor()

        # Execute the conversion
        processor.process_pdf(
            input_pdf_path=str(INPUT_PDF),
            output_pdf_path=str(OUTPUT_PDF),
            key=TEST_KEY,
            mode=TEST_MODE
        )

        logger.info("Conversion completed")

        # Sanity check: Output file exists
        if not OUTPUT_PDF.exists():
            logger.error(
                "Output PDF not created",
                out_pdf=str(OUTPUT_PDF)
            )
            return 1

        output_size = OUTPUT_PDF.stat().st_size

        # Sanity check: Output file has reasonable size
        if output_size < MIN_OUTPUT_SIZE:
            logger.error(
                "Output PDF too small",
                out_pdf=str(OUTPUT_PDF),
                size_bytes=output_size,
                min_expected_bytes=MIN_OUTPUT_SIZE
            )
            return 1

        # Success!
        logger.success(
            "Smoke test passed",
            in_pdf=str(INPUT_PDF),
            out_pdf=str(OUTPUT_PDF),
            input_size_bytes=input_size,
            output_size_bytes=output_size,
            key=TEST_KEY,
            mode=TEST_MODE
        )

        return 0

    except Exception as e:
        # Log failure with full exception details
        logger.error(
            "Conversion Failed",
            in_pdf=str(INPUT_PDF),
            out_pdf=str(OUTPUT_PDF),
            error={
                "name": type(e).__name__,
                "message": str(e),
                "stack": traceback.format_exc()
            }
        )
        return 1


if __name__ == "__main__":
    exit_code = run_smoke_test()
    sys.exit(exit_code)
