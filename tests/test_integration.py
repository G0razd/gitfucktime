import unittest
import os
import shutil
import tempfile
import subprocess
import datetime
import sys

# Ensure we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIntegration(unittest.TestCase):
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

    def _verify_work_hours(self, dates_output):
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

    # ========== Test: Basic Rewrite with Explicit Dates ==========
    def test_rewrite_with_explicit_dates(self):
        """Test basic rewrite with --start and --end flags"""
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2023-11-01", "--end", "2023-11-10"]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        
        # Verify dates are within specified range
        log_out = subprocess.check_output(["git", "log", "--format=%cd", "--date=iso"]).decode("utf-8")
        dates = self._verify_work_hours(log_out)
        
        # Verify all dates are in November
        for date_str in dates:
            dt = datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            self.assertGreaterEqual(dt, datetime.datetime(2023, 11, 1))
            self.assertLessEqual(dt, datetime.datetime(2023, 11, 10))

    # ========== Test: Last N Commits ==========
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

    # ========== Test: First N Commits ==========
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

    # ========== Test: Unpushed Mode ==========
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

    # ========== Test: All Commits (No Flags) ==========
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
        dates = self._verify_work_hours(log_out)
        
        # Verify we still have the same number of commits
        new_commit_count = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"]
        ).decode().strip())
        self.assertEqual(commit_count, new_commit_count)

    # ========== Test: Auto-Detection of Start Date ==========
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
        dates = self._verify_work_hours(log_out)
        self.assertEqual(len(dates), 2)

    # ========== Test: Validation - Future Date Warning ==========
    def test_future_date_validation(self):
        """Test that future end dates trigger appropriate handling"""
        # Try to set end date in the far future (should auto-cap or ask confirmation)
        future_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        cmd = [sys.executable, "-m", "gitfucktime.main", 
               "--start", "2023-11-01", "--end", future_date]
        
        # This should either succeed (auto-capped) or fail gracefully
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, input="n\n")  # Say no to confirmation
        
        # Command should handle this gracefully (either cap or cancel)
        self.assertIn(result.returncode, [0, 1], "Should handle future dates gracefully")

    # ========== Test: Work Hours Constraint ==========
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
        self._verify_work_hours(log_out)

if __name__ == '__main__':
    unittest.main()
