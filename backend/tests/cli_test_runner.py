#!/usr/bin/env python3
"""
CLI Test Runner for Nashville Numbers Converter

Usage:
    python -m backend.tests.cli_test_runner <input.pdf> --key G --mode major [--debug]
"""

import argparse
import sys
import json
import uuid
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.models import ConversionRequest, ConversionMode
from backend.app.config import TEMP_DIR, ensure_temp_dir
from backend.pipeline.processor import NashvillePipeline
from backend.utils.cleanup import TempFileManager
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Test PDF conversion with Nashville Numbers Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        'input',
        type=str,
        help='Input PDF file path'
    )

    parser.add_argument(
        '--key', '-k',
        type=str,
        default='C',
        help='Musical key (default: C)'
    )

    parser.add_argument(
        '--mode', '-m',
        type=str,
        default='major',
        choices=['major', 'minor'],
        help='Musical mode (default: major)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output PDF path (default: auto-generated in output dir)'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode with detailed output'
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Setup
    ensure_temp_dir()
    temp_manager = TempFileManager(TEMP_DIR, ttl_minutes=15)
    pipeline = NashvillePipeline(temp_manager)

    # Determine output path
    if args.output:
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path('backend/tests/fixtures/output')
        output_dir.mkdir(parents=True, exist_ok=True)

    # Read input PDF
    print(f"\nReading PDF: {input_path}")
    with open(input_path, 'rb') as f:
        pdf_bytes = f.read()

    print(f"File size: {len(pdf_bytes) / 1024:.1f} KB")

    # Create request
    correlation_id = str(uuid.uuid4())
    request = ConversionRequest(
        correlation_id=correlation_id,
        key=args.key,
        mode=ConversionMode(args.mode),
    )

    print(f"\nConverting to Nashville numbers...")
    print(f"  Key: {args.key} {args.mode}")
    print(f"  Correlation ID: {correlation_id}")

    # Process
    result, temp_output_path = pipeline.process(pdf_bytes, request)

    # Check result
    if not result.success:
        print(f"\n❌ CONVERSION FAILED")
        if result.error:
            print(f"   Error: {result.error.message}")
            if result.error.details and args.debug:
                print(f"   Details: {json.dumps(result.error.details, indent=2)}")
        sys.exit(1)

    # Success!
    print(f"\n✅ CONVERSION SUCCESSFUL")
    print(f"\nStatistics:")
    print(f"  Processing time: {result.processing_time_seconds:.2f}s")
    print(f"  Pages: {result.pdf_metadata.num_pages if result.pdf_metadata else 'N/A'}")
    print(f"  Tokens extracted: {result.total_tokens_extracted}")
    print(f"  Chords identified: {result.total_chords_identified}")
    print(f"  Chords converted: {result.total_chords_converted}")

    if result.warnings:
        print(f"\n⚠ Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    # Move output to final location
    if args.output:
        final_output_path = Path(args.output)
    else:
        final_output_path = output_dir / f"{input_path.stem}_nashville.pdf"

    if temp_output_path:
        import shutil
        shutil.move(str(temp_output_path), str(final_output_path))
        print(f"\nOutput saved to: {final_output_path}")

    # Debug mode: show detailed info
    if args.debug:
        print(f"\n📊 DEBUG INFO:")
        print(f"  Correlation ID: {correlation_id}")
        print(f"  PDF Type: {result.pdf_metadata.pdf_type if result.pdf_metadata else 'N/A'}")

    sys.exit(0)


if __name__ == '__main__':
    main()
