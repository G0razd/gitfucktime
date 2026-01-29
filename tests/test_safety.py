import sys
import os
import shutil
import subprocess
import unittest
from tests.test_base import GitfucktimeTestCase

class TestSafetyFeatures(GitfucktimeTestCase):
    
    def test_backup_creation(self):
        """Test that a backup branch is created by default."""
        # 1. Run gitfucktime
        cmd = [sys.executable, "-m", "gitfucktime.main", "--last", "1", "--start", "2024-01-01"]
        # Use existing checkout
        subprocess.check_call(cmd)
        
        # 2. Check branches
        branches = subprocess.check_output(["git", "branch"]).decode("utf-8")
        self.assertIn("gitfucktime-backup-", branches)

    def test_no_backup_flag(self):
        """Test that --no-backup prevents backup branch creation."""
        cmd = [sys.executable, "-m", "gitfucktime.main", "--last", "1", "--start", "2024-01-01", "--no-backup"]
        subprocess.check_call(cmd)
        
        branches = subprocess.check_output(["git", "branch"]).decode("utf-8")
        self.assertNotIn("gitfucktime-backup-", branches)

    def test_revert_functionality(self):
        """Test the revert feature."""
        # 1. Get initial commit hash
        initial_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        
        # 2. Run rewrite
        cmd = [sys.executable, "-m", "gitfucktime.main", "--last", "1", "--start", "2024-01-01"]
        subprocess.check_call(cmd)
        
        # 3. Verify hash changed
        new_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        self.assertNotEqual(initial_hash, new_hash)
        
        # 4. Run revert
        cmd_revert = [sys.executable, "-m", "gitfucktime.main", "--revert"]
        subprocess.check_call(cmd_revert)
        
        # 5. Verify hash is back to initial (or equivalent content/tree)
        reverted_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        self.assertEqual(initial_hash, reverted_hash)
        
        # 6. Check that revert also created a backup (backup of the rewritten state)
        branches = subprocess.check_output(["git", "branch"]).decode("utf-8")
        # Should have at least 2 backups now (one from first run, one from revert)
        self.assertTrue(branches.count("gitfucktime-backup-") >= 2)

    def test_revert_no_backup(self):
        """Test revert with --no-backup."""
        # Run rewrite
        subprocess.check_call([sys.executable, "-m", "gitfucktime.main", "--last", "1", "--start", "2024-01-01"])
        
        # Get count of backups
        branches_before = subprocess.check_output(["git", "branch"]).decode("utf-8")
        count_before = branches_before.count("gitfucktime-backup-")
        
        # Run revert no backup
        subprocess.check_call([sys.executable, "-m", "gitfucktime.main", "--revert", "--no-backup"])
        
        # Verify count didn't increase
        branches_after = subprocess.check_output(["git", "branch"]).decode("utf-8")
        count_after = branches_after.count("gitfucktime-backup-")
        
        self.assertEqual(count_before, count_after)

if __name__ == '__main__':
    unittest.main()
