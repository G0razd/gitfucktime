"""Tests for chronological ordering of rewritten commits"""
import sys
import subprocess
import datetime
import tempfile
import shutil
from tests.test_base import GitfucktimeTestCase


class TestChronologicalOrder(GitfucktimeTestCase):
    """Test that commits maintain proper chronological order after rewriting"""
    
    def test_last_n_chronological_order(self):
        """Test that --last N maintains chronological order"""
        # Run --last 3
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--last", "3", "--start", "2024-01-10", "--end", "2024-01-15"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Get all commits in chronological order (oldest first) using Unix timestamps
        log_out = subprocess.check_output(
            ["git", "log", "--format=%ct", "--reverse"]  # Unix timestamp
        ).decode("utf-8").strip().splitlines()
        
        # Parse timestamps
        timestamps = [int(ts) for ts in log_out]
        
        # Verify chronological order
        for i in range(1, len(timestamps)):
            self.assertGreaterEqual(timestamps[i], timestamps[i-1], 
                                  f"Date inversion: commit {i} is before commit {i-1}")

    def test_all_commits_chronological_order(self):
        """Test that default mode (all commits) maintains chronological order"""
        # Run default mode
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2024-02-01", "--end", "2024-02-10"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Get all commits in chronological order (oldest first) using Unix timestamps
        log_out = subprocess.check_output(
            ["git", "log", "--format=%ct", "--reverse"]  # Unix timestamp
        ).decode("utf-8").strip().splitlines()
        
        # Parse timestamps
        timestamps = [int(ts) for ts in log_out]
        
        # Verify chronological order
        for i in range(1, len(timestamps)):
            self.assertGreaterEqual(timestamps[i], timestamps[i-1], 
                                  f"Date inversion: commit {i} is before commit {i-1}")


if __name__ == '__main__':
    import unittest
    unittest.main()
