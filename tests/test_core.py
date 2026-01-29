import unittest
import datetime
from gitfucktime.utils import get_next_work_day, is_work_day, generate_work_hours_timestamp
from gitfucktime.core import get_repo_stats

class TestUtils(unittest.TestCase):
    def test_is_work_day(self):
        # Mon (0) to Fri (4) should be True
        self.assertTrue(is_work_day(datetime.datetime(2023, 10, 23))) # Mon
        self.assertTrue(is_work_day(datetime.datetime(2023, 10, 27))) # Fri
        
        # Sat (5) and Sun (6) should be False
        self.assertFalse(is_work_day(datetime.datetime(2023, 10, 28))) # Sat
        self.assertFalse(is_work_day(datetime.datetime(2023, 10, 29))) # Sun

    def test_get_next_work_day(self):
        # Friday -> Monday
        fri = datetime.datetime(2023, 10, 27)
        mon = datetime.datetime(2023, 10, 30)
        self.assertEqual(get_next_work_day(fri), mon)
        
        # Monday -> Tuesday
        tue = datetime.datetime(2023, 10, 24)
        next_day = get_next_work_day(datetime.datetime(2023, 10, 23)) # Mon
        self.assertEqual(next_day, tue)

    def test_generate_work_hours_timestamp(self):
        start = datetime.datetime(2023, 10, 23)
        end = datetime.datetime(2023, 10, 27)
        
        for _ in range(100):
            ts = generate_work_hours_timestamp(start, end)
            self.assertTrue(9 <= ts.hour <= 16) # 9am to 4:59pm (executes till 17:00? No, 16:59 is fine)
            # logic says hour = random.randint(9, 16) -> 09:xx to 16:xx. 
            self.assertTrue(ts.weekday() < 5)

if __name__ == '__main__':
    unittest.main()
