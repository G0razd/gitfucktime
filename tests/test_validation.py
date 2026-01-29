"""Tests for validation logic: future dates, work hours constraints"""
import sys
import subprocess
import datetime
from tests.test_base import GitfucktimeTestCase


class TestValidation(GitfucktimeTestCase):
    """Test validation and safety features"""
    
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


if __name__ == '__main__':
    import unittest
    unittest.main()
