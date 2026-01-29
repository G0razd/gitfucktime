import unittest
from unittest.mock import MagicMock, patch
import sys
from gitfucktime.ui import display_commit_history

class TestUI(unittest.TestCase):
    
    @patch('gitfucktime.ui.Pager')
    @patch('gitfucktime.ui.GeneratorSource')
    @patch('gitfucktime.ui.console')
    def test_display_commit_history_with_commits(self, mock_console, mock_gen_source, mock_pager_cls):
        """Test that display_commit_history sets up the pager correctly when commits exist."""
        # Setup mocks
        mock_pager_instance = mock_pager_cls.return_value
        
        # Test data
        commits = [
            {
                'hash': 'abcdef1234567890',
                'date': '2023-01-01 12:00:00',
                'relative_date': '2 days ago',
                'author': 'Tester',
                'message': 'Test commit'
            }
        ]
        
        # Execute
        display_commit_history(commits)
        
        # Verify
        # Verify Pager and GeneratorSource were initialized
        mock_pager_cls.assert_called_once()
        mock_gen_source.assert_called_once()
        mock_pager_instance.add_source.assert_called_once()
        mock_pager_instance.run.assert_called_once()
        
        # Get the generator passed to GeneratorSource
        args, _ = mock_gen_source.call_args
        generator = args[0]
        
        # Consume the generator to trigger the internal logic (console.print)
        next(generator)
        
        # Now verify console.print was called
        mock_console.print.assert_called()
        mock_console.capture.assert_called()

    @patch('gitfucktime.ui.console')
    def test_display_commit_history_no_commits(self, mock_console):
        """Test that display_commit_history handles empty commit list."""
        display_commit_history([])
        
        # Should just print a message and return, no pager involvement
        mock_console.print.assert_called_with("[yellow]No commits found.[/yellow]")

if __name__ == '__main__':
    unittest.main()
