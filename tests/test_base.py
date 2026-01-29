"""Base test class and common test utilities for gitfucktime integration tests"""
import unittest
import os
import shutil
import tempfile
import subprocess
import datetime
import sys

# Ensure we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class GitfucktimeTestCase(unittest.TestCase):
    """Base test class with common setup/teardown and utilities"""
    
    def setUp(self):
        """Create a temporary git repository for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.pwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize a git repo
        subprocess.check_call(["git", "init"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "config", "user.name", "Test User"], stdout=subprocess.DEVNULL)

        # Create commits with "bad" dates (weekends/late night)
        self._create_test_commits()

    def _create_test_commits(self, num_commits=5):
        """Helper to create test commits with weekend/late night dates"""
        env = os.environ.copy()
        
        for i in range(num_commits):
            # Alternate between Saturday 3 AM and Sunday 11 PM
            if i % 2 == 0:
                bad_date = f"2023-10-{28 + (i // 2)}T03:00:00"  # Saturdays at 3 AM
            else:
                bad_date = f"2023-10-{29 + (i // 2)}T23:00:00"  # Sundays at 11 PM
                
            env["GIT_AUTHOR_DATE"] = bad_date
            env["GIT_COMMITTER_DATE"] = bad_date
            
            with open(f"file{i}.txt", "w") as f:
                f.write(f"content{i}")
            subprocess.check_call(["git", "add", f"file{i}.txt"], stdout=subprocess.DEVNULL)
            subprocess.check_call(["git", "commit", "-m", f"Commit {i}"], env=env, stdout=subprocess.DEVNULL)

    def tearDown(self):
        """Clean up temporary directory"""
        os.chdir(self.pwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def verify_work_hours(self, dates_output):
        """Verify all commits are in work hours (Mon-Fri, 9-17)"""
        dates = dates_output.strip().splitlines()
        
        for date_str in dates:
            # Parse date: "2023-10-30 14:12:33 +0100"
            dt = datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            
            # Check it's a weekday
            self.assertTrue(dt.weekday() < 5, f"Date {dt} is not a weekday")
            
            # Check time is work hours
            time_part = date_str.split()[1]
            hour = int(time_part.split(':')[0])
            self.assertTrue(9 <= hour <= 16, f"Hour {hour} is not between 9 and 16")
        
        return dates
