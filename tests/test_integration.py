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
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.pwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize a git repo
        subprocess.check_call(["git", "init"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "config", "user.email", "test@example.com"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "config", "user.name", "Test User"], stdout=subprocess.DEVNULL)

        # Create some commits with "bad" dates (e.g. weekends or late night)
        # We'll validly set dates using GIT_AUTHOR_DATE/GIT_COMMITTER_DATE
        
        # Commit 1: Saturday 3 AM
        env = os.environ.copy()
        bad_date = "2023-10-28T03:00:00"
        env["GIT_AUTHOR_DATE"] = bad_date
        env["GIT_COMMITTER_DATE"] = bad_date
        
        with open("file1.txt", "w") as f: f.write("content1")
        subprocess.check_call(["git", "add", "file1.txt"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "commit", "-m", "Commit 1"], env=env, stdout=subprocess.DEVNULL)

        # Commit 2: Sunday 11 PM
        bad_date_2 = "2023-10-29T23:00:00"
        env["GIT_AUTHOR_DATE"] = bad_date_2
        env["GIT_COMMITTER_DATE"] = bad_date_2
        
        with open("file2.txt", "w") as f: f.write("content2")
        subprocess.check_call(["git", "add", "file2.txt"], stdout=subprocess.DEVNULL)
        subprocess.check_call(["git", "commit", "-m", "Commit 2"], env=env, stdout=subprocess.DEVNULL)

    def tearDown(self):
        os.chdir(self.pwd)
        # Use simple ignore_errors to avoid issues with readonly git files on windows
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_rewrite_history(self):
        # Run gitfucktime
        # We will use the module execution
        try:
            # Running with --start and --end covering these dates?
            # Actually, let's just use --last 2 to rewrite them.
            # We must provide --start and --end or rely on auto-detection.
            # Let's force start/end to be next week (Mon-Fri)
            
            cmd = [sys.executable, "-m", "gitfucktime.main", "--start", "2023-10-30", "--end", "2023-11-03"]
            
            # Since our script might fail if not installed or python path issue, we rely on the sys.path insert above
            # checking call directly
            
            # Note: windows requires generated script execution, so allow it time
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            # Verify Dates
            log_out = subprocess.check_output(["git", "log", "--format=%cd", "--date=iso"]).decode("utf-8")
            
            dates = log_out.strip().splitlines()
            self.assertEqual(len(dates), 2)
            
            for date_str in dates:
                # Format: 2023-10-30 14:12:33 +0100
                dt = datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                
                # Assert it IS NOT the weekend (Sat/Sun)
                # 2023-10-30 is Monday. 2023-10-28/29 were Sat/Sun.
                self.assertTrue(dt.weekday() < 5, f"Date {dt} is not a weekday")
                
                # Assert time is between 09:00 and 17:00
                # We need to parse the full time string to get hour
                # git log iso format: YYYY-MM-DD HH:MM:SS +/-TZ
                time_part = date_str.split()[1]
                hour = int(time_part.split(':')[0])
                self.assertTrue(9 <= hour <= 16, f"Hour {hour} is not between 9 and 16")

        except subprocess.CalledProcessError as e:
            self.fail(f"Tool execution failed: {e}")

    def test_unpushed_mode_only_rewrites_unpushed(self):
        """Test that --unpushed mode only rewrites commits after origin/master, not entire history"""
        try:
            # Create a "remote" bare repository
            remote_dir = tempfile.mkdtemp()
            subprocess.check_call(["git", "init", "--bare", remote_dir], stdout=subprocess.DEVNULL)
            
            # Add remote and push ONLY the first commit
            subprocess.check_call(["git", "remote", "add", "origin", remote_dir], stdout=subprocess.DEVNULL)
            subprocess.check_call(["git", "branch", "-M", "master"], stdout=subprocess.DEVNULL)
            subprocess.check_call(["git", "push", "-u", "origin", "HEAD~1:refs/heads/master"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Now HEAD~1 is pushed, HEAD is unpushed
            # Get dates before rewrite
            first_commit_date_before = subprocess.check_output(
                ["git", "show", "-s", "--format=%cd", "--date=iso-strict", "HEAD~1"]
            ).decode("utf-8").strip()
            
            second_commit_date_before = subprocess.check_output(
                ["git", "show", "-s", "--format=%cd", "--date=iso-strict", "HEAD"]
            ).decode("utf-8").strip()
            
            print(f"\nBefore rewrite:")
            print(f"  First commit (pushed):   {first_commit_date_before}")
            print(f"  Second commit (unpushed): {second_commit_date_before}")
            
            # Run gitfucktime in unpushed mode
            cmd = [sys.executable, "-m", "gitfucktime.main", "--unpushed", "--start", "2023-11-01", "--end", "2023-11-03"]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"\nGitfucktime output:\n{result.stdout}\n{result.stderr}")
            
            # Get dates after rewrite
            first_commit_date_after = subprocess.check_output(
                ["git", "show", "-s", "--format=%cd", "--date=iso-strict", "HEAD~1"]
            ).decode("utf-8").strip()
            
            second_commit_date_after = subprocess.check_output(
                ["git", "show", "-s", "--format=%cd", "--date=iso-strict", "HEAD"]
            ).decode("utf-8").strip()
            
            print(f"\nAfter rewrite:")
            print(f"  First commit (pushed):   {first_commit_date_after}")
            print(f"  Second commit (unpushed): {second_commit_date_after}")
            
            # Verify: First commit should have the SAME date (not rewritten)
            self.assertEqual(first_commit_date_before, first_commit_date_after,
                           "First (pushed) commit date should NOT have changed in --unpushed mode")
            
            # Verify: Second commit should have a DIFFERENT date (rewritten)
            self.assertNotEqual(second_commit_date_before, second_commit_date_after,
                              "Second (unpushed) commit date SHOULD have changed")
            
            # Verify second commit is now in the correct date range
            second_dt = datetime.datetime.fromisoformat(second_commit_date_after.replace('+', ' +').split()[0])
            self.assertGreaterEqual(second_dt.date(), datetime.date(2023, 11, 1))
            self.assertLessEqual(second_dt.date(), datetime.date(2023, 11, 3))
            
            # Cleanup remote
            shutil.rmtree(remote_dir, ignore_errors=True)
            
        except subprocess.CalledProcessError as e:
            print(f"\nSubprocess error: {e}")
            print(f"Output: {e.output if hasattr(e, 'output') else 'N/A'}")
            self.fail(f"Unpushed mode test failed: {e}")

if __name__ == '__main__':
    unittest.main()
