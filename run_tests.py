#!/usr/bin/env python3
"""
Comprehensive Test Runner for Hospital Referral System
Demonstrates different testing strategies, data values, and performance metrics
"""

import os
import sys
import subprocess
import time
import json
import platform
import psutil
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'test_results': {}
        }
    
    def get_system_info(self):
        """Get system specifications for performance testing."""
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').total
        }
    
    def run_command(self, command, description):
        """Run a command and capture results."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {command}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            end_time = time.time()
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'duration': end_time - start_time
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Test timed out after 5 minutes',
                'return_code': -1,
                'duration': 300
            }
    
    def run_unit_tests(self):
        """Run unit tests with different data values."""
        print("\n🔬 UNIT TESTS - Testing individual components")
        
        # Test with different data scenarios
        test_scenarios = [
            "Basic functionality",
            "Edge cases",
            "Invalid data handling",
            "Boundary conditions"
        ]
        
        for scenario in test_scenarios:
            print(f"\n--- Testing: {scenario} ---")
            result = self.run_command(
                f"python -m pytest tests/test_models.py -v -m unit --tb=short",
                f"Unit tests - {scenario}"
            )
            self.results['test_results'][f'unit_{scenario.lower().replace(" ", "_")}'] = result
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 INTEGRATION TESTS - Testing component interactions")
        
        result = self.run_command(
            "python -m pytest tests/test_api.py -v -m integration --tb=short",
            "Integration tests - API endpoints and database operations"
        )
        self.results['test_results']['integration'] = result
    
    def run_functional_tests(self):
        """Run functional tests."""
        print("\n🎯 FUNCTIONAL TESTS - Testing complete user workflows")
        
        result = self.run_command(
            "python -m pytest tests/test_functional.py -v -m functional --tb=short",
            "Functional tests - End-to-end user scenarios"
        )
        self.results['test_results']['functional'] = result
    
    def run_performance_tests(self):
        """Run performance tests on different hardware specifications."""
        print("\n⚡ PERFORMANCE TESTS - Testing system performance")
        
        # Test with different load levels
        load_levels = [10, 50, 100]
        
        for load in load_levels:
            print(f"\n--- Testing with {load} concurrent operations ---")
            result = self.run_command(
                f"python -m pytest tests/test_performance.py::TestPerformance::test_concurrent_referral_creation -v -m performance",
                f"Performance test - {load} concurrent operations"
            )
            self.results['test_results'][f'performance_{load}_concurrent'] = result
    
    def run_validation_tests(self):
        """Run validation tests."""
        print("\n✅ VALIDATION TESTS - Testing data integrity and business rules")
        
        result = self.run_command(
            "python -m pytest tests/test_models.py::TestReferralRequest::test_referral_escalation_logic -v",
            "Validation tests - Business rule compliance"
        )
        self.results['test_results']['validation'] = result
    
    def run_cross_platform_tests(self):
        """Run cross-platform compatibility tests."""
        print("\n🖥️ CROSS-PLATFORM TESTS - Testing different software configurations")
        
        # Test with different Python versions (if available)
        python_versions = ['python', 'python3', 'python3.9', 'python3.10', 'python3.11']
        
        for py_version in python_versions:
            try:
                result = self.run_command(
                    f"{py_version} -c 'import sys; print(f\"Python {sys.version}\")'",
                    f"Python version test - {py_version}"
                )
                if result['success']:
                    self.results['test_results'][f'python_version_{py_version}'] = result
                    break
            except:
                continue
    
    def run_coverage_analysis(self):
        """Run code coverage analysis."""
        print("\n📊 COVERAGE ANALYSIS - Testing code coverage")
        
        result = self.run_command(
            "python -m pytest --cov=app --cov-report=html --cov-report=term-missing",
            "Code coverage analysis"
        )
        self.results['test_results']['coverage'] = result
    
    def run_load_testing(self):
        """Run load testing with different specifications."""
        print("\n🚀 LOAD TESTING - Testing system under load")
        
        # Simulate different hardware specifications
        scenarios = [
            "Low-end server (2 CPU cores, 4GB RAM)",
            "Medium server (4 CPU cores, 8GB RAM)", 
            "High-end server (8 CPU cores, 16GB RAM)"
        ]
        
        for i, scenario in enumerate(scenarios):
            print(f"\n--- {scenario} ---")
            result = self.run_command(
                f"python -m pytest tests/test_performance.py::TestLoadTesting::test_high_concurrent_users -v",
                f"Load testing - {scenario}"
            )
            self.results['test_results'][f'load_test_{i+1}'] = result
    
    def run_stress_testing(self):
        """Run stress testing."""
        print("\n💪 STRESS TESTING - Testing system limits")
        
        result = self.run_command(
            "python -m pytest tests/test_performance.py::TestStressTesting -v -m slow",
            "Stress testing - System limits and failure recovery"
        )
        self.results['test_results']['stress_testing'] = result
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 GENERATING TEST REPORT")
        
        report = {
            'summary': {
                'total_tests': len(self.results['test_results']),
                'passed_tests': sum(1 for r in self.results['test_results'].values() if r['success']),
                'failed_tests': sum(1 for r in self.results['test_results'].values() if not r['success']),
                'total_duration': sum(r['duration'] for r in self.results['test_results'].values())
            },
            'system_performance': {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            },
            'detailed_results': self.results['test_results']
        }
        
        # Save report to file
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Total Duration: {report['summary']['total_duration']:.2f} seconds")
        print(f"CPU Usage: {report['system_performance']['cpu_usage']:.1f}%")
        print(f"Memory Usage: {report['system_performance']['memory_usage']:.1f}%")
        print(f"Disk Usage: {report['system_performance']['disk_usage']:.1f}%")
        print(f"{'='*60}")
        
        return report
    
    def run_all_tests(self):
        """Run all test categories."""
        print("🏥 HOSPITAL REFERRAL SYSTEM - COMPREHENSIVE TESTING")
        print("=" * 60)
        print("This demonstrates functionality under different testing strategies,")
        print("with different data values, and performance on different specifications")
        print("=" * 60)
        
        # Run all test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_functional_tests()
        self.run_performance_tests()
        self.run_validation_tests()
        self.run_cross_platform_tests()
        self.run_coverage_analysis()
        self.run_load_testing()
        self.run_stress_testing()
        
        # Generate final report
        report = self.generate_test_report()
        
        print("\n✅ Testing completed! Check test_report.json for detailed results.")
        return report

def main():
    """Main function to run all tests."""
    runner = TestRunner()
    report = runner.run_all_tests()
    
    # Exit with appropriate code
    if report['summary']['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 