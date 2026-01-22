#!/usr/bin/env python3
"""
PDF Test Runner - Iterative testing tool for PDF generation

This script allows you to test PDF generation with detailed diagnostics.
You can run it repeatedly until the PDF processes correctly.

Usage:
    python test_pdf_runner.py <input_pdf> [--key C] [--mode major] [--verbose]

Example:
    python test_pdf_runner.py tests/fixtures/input/sample.pdf --key G --mode major -v
"""

import sys
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.pdf_processor import PDFProcessor  # noqa: E402


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def validate_input(input_path: Path) -> bool:
    """Validate input PDF exists and is readable"""
    if not input_path.exists():
        print_error(f"Input file does not exist: {input_path}")
        return False

    if not input_path.is_file():
        print_error(f"Input path is not a file: {input_path}")
        return False

    if input_path.suffix.lower() != '.pdf':
        print_warning(f"Input file does not have .pdf extension: {input_path}")

    file_size = input_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    if file_size_mb > 10:
        print_error(f"File size ({file_size_mb:.2f} MB) exceeds 10 MB limit")
        return False

    print_success(f"Input file validated: {input_path.name} ({file_size_mb:.2f} MB)")
    return True


def run_pdf_test(
    input_path: Path,
    output_path: Path,
    key: str = "C",
    mode: str = "major",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run PDF processing with detailed diagnostics

    Returns a dict with:
        - success: bool
        - error: Optional[str]
        - stats: Optional[Dict]
        - output_path: Optional[Path]
    """
    result = {
        'success': False,
        'error': None,
        'stats': None,
        'output_path': None
    }

    try:
        print_header("Starting PDF Processing")

        # Initialize processor
        print_info("Initializing PDF processor...")
        processor = PDFProcessor()

        # Run processing
        print_info(f"Processing: {input_path.name}")
        print_info(f"Key: {key} {mode}")
        print_info(f"Output: {output_path.name}")

        start_time = datetime.now()

        process_result = processor.process_pdf(
            str(input_path),
            str(output_path),
            key=key,
            mode=mode
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Check results
        if process_result.get('success'):
            print_header("Processing Successful")
            print_success(f"Processing completed in {duration:.2f} seconds")

            result['success'] = True
            result['stats'] = process_result
            result['output_path'] = output_path

            # Print statistics
            if verbose:
                print_info("\nProcessing Statistics:")
                print(f"  PDF Type: {process_result.get('pdf_type', 'unknown')}")
                print(f"  Pages Processed: {process_result.get('pages_processed', 0)}")
                print(f"  Chords Found: {process_result.get('chords_found', 0)}")
                print(f"  Chords Converted: {process_result.get('chords_converted', 0)}")

                if 'render_quality' in process_result:
                    quality = process_result['render_quality']
                    print(f"  Render Quality: {quality.get('score', 0):.1f}/100")
                    print(f"  Font Match Rate: {quality.get('font_match_rate', 0):.1f}%")
                    print(f"  Size Match Rate: {quality.get('size_match_rate', 0):.1f}%")

                if 'ocr_confidence' in process_result:
                    ocr = process_result['ocr_confidence']
                    print(f"  OCR Mean Confidence: {ocr.get('mean', 0):.1f}%")
                    print(f"  OCR Median Confidence: {ocr.get('median', 0):.1f}%")

            # Verify output exists
            if output_path.exists():
                output_size = output_path.stat().st_size / 1024
                print_success(f"Output file created: {output_path.name} ({output_size:.1f} KB)")
            else:
                print_error("Output file was not created!")
                result['success'] = False
                result['error'] = "Output file not found"

        else:
            error_msg = process_result.get('error', 'Unknown error')
            print_header("Processing Failed")
            print_error(f"Error: {error_msg}")
            result['error'] = error_msg

            if verbose and 'traceback' in process_result:
                print("\n" + process_result['traceback'])

    except Exception as e:
        print_header("Processing Failed with Exception")
        print_error(f"Exception: {str(e)}")

        if verbose:
            print("\nFull Traceback:")
            traceback.print_exc()

        result['error'] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Test PDF generation with detailed diagnostics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with defaults (C major)
  python test_pdf_runner.py tests/fixtures/input/sample.pdf

  # Test with specific key
  python test_pdf_runner.py input.pdf --key G --mode minor

  # Verbose output with diagnostics
  python test_pdf_runner.py input.pdf -v

  # Specify custom output location
  python test_pdf_runner.py input.pdf -o output.pdf
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='Input PDF file path'
    )

    parser.add_argument(
        '-k', '--key',
        type=str,
        default='C',
        help='Musical key (default: C)'
    )

    parser.add_argument(
        '-m', '--mode',
        type=str,
        default='major',
        choices=['major', 'minor'],
        help='Musical mode (default: major)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output PDF path (default: tests/fixtures/output/<input>_nashville.pdf)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output with detailed diagnostics'
    )

    args = parser.parse_args()

    # Resolve paths
    input_path = Path(args.input).resolve()

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        # Default output to fixtures/output directory
        output_dir = Path(__file__).parent / 'fixtures' / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = f"{input_path.stem}_nashville.pdf"
        output_path = output_dir / output_name

    # Print configuration
    print_header("PDF Test Runner")
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Key:    {args.key} {args.mode}")
    print(f"Verbose: {args.verbose}")

    # Validate input
    if not validate_input(input_path):
        sys.exit(1)

    # Run test
    result = run_pdf_test(
        input_path=input_path,
        output_path=output_path,
        key=args.key,
        mode=args.mode,
        verbose=args.verbose
    )

    # Print final status
    print_header("Final Status")

    if result['success']:
        print_success("PDF processing completed successfully!")
        print(f"\nOutput: {result['output_path']}")
        sys.exit(0)
    else:
        print_error("PDF processing failed!")
        if result['error']:
            print(f"\nError: {result['error']}")
        sys.exit(1)


if __name__ == '__main__':
    main()
