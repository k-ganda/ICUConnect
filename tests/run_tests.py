#!/usr/bin/env python3
"""
Test runner script for ICUConnect application.
This script ensures tests run with proper isolation and configuration.
"""

import os
import sys
import subprocess
import tempfile

def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    
    # Create a temporary directory for test databases
    temp_dir = tempfile.mkdtemp(prefix='icuconnect_test_')
    os.environ['TEST_DB_PATH'] = temp_dir
    
    return temp_dir

def run_tests():
    """Run the test suite."""
    print("Setting up test environment...")
    temp_dir = setup_test_environment()
    
    try:
        print("Running tests...")
        # Run pytest with specific options
        cmd = [
            sys.executable, '-m', 'pytest',
            '.',  # Run tests in current directory (tests folder)
            '-v',
            '--tb=short',
            '--disable-warnings',
            '--strict-markers'
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
        
    finally:
        # Cleanup
        print(f"Cleaning up test environment: {temp_dir}")
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up {temp_dir}: {e}")

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code) 