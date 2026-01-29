"""Tests for basic rewrite functionality with explicit date ranges"""
import sys
import subprocess
import datetime
from tests.test_base import GitfucktimeTestCase


class TestBasicRewrite(GitfucktimeTestCase):
    """Test basic commit rewriting with explicit date ranges"""
    
    def test_rewrite_with_explicit_dates(self):
        """Test basic rewrite with --start and --end flags"""
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2023-11-01", "--end", "2023-11-10"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify dates are within specified range
        log_out = subprocess.check_output(["git", "log", "--format=%cd", "--date=iso"]).decode("utf-8")
        dates = self.verify_work_hours(log_out)
        
        # Verify all dates are in November
        for date_str in dates:
            dt = datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            self.assertGreaterEqual(dt, datetime.datetime(2023, 11, 1))
            self.assertLessEqual(dt, datetime.datetime(2023, 11, 10))

    def test_all_commits_default_mode(self):
        """Test default mode rewrites all commits"""
        # Count commits before
        commit_count = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"]
        ).decode().strip())
        
        # Rewrite all commits
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2023-12-10", "--end", "2023-12-20"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify all commits are in work hours
        log_out = subprocess.check_output(["git", "log", "--format=%cd", "--date=iso"]).decode("utf-8")
        dates = self.verify_work_hours(log_out)
        
        # Verify we still have the same number of commits
        new_commit_count = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"]
        ).decode().strip())
        self.assertEqual(commit_count, new_commit_count)

    def test_all_commits_within_work_hours(self):
        """Comprehensive test that ALL rewritten commits are Mon-Fri 9-17"""
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2023-11-01", "--end", "2023-11-30"]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Get full log with ISO format
        log_out = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso"]
        ).decode("utf-8")
        
        # Verify every single commit
        self.verify_work_hours(log_out)


if __name__ == '__main__':
    import unittest
    unittest.main()
