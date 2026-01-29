"""Tests for filtering modes: --last, --first, and --unpushed"""
import sys
import subprocess
import tempfile
import shutil
import datetime
from tests.test_base import GitfucktimeTestCase


class TestFilterModes(GitfucktimeTestCase):
    """Test different filtering modes for selective commit rewriting"""
    
    def test_last_n_commits(self):
        """Test --last N flag to rewrite only last N commits"""
        # Record dates of commits before rewrite
        log_before = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso"]
        ).decode("utf-8").strip().splitlines()
        
        # Rewrite only last 2 commits
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--last", "2", "--start", "2023-11-15", "--end", "2023-11-20"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify only 2 commits were rewritten
        log_after = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso"]
        ).decode("utf-8").strip().splitlines()
        
        # Last 2 commits should be different (in November)
        self.assertNotEqual(log_before[0], log_after[0])
        self.assertNotEqual(log_before[1], log_after[1])
        
        # Older commits should be unchanged
        self.assertEqual(log_before[2], log_after[2])
        self.assertEqual(log_before[3], log_after[3])

    def test_first_n_commits(self):
        """Test --first N flag to rewrite only first N commits"""
        # Record dates before rewrite
        log_before = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso", "--reverse"]
        ).decode("utf-8").strip().splitlines()
        
        # Rewrite only first 2 commits
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--first", "2", "--start", "2023-11-01", "--end", "2023-11-05"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify only first 2 commits were rewritten
        log_after = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso", "--reverse"]
        ).decode("utf-8").strip().splitlines()
        
        # First 2 commits should be different
        self.assertNotEqual(log_before[0], log_after[0])
        self.assertNotEqual(log_before[1], log_after[1])
        
        # Later commits should be unchanged
        self.assertEqual(log_before[2], log_after[2])

    def test_unpushed_mode_only_rewrites_unpushed(self):
        """Test that --unpushed mode only rewrites commits after origin/master"""
        # Create a bare remote repository
        remote_dir = tempfile.mkdtemp()
        subprocess.check_call(["git", "init", "--bare", remote_dir], stdout=subprocess.DEVNULL)
        
        # Add remote and push first 3 commits
        subprocess.check_call(["git", "remote", "add", "origin", remote_dir], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "branch", "-M", "master"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "push", "-u", "origin", "HEAD~2:refs/heads/master"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Now first 3 commits are pushed, last 2 are unpushed
        # Get dates before rewrite
        all_dates_before = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso-strict"]
        ).decode("utf-8").strip().splitlines()
        
        # Run unpushed mode
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--unpushed", "--start", "2023-12-01", "--end", "2023-12-05"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Get dates after rewrite
        all_dates_after = subprocess.check_output(
            ["git", "log", "--format=%cd", "--date=iso-strict"]
        ).decode("utf-8").strip().splitlines()
        
        # Last 2 commits (unpushed) should be different
        self.assertNotEqual(all_dates_before[0], all_dates_after[0])
        self.assertNotEqual(all_dates_before[1], all_dates_after[1])
        
        # First 3 commits (pushed) should be unchanged
        self.assertEqual(all_dates_before[2], all_dates_after[2])
        self.assertEqual(all_dates_before[3], all_dates_after[3])
        self.assertEqual(all_dates_before[4], all_dates_after[4])
        
        # Cleanup
        shutil.rmtree(remote_dir, ignore_errors=True)

    def test_auto_start_date_detection(self):
        """Test that start date is auto-detected from parent commit when using --last"""
        # Get the date of the 3rd commit from HEAD (which will be the parent after --last 2)
        parent_commit = subprocess.check_output(["git", "rev-parse", "HEAD~2"]).decode().strip()
        
        # Run with --last 2 (should auto-detect start date from parent)
        cmd = [sys.executable, "-m", "gitfucktime.main", "--last", "2"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify it worked
        log_out = subprocess.check_output(["git", "log", "--format=%cd", "--date=iso", "-2"]).decode("utf-8")
        dates = self.verify_work_hours(log_out)
        self.assertEqual(len(dates), 2)


if __name__ == '__main__':
    import unittest
    unittest.main()
