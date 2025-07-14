#!/usr/bin/env python3
"""
Test runner script for EZBI Analytics comprehensive testing framework.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
import time
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner for EZBI Analytics."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.results = {}
        
    def run_unit_tests(self, coverage: bool = True) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "-v",
            "--tb=short",
            "-m", "unit"
        ]
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov/unit",
                "--cov-report=term-missing"
            ])
        
        result = self._run_command(cmd)
        self.results['unit_tests'] = result
        return result
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"),
            "-v",
            "--tb=short",
            "-m", "integration"
        ]
        
        result = self._run_command(cmd)
        self.results['integration_tests'] = result
        return result
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests."""
        print("🌐 Running End-to-End Tests...")
        
        # Install Playwright browsers if needed
        self._install_playwright_browsers()
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "e2e"),
            "-v",
            "--tb=short",
            "-m", "e2e",
            "--timeout=300"
        ]
        
        result = self._run_command(cmd)
        self.results['e2e_tests'] = result
        return result
    
    def run_ml_tests(self) -> Dict[str, Any]:
        """Run ML model tests."""
        print("🤖 Running ML Model Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "ml"),
            "-v",
            "--tb=short",
            "-m", "ml",
            "--timeout=600"
        ]
        
        result = self._run_command(cmd)
        self.results['ml_tests'] = result
        return result
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "performance"),
            "-v",
            "--tb=short",
            "-m", "performance",
            "--timeout=600",
            "--benchmark-only"
        ]
        
        result = self._run_command(cmd)
        self.results['performance_tests'] = result
        return result
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""
        print("🔒 Running Security Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "security"),
            "-v",
            "--tb=short",
            "-m", "security"
        ]
        
        result = self._run_command(cmd)
        self.results['security_tests'] = result
        return result
    
    def run_manufacturing_tests(self) -> Dict[str, Any]:
        """Run manufacturing-specific tests."""
        print("🏭 Running Manufacturing Domain Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "-m", "manufacturing"
        ]
        
        result = self._run_command(cmd)
        self.results['manufacturing_tests'] = result
        return result
    
    def run_french_compliance_tests(self) -> Dict[str, Any]:
        """Run French compliance tests."""
        print("🇫🇷 Running French Compliance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "-m", "french"
        ]
        
        result = self._run_command(cmd)
        self.results['french_compliance_tests'] = result
        return result
    
    def run_all_tests(self, skip_slow: bool = False) -> Dict[str, Any]:
        """Run all test suites."""
        print("🚀 Running Complete Test Suite...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "--cov=app",
            "--cov-report=html:htmlcov/complete",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--junit-xml=test-results.xml"
        ]
        
        if skip_slow:
            cmd.extend(["-m", "not slow"])
        
        result = self._run_command(cmd)
        self.results['all_tests'] = result
        return result
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run smoke tests for quick validation."""
        print("💨 Running Smoke Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "test_main.py"),
            str(self.test_dir / "unit/test_auth.py::TestPasswordSecurity::test_password_hashing"),
            str(self.test_dir / "integration/test_api_endpoints.py::TestAuthEndpoints::test_login_success"),
            "-v",
            "--tb=short"
        ]
        
        result = self._run_command(cmd)
        self.results['smoke_tests'] = result
        return result
    
    def run_parallel_tests(self, workers: int = 4) -> Dict[str, Any]:
        """Run tests in parallel."""
        print(f"⚡ Running Tests in Parallel (workers: {workers})...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-v",
            "--tb=short",
            "-n", str(workers),
            "--dist=loadfile"
        ]
        
        result = self._run_command(cmd)
        self.results['parallel_tests'] = result
        return result
    
    def generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        print("📊 Generating Test Report...")
        
        report_dir = self.test_dir / "reports"
        report_dir.mkdir(exist_ok=True)
        
        # Generate HTML report
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "--html=reports/test-report.html",
            "--self-contained-html",
            "--collect-only"
        ]
        
        self._run_command(cmd)
        
        # Generate coverage report
        if 'all_tests' in self.results:
            print("📈 Coverage report available at: htmlcov/complete/index.html")
        
        # Print summary
        self._print_test_summary()
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run security audit tools."""
        print("🔍 Running Security Audit...")
        
        results = {}
        
        # Run bandit for security issues
        try:
            cmd = ["bandit", "-r", str(self.project_root / "app"), "-f", "json"]
            result = self._run_command(cmd)
            results['bandit'] = result
        except FileNotFoundError:
            print("⚠️ Bandit not installed, skipping security scan")
        
        # Run safety for dependency vulnerabilities
        try:
            cmd = ["safety", "check", "--json"]
            result = self._run_command(cmd)
            results['safety'] = result
        except FileNotFoundError:
            print("⚠️ Safety not installed, skipping dependency scan")
        
        self.results['security_audit'] = results
        return results
    
    def run_code_quality_checks(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("📝 Running Code Quality Checks...")
        
        results = {}
        
        # Run ruff for linting
        try:
            cmd = ["ruff", "check", str(self.project_root / "app")]
            result = self._run_command(cmd)
            results['ruff'] = result
        except FileNotFoundError:
            print("⚠️ Ruff not installed, skipping linting")
        
        # Run mypy for type checking
        try:
            cmd = ["mypy", str(self.project_root / "app")]
            result = self._run_command(cmd)
            results['mypy'] = result
        except FileNotFoundError:
            print("⚠️ MyPy not installed, skipping type checking")
        
        self.results['code_quality'] = results
        return results
    
    def setup_test_environment(self) -> None:
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        
        # Set environment variables
        os.environ['TESTING'] = '1'
        os.environ['ENVIRONMENT'] = 'testing'
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test'
        
        # Create test directories
        (self.test_dir / "reports").mkdir(exist_ok=True)
        (self.test_dir / "htmlcov").mkdir(exist_ok=True)
        
        # Install test requirements
        try:
            cmd = ["pip", "install", "-r", str(self.test_dir / "test_requirements.txt")]
            self._run_command(cmd)
        except Exception as e:
            print(f"⚠️ Warning: Could not install test requirements: {e}")
    
    def _install_playwright_browsers(self) -> None:
        """Install Playwright browsers."""
        try:
            cmd = ["playwright", "install"]
            self._run_command(cmd)
        except FileNotFoundError:
            print("⚠️ Playwright not installed, skipping browser installation")
        except Exception as e:
            print(f"⚠️ Warning: Could not install Playwright browsers: {e}")
    
    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Run a command and return results."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration,
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'duration': 1800,
                'command': ' '.join(cmd)
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0,
                'command': ' '.join(cmd)
            }
    
    def _print_test_summary(self) -> None:
        """Print test execution summary."""
        print("\n" + "="*80)
        print("📋 TEST EXECUTION SUMMARY")
        print("="*80)
        
        total_duration = 0
        passed_suites = 0
        failed_suites = 0
        
        for suite_name, result in self.results.items():
            if isinstance(result, dict):
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                duration = result.get('duration', 0)
                total_duration += duration
                
                if result.get('success', False):
                    passed_suites += 1
                else:
                    failed_suites += 1
                
                print(f"{suite_name:25} | {status} | {duration:.2f}s")
        
        print("-"*80)
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Passed Suites:  {passed_suites}")
        print(f"Failed Suites:  {failed_suites}")
        print(f"Success Rate:   {passed_suites/(passed_suites + failed_suites)*100:.1f}%")
        print("="*80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="EZBI Analytics Test Runner")
    
    parser.add_argument(
        "--suite",
        choices=[
            "unit", "integration", "e2e", "ml", "performance", 
            "security", "manufacturing", "french", "all", "smoke"
        ],
        default="all",
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers"
    )
    
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow tests"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up test environment"
    )
    
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run security audit"
    )
    
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Run code quality checks"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.setup:
        runner.setup_test_environment()
        return
    
    if args.audit:
        runner.run_security_audit()
        return
    
    if args.quality:
        runner.run_code_quality_checks()
        return
    
    # Run tests based on arguments
    if args.parallel:
        runner.run_parallel_tests(args.workers)
    elif args.suite == "unit":
        runner.run_unit_tests(coverage=not args.no_coverage)
    elif args.suite == "integration":
        runner.run_integration_tests()
    elif args.suite == "e2e":
        runner.run_e2e_tests()
    elif args.suite == "ml":
        runner.run_ml_tests()
    elif args.suite == "performance":
        runner.run_performance_tests()
    elif args.suite == "security":
        runner.run_security_tests()
    elif args.suite == "manufacturing":
        runner.run_manufacturing_tests()
    elif args.suite == "french":
        runner.run_french_compliance_tests()
    elif args.suite == "smoke":
        runner.run_smoke_tests()
    elif args.suite == "all":
        runner.run_all_tests(skip_slow=args.skip_slow)
    
    # Generate report
    runner.generate_test_report()


if __name__ == "__main__":
    main()