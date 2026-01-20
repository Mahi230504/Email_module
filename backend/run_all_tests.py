"""
Comprehensive End-to-End Test Runner Script

Run with: python run_all_tests.py
"""

import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Runs all tests and generates comprehensive report."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": [],
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_duration": 0.0
        }
    
    def run_pytest(self, test_files, description):
        """Run pytest on specified files."""
        cmd = [
            "./venv/bin/pytest",
            *test_files,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=.test_report.json"
        ]
        
        print(f"\n{'='*70}")
        print(f"Running: {description}")
        print(f"{'='*70}\n")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/Users/kabeer/Downloads/TCO-email-module/backend"
        )
        
        suite_result = {
            "name": description,
            "files": test_files,
            "exit_code": result.exit_code,
            "output": result.stdout
        }
        
        self.results["test_suites"].append(suite_result)
        
        # Parse output for pass/fail counts
        if "passed" in result.stdout:
            print(result.stdout)
        else:
            print(result.stderr)
        
        return result.exit_code == 0
    
    def generate_report(self):
        """Generate comprehensive test report."""
        report = []
        report.append("="*70)
        report.append("COMPREHENSIVE TEST EXECUTION REPORT")
        report.append("="*70)
        report.append(f"\nGenerated: {self.results['timestamp']}\n")
        
        all_passed = True
        
        for suite in self.results["test_suites"]:
            status = "✅ PASSED" if suite["exit_code"] == 0 else "❌ FAILED"
            report.append(f"\n{suite['name']}: {status}")
            report.append(f"  Files: {', '.join(suite['files'])}")
            
            if suite["exit_code"] != 0:
                all_passed = False
        
        report.append("\n" + "="*70)
        if all_passed:
            report.append("✅ ALL TEST SUITES PASSED - PRODUCTION READY")
        else:
            report.append("❌ SOME TESTS FAILED - REVIEW REQUIRED")
        report.append("="*70)
        
        return "\n".join(report)
    
    def save_report(self, report):
        """Save report to file."""
        report_path = "/Users/kabeer/Downloads/TCO-email-module/backend/test_results.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n📄 Full report saved to: {report_path}")


def main():
    """Main test execution."""
    runner = TestRunner()
    
    # Test Suite 1: Core Services
    runner.run_pytest(
        ["tests/test_threading.py", "tests/test_classification.py"],
        "Core Services (Threading Engine & Classification)"
    )
    
    # Test Suite 2: Authentication
    runner.run_pytest(
        ["tests/test_api_auth.py"],
        "Authentication API Endpoints"
    )
    
    # Test Suite 3: Client Management
    runner.run_pytest(
        ["tests/test_api_clients.py"],
        "Client Management API"
    )
    
    # Test Suite 4: Email Operations
    runner.run_pytest(
        ["tests/test_api_emails.py"],
        "Email CRUD Operations"
    )
    
    # Test Suite 5: Thread Management
    runner.run_pytest(
        ["tests/test_api_threads.py"],
        "Thread Management API"
    )
    
    # Test Suite 6: Webhooks
    runner.run_pytest(
        ["tests/test_api_webhooks.py"],
        "Webhook Integration"
    )
    
    # Generate and display report
    report = runner.generate_report()
    print("\n" + report)
    runner.save_report(report)


if __name__ == "__main__":
    main()
