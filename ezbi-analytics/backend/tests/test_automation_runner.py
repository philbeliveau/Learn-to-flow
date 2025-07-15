#!/usr/bin/env python3
"""
Test Automation Runner - Production Testing Suite
Automated test execution for continuous integration and deployment
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestAutomationRunner:
    """Automated test execution for production deployment."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize test automation runner."""
        self.project_root = project_root
        self.test_dir = self.project_root / "tests"
        self.config = self._load_config(config_path)
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # Create reports directory
        self.reports_dir = self.test_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Set up environment for testing
        self._setup_test_environment()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load test configuration."""
        default_config = {
            "test_suites": {
                "unit": {
                    "path": "unit/",
                    "timeout": 300,
                    "parallel": True,
                    "coverage": True
                },
                "integration": {
                    "path": "integration/",
                    "timeout": 600,
                    "parallel": True,
                    "coverage": True
                },
                "manufacturing": {
                    "path": "test_manufacturing_endpoints.py",
                    "timeout": 900,
                    "parallel": False,
                    "coverage": False
                },
                "security": {
                    "path": "security/",
                    "timeout": 600,
                    "parallel": True,
                    "coverage": False
                },
                "performance": {
                    "path": "performance/",
                    "timeout": 1800,
                    "parallel": False,
                    "coverage": False
                },
                "load_testing": {
                    "path": "test_load_and_ci_cd.py::TestLoadTesting",
                    "timeout": 3600,
                    "parallel": False,
                    "coverage": False
                },
                "production_readiness": {
                    "path": "test_production_readiness.py",
                    "timeout": 1200,
                    "parallel": False,
                    "coverage": False
                }
            },
            "requirements": {
                "min_python_version": "3.9",
                "coverage_threshold": 90.0,
                "max_execution_time": 7200,  # 2 hours
                "environment": "testing"
            },
            "notifications": {
                "email": False,
                "slack": False,
                "webhook": None
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with default config
                default_config.update(user_config)
        
        return default_config
    
    def _setup_test_environment(self):
        """Set up test environment variables."""
        test_env = {
            "TESTING": "1",
            "ENVIRONMENT": "testing",
            "DATABASE_URL": "postgresql+asyncpg://postgres:password@localhost/ezbi_analytics_test",
            "SECRET_KEY": "test_secret_key_for_testing_only_never_use_in_production",
            "REDIS_URL": "redis://localhost:6379/0",
            "LOG_LEVEL": "INFO",
            "PYTHONPATH": str(self.project_root)
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
    
    def validate_environment(self) -> bool:
        """Validate test environment setup."""
        logger.info("Validating test environment...")
        
        # Check Python version
        python_version = sys.version_info
        required_version = tuple(map(int, self.config["requirements"]["min_python_version"].split('.')))
        
        if python_version < required_version:
            logger.error(f"Python {self.config['requirements']['min_python_version']} or higher required")
            return False
        
        # Check required dependencies
        required_packages = [
            "pytest", "pytest-asyncio", "pytest-cov", "httpx", "psutil", "numpy"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            return False
        
        # Check database connection
        try:
            import asyncpg
            # This is a basic check - full connection testing would require async context
            logger.info("Database driver available")
        except ImportError:
            logger.error("Database driver (asyncpg) not available")
            return False
        
        logger.info("Environment validation passed")
        return True
    
    def run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite."""
        logger.info(f"Running test suite: {suite_name}")
        
        if suite_name not in self.config["test_suites"]:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite_config = self.config["test_suites"][suite_name]
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / suite_config["path"]),
            "-v",
            "--tb=short",
            f"--timeout={suite_config['timeout']}",
            "--asyncio-mode=auto"
        ]
        
        # Add coverage if enabled
        if suite_config.get("coverage", False):
            cmd.extend([
                "--cov=app",
                f"--cov-report=html:{self.reports_dir}/coverage_{suite_name}",
                "--cov-report=term-missing",
                "--cov-report=xml"
            ])
        
        # Add parallel execution if enabled
        if suite_config.get("parallel", False):
            cmd.extend(["-n", "auto"])
        
        # Add JUnit XML report
        cmd.extend([
            f"--junit-xml={self.reports_dir}/junit_{suite_name}.xml"
        ])
        
        # Execute test suite
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=suite_config["timeout"]
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            suite_result = {
                "suite": suite_name,
                "success": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(cmd)
            }
            
            # Extract test statistics from output
            suite_result.update(self._parse_test_output(result.stdout))
            
            logger.info(f"Test suite {suite_name} completed in {duration:.2f}s")
            
            return suite_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test suite {suite_name} timed out after {suite_config['timeout']}s")
            return {
                "suite": suite_name,
                "success": False,
                "duration": suite_config["timeout"],
                "error": "Test suite timed out",
                "returncode": -1
            }
        except Exception as e:
            logger.error(f"Error running test suite {suite_name}: {str(e)}")
            return {
                "suite": suite_name,
                "success": False,
                "duration": 0,
                "error": str(e),
                "returncode": -1
            }
    
    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test statistics."""
        stats = {
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "tests_total": 0,
            "coverage_percentage": 0.0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            # Parse test results line
            if "passed" in line and "failed" in line:
                # Example: "5 passed, 2 failed, 1 skipped"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        stats["tests_passed"] = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        stats["tests_failed"] = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        stats["tests_skipped"] = int(parts[i-1])
            
            # Parse coverage line
            if "TOTAL" in line and "%" in line:
                # Example: "TOTAL    1234    567    89%"
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            stats["coverage_percentage"] = float(part[:-1])
                        except ValueError:
                            pass
        
        stats["tests_total"] = stats["tests_passed"] + stats["tests_failed"] + stats["tests_skipped"]
        
        return stats
    
    def run_all_tests(self, parallel_suites: bool = False) -> Dict[str, Any]:
        """Run all test suites."""
        logger.info("Starting comprehensive test execution...")
        
        self.start_time = time.time()
        
        # Define test execution order (dependencies)
        test_order = [
            "unit",
            "integration", 
            "manufacturing",
            "security",
            "performance",
            "load_testing",
            "production_readiness"
        ]
        
        if parallel_suites:
            # Run independent test suites in parallel
            parallel_suites_list = ["unit", "integration", "security"]
            sequential_suites = ["manufacturing", "performance", "load_testing", "production_readiness"]
            
            # Run parallel suites
            with ThreadPoolExecutor(max_workers=3) as executor:
                parallel_futures = {
                    executor.submit(self.run_test_suite, suite): suite 
                    for suite in parallel_suites_list
                }
                
                for future in as_completed(parallel_futures):
                    suite = parallel_futures[future]
                    try:
                        result = future.result()
                        self.results[suite] = result
                    except Exception as e:
                        logger.error(f"Error in parallel suite {suite}: {str(e)}")
                        self.results[suite] = {
                            "suite": suite,
                            "success": False,
                            "error": str(e)
                        }
            
            # Run sequential suites
            for suite in sequential_suites:
                if suite in self.config["test_suites"]:
                    self.results[suite] = self.run_test_suite(suite)
        else:
            # Run all suites sequentially
            for suite in test_order:
                if suite in self.config["test_suites"]:
                    self.results[suite] = self.run_test_suite(suite)
                    
                    # Stop on critical failures
                    if not self.results[suite]["success"] and suite in ["unit", "integration"]:
                        logger.error(f"Critical test suite {suite} failed, stopping execution")
                        break
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        return self._generate_test_report()
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Calculate overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        successful_suites = 0
        total_suites = len(self.results)
        
        for suite_result in self.results.values():
            if suite_result.get("success", False):
                successful_suites += 1
            
            total_tests += suite_result.get("tests_total", 0)
            total_passed += suite_result.get("tests_passed", 0)
            total_failed += suite_result.get("tests_failed", 0)
            total_skipped += suite_result.get("tests_skipped", 0)
        
        # Calculate success rates
        suite_success_rate = successful_suites / total_suites if total_suites > 0 else 0
        test_success_rate = total_passed / total_tests if total_tests > 0 else 0
        
        # Overall test status
        overall_success = (
            suite_success_rate >= 0.8 and  # 80% of suites must pass
            test_success_rate >= 0.9 and   # 90% of tests must pass
            total_failed == 0               # No failed tests in critical areas
        )
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "total_duration": total_duration,
            "summary": {
                "total_suites": total_suites,
                "successful_suites": successful_suites,
                "suite_success_rate": suite_success_rate,
                "total_tests": total_tests,
                "tests_passed": total_passed,
                "tests_failed": total_failed,
                "tests_skipped": total_skipped,
                "test_success_rate": test_success_rate
            },
            "suite_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for failed suites
        failed_suites = [name for name, result in self.results.items() if not result.get("success", False)]
        if failed_suites:
            recommendations.append(f"Fix failing test suites: {', '.join(failed_suites)}")
        
        # Check coverage
        for suite_name, result in self.results.items():
            coverage = result.get("coverage_percentage", 0)
            if coverage > 0 and coverage < self.config["requirements"]["coverage_threshold"]:
                recommendations.append(f"Increase test coverage for {suite_name} (current: {coverage:.1f}%)")
        
        # Check execution time
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        if total_duration > self.config["requirements"]["max_execution_time"]:
            recommendations.append("Consider optimizing test execution time")
        
        # Check for critical failures
        critical_suites = ["unit", "integration", "security"]
        for suite in critical_suites:
            if suite in self.results and not self.results[suite].get("success", False):
                recommendations.append(f"Critical suite {suite} failed - must be fixed before deployment")
        
        if not recommendations:
            recommendations.append("All tests passed - ready for deployment")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """Save test report to file."""
        # Save JSON report
        json_report_path = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save human-readable report
        html_report = self._generate_html_report(report)
        html_report_path = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_report_path, 'w') as f:
            f.write(html_report)
        
        logger.info(f"Test report saved to {json_report_path} and {html_report_path}")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML test report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>EZBI Analytics Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .suite {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }}
        .recommendations {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EZBI Analytics Test Report</h1>
        <p><strong>Generated:</strong> {report['timestamp']}</p>
        <p><strong>Overall Status:</strong> 
            <span class="{'success' if report['overall_success'] else 'failure'}">
                {'✅ PASSED' if report['overall_success'] else '❌ FAILED'}
            </span>
        </p>
        <p><strong>Duration:</strong> {report['total_duration']:.2f} seconds</p>
    </div>
    
    <h2>Summary</h2>
    <div class="metric">
        <strong>Test Suites:</strong> {report['summary']['successful_suites']}/{report['summary']['total_suites']} passed
    </div>
    <div class="metric">
        <strong>Test Cases:</strong> {report['summary']['tests_passed']}/{report['summary']['total_tests']} passed
    </div>
    <div class="metric">
        <strong>Success Rate:</strong> {report['summary']['test_success_rate']:.1%}
    </div>
    
    <h2>Test Suite Results</h2>
"""
        
        for suite_name, result in report['suite_results'].items():
            status_class = "success" if result.get("success", False) else "failure"
            status_text = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            
            html += f"""
    <div class="suite">
        <h3>{suite_name} <span class="{status_class}">{status_text}</span></h3>
        <p><strong>Duration:</strong> {result.get('duration', 0):.2f}s</p>
        <p><strong>Tests:</strong> {result.get('tests_total', 0)} total, 
           {result.get('tests_passed', 0)} passed, 
           {result.get('tests_failed', 0)} failed, 
           {result.get('tests_skipped', 0)} skipped</p>
        {f"<p><strong>Coverage:</strong> {result.get('coverage_percentage', 0):.1f}%</p>" if result.get('coverage_percentage', 0) > 0 else ""}
        {f"<p><strong>Error:</strong> {result.get('error', '')}</p>" if result.get('error') else ""}
    </div>
"""
        
        html += f"""
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"""
        
        for rec in report['recommendations']:
            html += f"<li>{rec}</li>"
        
        html += """
        </ul>
    </div>
</body>
</html>
"""
        
        return html
    
    def send_notifications(self, report: Dict[str, Any]):
        """Send test result notifications."""
        if not self.config["notifications"]["email"] and not self.config["notifications"]["slack"]:
            return
        
        # This would implement notification sending
        # For now, just log the intent
        logger.info(f"Test results: {'PASSED' if report['overall_success'] else 'FAILED'}")
    
    def cleanup(self):
        """Clean up test artifacts."""
        # Remove temporary files, reset state, etc.
        logger.info("Cleaning up test artifacts...")
        
        # Clean up old reports (keep last 10)
        report_files = list(self.reports_dir.glob("test_report_*.json"))
        if len(report_files) > 10:
            report_files.sort(key=lambda f: f.stat().st_mtime)
            for old_file in report_files[:-10]:
                old_file.unlink()
        
        logger.info("Cleanup completed")


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(description="EZBI Analytics Test Automation Runner")
    
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "manufacturing", "security", "performance", "load_testing", "production_readiness", "all"],
        default="all",
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run independent test suites in parallel"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment, don't run tests"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old test artifacts"
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = TestAutomationRunner(args.config)
    
    try:
        # Validate environment
        if not runner.validate_environment():
            logger.error("Environment validation failed")
            sys.exit(1)
        
        if args.validate_only:
            logger.info("Environment validation passed")
            sys.exit(0)
        
        # Run tests
        if args.suite == "all":
            report = runner.run_all_tests(parallel_suites=args.parallel)
        else:
            result = runner.run_test_suite(args.suite)
            report = {
                "overall_success": result["success"],
                "suite_results": {args.suite: result}
            }
        
        # Send notifications
        runner.send_notifications(report)
        
        # Clean up if requested
        if args.cleanup:
            runner.cleanup()
        
        # Exit with appropriate code
        if report["overall_success"]:
            logger.info("All tests passed successfully")
            sys.exit(0)
        else:
            logger.error("Some tests failed")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()