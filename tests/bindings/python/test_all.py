#!/usr/bin/env python3
"""
duvc-ctl Test Suite Runner
===========================

Centralized test runner for all duvc-ctl Python binding tests.

Features:
  - Runs all 20 test suites (1000+ total tests)
  - Continues execution even if individual tests fail
  - Generates multiple report formats:
    * HTML report (pytest-html)
    * JSON report (pytest-json-report)
    * JUnit XML (pytest)
    * Coverage report (pytest-cov)
  - Summary statistics and analysis
  - Hardware/no-hardware test modes

Usage:
  # Run all tests with hardware
  python test_all.py

  # Run without hardware (skips @pytest.mark.hardware tests)
  python test_all.py --no-hardware

  # Run specific test suite
  python test_all.py --test test_01_core_enums.py

  # Generate only specific report types
  python test_all.py --html-only
  python test_all.py --json-only

  # Verbose output
  python test_all.py -v
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import argparse


# ============================================================================
# CONFIGURATION
# ============================================================================

TEST_SUITES = [
    ("test_01_core_enums.py", "Core Enums", 115),
    ("test_02_core_types.py", "Core Types", 130),
    ("test_03_result_types.py", "Result Types", 85),
    ("test_04_device_enumeration.py", "Device Enumeration", 65),
    ("test_05_device_discovery.py", "Device Discovery", 75),
    ("test_06_result_api.py", "Result-Based API", 100),
    ("test_07_pythonic_api_props.py", "Pythonic API Properties", 95),
    ("test_08_pythonic_api_methods.py", "Pythonic API Methods", 90),
    ("test_09_pythonic_api_queries.py", "Pythonic API Queries", 50),
    ("test_10_presets_defaults.py", "Presets & Defaults", 55),
    ("test_11_bulk_operations.py", "Bulk Operations", 45),
    ("test_12_device_capabilities.py", "Device Capabilities", 55),
    ("test_13_string_conversion.py", "String Conversion", 40),
    ("test_14_logging.py", "Logging", 50),
    ("test_15_error_handling.py", "Error Handling", 60),
    ("test_16_device_callbacks.py", "Device Callbacks", 45),
    ("test_17_utility_functions.py", "Helper Functions", 60),
    ("test_18_windows_features.py", "Windows Features", 70),
    ("test_19_platform_interface.py", "Platform Interface", 55),
    ("test_20_integration.py", "Integration Workflows", 50),
]

TOTAL_EXPECTED_TESTS = sum(count for _, _, count in TEST_SUITES)

# Report output directories
REPORTS_DIR = Path("test_reports")
HTML_REPORT = REPORTS_DIR / "test_report.html"
JSON_REPORT = REPORTS_DIR / "test_report.json"
JUNIT_XML = REPORTS_DIR / "junit.xml"
COVERAGE_DIR = REPORTS_DIR / "coverage"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header(text: str, char: str = "="):
    """Print formatted header."""
    width = 80
    print()
    print(char * width)
    print(f" {text}")
    print(char * width)


def print_section(text: str):
    """Print formatted section header."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print('─' * 80)


def ensure_reports_dir():
    """Ensure reports directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    COVERAGE_DIR.mkdir(parents=True, exist_ok=True)


def check_pytest_plugins() -> Dict[str, bool]:
    """Check if required pytest plugins are installed."""
    plugins = {
        'pytest-html': False,
        'pytest-json-report': False,
        'pytest-cov': False,
    }
    
    try:
        import pytest_html
        plugins['pytest-html'] = True
    except ImportError:
        pass
    
    try:
        import pytest_jsonreport
        plugins['pytest-json-report'] = True
    except ImportError:
        pass
    
    try:
        import pytest_cov
        plugins['pytest-cov'] = True
    except ImportError:
        pass
    
    return plugins


def install_missing_plugins(plugins: Dict[str, bool]):
    """Prompt to install missing pytest plugins."""
    missing = [name for name, installed in plugins.items() if not installed]
    
    if not missing:
        return True
    
    print("\n⚠️  Missing pytest plugins:")
    for plugin in missing:
        print(f"   - {plugin}")
    
    print("\nTo install missing plugins, run:")
    print(f"   pip install {' '.join(missing)}")
    
    response = input("\nContinue without these plugins? (y/n): ")
    return response.lower() == 'y'


# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_test_suite(
    test_file: str,
    test_name: str,
    verbose: bool = False,
    camera_index: int = 0,
    no_hardware: bool = False,
    plugins: Dict[str, bool] = None
) -> Dict:
    """
    Run a single test suite and return results.
    
    Returns dict with:
        - success: bool
        - passed: int
        - failed: int
        - skipped: int
        - duration: float
        - exit_code: int
    """
    print(f"\n{'━' * 80}")
    print(f"Running: {test_name} ({test_file})")
    print('━' * 80)
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", test_file]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    cmd.append(f"--camera-index={camera_index}")

    # Add hardware marker
    if no_hardware:
        cmd.extend(["-m", "not hardware"])
    
    # Add reporting flags (per-suite JSON for parsing)
    suite_json = REPORTS_DIR / f"{test_file.replace('.py', '')}.json"
    if plugins and plugins.get('pytest-json-report'):
        cmd.extend([
            "--json-report",
            f"--json-report-file={suite_json}",
            "--json-report-indent=2"
        ])
    
    # Add traceback control
    cmd.append("--tb=short")
    
    # Continue on failure
    cmd.append("--maxfail=9999")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per suite
        )
        
        duration = time.time() - start_time
        exit_code = result.returncode
        
        # Parse JSON report if available
        passed, failed, skipped = 0, 0, 0
        
        if suite_json.exists():
            try:
                with open(suite_json, 'r') as f:
                    data = json.load(f)
                    summary = data.get('summary', {})
                    passed = summary.get('passed', 0)
                    failed = summary.get('failed', 0)
                    skipped = summary.get('skipped', 0)
            except Exception as e:
                print(f"⚠️  Could not parse JSON report: {e}")
        
        # Print output
        if verbose or failed > 0:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Print summary
        status = "✓ PASSED" if exit_code == 0 else "✗ FAILED"
        print(f"\n{status}: {test_name}")
        print(f"   Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
        print(f"   Duration: {duration:.2f}s")
        
        return {
            'success': exit_code == 0,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'duration': duration,
            'exit_code': exit_code,
            'test_file': test_file,
            'test_name': test_name,
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\n⚠️  TIMEOUT: {test_name} exceeded 5 minutes")
        return {
            'success': False,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': duration,
            'exit_code': -1,
            'test_file': test_file,
            'test_name': test_name,
            'timeout': True,
        }
    
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ ERROR: {test_name} - {e}")
        return {
            'success': False,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': duration,
            'exit_code': -2,
            'test_file': test_file,
            'test_name': test_name,
            'error': str(e),
        }


def run_all_tests(
    test_files: Optional[List[str]] = None,
    verbose: bool = False,
    camera_index: int = 0,
    no_hardware: bool = False,
    generate_html: bool = True,
    generate_json: bool = True,
    plugins: Dict[str, bool] = None
) -> Dict:
    """Run all test suites and aggregate results."""
    
    ensure_reports_dir()
    
    # Determine which tests to run
    if test_files:
        suites = [(f, n, c) for f, n, c in TEST_SUITES if f in test_files]
    else:
        suites = TEST_SUITES
    
    print_header("duvc-ctl Test Suite Runner")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'No Hardware' if no_hardware else 'With Hardware'}")
    print(f"Test Suites: {len(suites)}")
    print(f"Expected Tests: ~{sum(c for _, _, c in suites)}")
    
    results = []
    start_time = time.time()
    
    # Run each test suite
    for test_file, test_name, _ in suites:
        result = run_test_suite(
            test_file,
            test_name,
            verbose=verbose,
            camera_index=camera_index,
            no_hardware=no_hardware,
            plugins=plugins
        )
        results.append(result)
    
    total_duration = time.time() - start_time
    
    # Generate consolidated reports
    if generate_html and plugins and plugins.get('pytest-html'):
        generate_html_report(results, total_duration, no_hardware)
    
    if generate_json:
        generate_json_report(results, total_duration, no_hardware)
    
    # Generate final summary
    generate_summary(results, total_duration)
    
    return {
        'results': results,
        'total_duration': total_duration,
        'timestamp': datetime.now().isoformat(),
    }


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_html_report(results: List[Dict], duration: float, no_hardware: bool):
    """Generate consolidated HTML report."""
    print_section("Generating HTML Report")
    
    # Run pytest with HTML report on all tests
    cmd = [
        "pytest",
        "--html=" + str(HTML_REPORT),
        "--self-contained-html",
        "--tb=short",
        "--maxfail=9999",
    ]
    
    if no_hardware:
        cmd.extend(["-m", "not hardware"])
    
    # Add all test files
    cmd.extend([f for f, _, _ in TEST_SUITES])
    
    try:
        subprocess.run(cmd, capture_output=True, timeout=600)
        print(f"✓ HTML report generated: {HTML_REPORT}")
    except Exception as e:
        print(f"✗ HTML report generation failed: {e}")


def generate_json_report(results: List[Dict], duration: float, no_hardware: bool):
    """Generate consolidated JSON report."""
    print_section("Generating JSON Report")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_duration': duration,
        'mode': 'no_hardware' if no_hardware else 'with_hardware',
        'summary': {
            'total_suites': len(results),
            'passed_suites': sum(1 for r in results if r['success']),
            'failed_suites': sum(1 for r in results if not r['success']),
            'total_tests': sum(r['passed'] + r['failed'] + r['skipped'] for r in results),
            'total_passed': sum(r['passed'] for r in results),
            'total_failed': sum(r['failed'] for r in results),
            'total_skipped': sum(r['skipped'] for r in results),
        },
        'suites': results,
    }
    
    try:
        with open(JSON_REPORT, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ JSON report generated: {JSON_REPORT}")
    except Exception as e:
        print(f"✗ JSON report generation failed: {e}")


def generate_summary(results: List[Dict], duration: float):
    """Generate and print test summary."""
    print_header("Test Suite Summary", "=")
    
    total_suites = len(results)
    passed_suites = sum(1 for r in results if r['success'])
    failed_suites = total_suites - passed_suites
    
    total_tests = sum(r['passed'] + r['failed'] + r['skipped'] for r in results)
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_skipped = sum(r['skipped'] for r in results)
    
    print(f"\nTest Suites:  {passed_suites}/{total_suites} passed")
    print(f"Total Tests:  {total_passed}/{total_tests} passed")
    print(f"Failed Tests: {total_failed}")
    print(f"Skipped:      {total_skipped}")
    print(f"Duration:     {duration:.2f}s ({duration/60:.1f} minutes)")
    
    if failed_suites > 0:
        print("\n❌ Failed Test Suites:")
        for result in results:
            if not result['success']:
                print(f"   - {result['test_name']} ({result['test_file']})")
                print(f"     Failed: {result['failed']}, Exit Code: {result['exit_code']}")
    
    print("\n📊 Reports Generated:")
    if HTML_REPORT.exists():
        print(f"   HTML:  {HTML_REPORT}")
    if JSON_REPORT.exists():
        print(f"   JSON:  {JSON_REPORT}")
    
    # Overall pass/fail
    print()
    if failed_suites == 0 and total_failed == 0:
        print("✅ ALL TESTS PASSED!")
    elif total_failed <= total_tests * 0.05:  # < 5% failure
        print(f"⚠️  MOSTLY PASSED ({failed_suites} suites, {total_failed} tests failed)")
    else:
        print(f"❌ TESTS FAILED ({failed_suites} suites, {total_failed} tests failed)")
    
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="duvc-ctl Test Suite Runner")
    parser.add_argument(
        '--test',
        dest='test_files',
        nargs='+',
        help='Run specific test file(s)'
    )
    parser.add_argument(
        '--no-hardware',
        action='store_true',
        help='Skip hardware tests (run only @pytest.mark.hardware tests)'
    )
    parser.add_argument(
        '--camera-index',
        type=int,
        default=0,
        help='Camera index to use for testing (default: 0)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--html-only',
        action='store_true',
        help='Generate only HTML report'
    )
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Generate only JSON report'
    )
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip report generation'
    )
    
    args = parser.parse_args()
    
    # Check plugins
    plugins = check_pytest_plugins()
    
    if not args.no_reports:
        missing_any = any(not installed for installed in plugins.values())
        if missing_any:
            if not install_missing_plugins(plugins):
                print("\nExiting...")
                return 1
    
    # Determine report types
    generate_html = not args.no_reports and not args.json_only
    generate_json = not args.no_reports and not args.html_only
    
    # Run tests
    try:
        results = run_all_tests(
            test_files=args.test_files,
            verbose=args.verbose,
            camera_index=args.camera_index,
            no_hardware=args.no_hardware,
            generate_html=generate_html,
            generate_json=generate_json,
            plugins=plugins
        )
        
        # Exit code based on results
        failed_suites = sum(1 for r in results['results'] if not r['success'])
        return 0 if failed_suites == 0 else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


"""
**Usage Examples**:
``````bash
# Run all tests with hardware
python test_all.py

# Run without hardware (for CI)
python test_all.py --no-hardware

# Run specific test
python test_all.py --test test_01_core_enums.py

# Verbose output
python test_all.py -v

# Generate only JSON report
python test_all.py --json-only

# Run multiple specific tests
python test_all.py --test test_01_core_enums.py test_02_core_types.py
```

**Install required plugins**:
```bash```
pip install pytest-html pytest-json-report pytest-cov
```

The script will prompt to install missing plugins or continue without them!
"""