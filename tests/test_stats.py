"""Tests for StatsCollector."""

import unittest
from clawlayer.stats import StatsCollector


class TestStatsCollector(unittest.TestCase):
    """Test StatsCollector functionality."""
    
    def setUp(self):
        self.stats = StatsCollector(max_logs=10)
    
    def test_record_adds_log_with_id(self):
        """Test that record() adds log with auto-incrementing ID."""
        self.stats.record("test message", "greeting", 100.5)
        
        self.assertEqual(len(self.stats.logs), 1)
        self.assertEqual(self.stats.logs[0]['id'], 1)
        self.assertEqual(self.stats.logs[0]['message'], "test message")
        self.assertEqual(self.stats.logs[0]['router'], "greeting")
    
    def test_record_increments_id(self):
        """Test that IDs increment correctly."""
        self.stats.record("msg1", "router1", 100)
        self.stats.record("msg2", "router2", 200)
        self.stats.record("msg3", "router3", 300)
        
        self.assertEqual(self.stats.logs[0]['id'], 1)
        self.assertEqual(self.stats.logs[1]['id'], 2)
        self.assertEqual(self.stats.logs[2]['id'], 3)
    
    def test_delete_log_removes_entry(self):
        """Test that delete_log() removes the correct entry."""
        self.stats.record("msg1", "router1", 100)
        self.stats.record("msg2", "router2", 200)
        self.stats.record("msg3", "router3", 300)
        
        result = self.stats.delete_log(2)
        
        self.assertTrue(result)
        self.assertEqual(len(self.stats.logs), 2)
        self.assertEqual(self.stats.logs[0]['id'], 1)
        self.assertEqual(self.stats.logs[1]['id'], 3)
    
    def test_delete_log_returns_false_for_nonexistent(self):
        """Test that delete_log() returns False for non-existent ID."""
        self.stats.record("msg1", "router1", 100)
        
        result = self.stats.delete_log(999)
        
        self.assertFalse(result)
        self.assertEqual(len(self.stats.logs), 1)
    
    def test_delete_log_on_empty_logs(self):
        """Test delete_log() on empty logs."""
        result = self.stats.delete_log(1)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
