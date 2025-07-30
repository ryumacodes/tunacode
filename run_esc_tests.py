#!/usr/bin/env python
"""
Test runner for ESC interrupt functionality.

This script provides a convenient way to run the ESC cancellation tests
with different options and configurations.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(cmd, timeout=None, description=""):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🏃 {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            timeout=timeout, 
            capture_output=False,
            text=True
        )
        end_time = time.time()
        elapsed = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ PASSED in {elapsed:.1f}s")
            return True
        else:
            print(f"❌ FAILED in {elapsed:.1f}s (exit code {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"⏰ TIMEOUT after {elapsed:.1f}s")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run ESC interrupt tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "concurrency", "all", "quick"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per test suite in seconds"
    )
    parser.add_argument(
        "--markers", "-m",
        default="",
        help="Pytest markers to filter tests"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Build base pytest command
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    if args.fail_fast:
        base_cmd.append("-x")
    
    # Add timeout
    base_cmd.extend(["--timeout", str(args.timeout)])
    
    # Add markers if specified
    if args.markers:
        base_cmd.extend(["-m", args.markers])
    
    # Determine which tests to run
    test_suites = []
    
    if args.type in ["unit", "all", "quick"]:
        test_suites.append({
            "name": "Unit Tests",
            "path": "tests/test_esc_interrupt_unit.py",
            "timeout": 120,
            "description": "Basic unit tests with stubbed agents"
        })
    
    if args.type in ["integration", "all"]:
        test_suites.append({
            "name": "Integration Tests", 
            "path": "tests/test_esc_interrupt_integration.py",
            "timeout": 300,
            "description": "pexpect-style REPL boundary tests"
        })
    
    if args.type in ["concurrency", "all"]:
        test_suites.append({
            "name": "Concurrency Tests",
            "path": "tests/test_esc_interrupt_concurrency.py", 
            "timeout": 600,
            "description": "Torture tests for parallel cancellation"
        })
    
    if args.type == "quick":
        # Quick smoke test - just the essential cancellation markers
        test_suites = [{
            "name": "Quick Tests",
            "path": "tests/test_esc_interrupt_unit.py",
            "timeout": 60,
            "description": "Quick smoke test of essential functionality",
            "extra_args": ["-m", "cancellation"]
        }]
    
    print(f"🧪 Running ESC Interrupt Tests")
    print(f"Test type: {args.type}")
    print(f"Test suites: {len(test_suites)}")
    print(f"Timeout per suite: {args.timeout}s")
    
    # Run each test suite
    results = []
    overall_start = time.time()
    
    for suite in test_suites:
        cmd = base_cmd.copy()
        cmd.append(suite["path"])
        
        # Add suite-specific timeout
        suite_timeout = suite.get("timeout", args.timeout)
        cmd = [c for c in cmd if c not in ["--timeout", str(args.timeout)]]
        cmd.extend(["--timeout", str(suite_timeout)])
        
        # Add extra args if specified
        if "extra_args" in suite:
            cmd.extend(suite["extra_args"])
        
        success = run_command(
            cmd,
            timeout=suite_timeout + 30,  # Add buffer for pytest overhead
            description=f"{suite['name']}: {suite['description']}"
        )
        
        results.append({
            "name": suite["name"],
            "success": success
        })
    
    # Print summary
    overall_end = time.time()
    total_elapsed = overall_end - overall_start
    
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total time: {total_elapsed:.1f}s")
    print()
    
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status:12} {result['name']}")
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print("ESC interrupt functionality is working correctly!")
        return 0
    else:
        print("⚠️ Some tests failed.")
        if failed >= 2:
            print("💡 Consider implementing the fallback pre-emptive cancellation window.")
        return 1


if __name__ == "__main__":
    sys.exit(main())