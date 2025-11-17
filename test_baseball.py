import unittest
from baseball import GameState


class TestBaseballRunnerPositions(unittest.TestCase):
    
    def setUp(self):
        self.state = GameState()
    
    def test_lead_runner_position_empty_bases(self):
        """Test lead runner position when no runners are on base"""
        self.state.bases = [False, False, False]
        self.assertEqual(self.state._leading_runner_position(), -1)
    
    def test_lead_runner_position_runner_on_first(self):
        """Test lead runner position when only runner is on first base"""
        self.state.bases = [True, False, False]
        self.assertEqual(self.state._leading_runner_position(), 0)
    
    def test_lead_runner_position_runner_on_second(self):
        """Test lead runner position when only runner is on second base"""
        self.state.bases = [False, True, False]
        self.assertEqual(self.state._leading_runner_position(), 1)
    
    def test_lead_runner_position_runner_on_third(self):
        """Test lead runner position when only runner is on third base"""
        self.state.bases = [False, False, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
    
    def test_lead_runner_position_runners_on_first_and_second(self):
        """Test lead runner position when runners are on first and second"""
        self.state.bases = [True, True, False]
        self.assertEqual(self.state._leading_runner_position(), 1)
    
    def test_lead_runner_position_runners_on_first_and_third(self):
        """Test lead runner position when runners are on first and third"""
        self.state.bases = [True, False, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
    
    def test_lead_runner_position_runners_on_second_and_third(self):
        """Test lead runner position when runners are on second and third"""
        self.state.bases = [False, True, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
    
    def test_lead_runner_position_bases_loaded(self):
        """Test lead runner position when bases are loaded"""
        self.state.bases = [True, True, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
    
    def test_leading_forced_runner_position_empty_bases(self):
        """Test leading forced runner position when no runners are on base"""
        self.state.bases = [False, False, False]
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
    
    def test_leading_forced_runner_position_runner_on_first_only(self):
        """Test leading forced runner position when only runner is on first"""
        self.state.bases = [True, False, False]
        self.assertEqual(self.state._leading_forced_runner_position(), 0)
    
    def test_leading_forced_runner_position_runner_on_second_only(self):
        """Test leading forced runner position when only runner is on second"""
        self.state.bases = [False, True, False]
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
    
    def test_leading_forced_runner_position_runner_on_third_only(self):
        """Test leading forced runner position when only runner is on third"""
        self.state.bases = [False, False, True]
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
    
    def test_leading_forced_runner_position_runners_on_first_and_second(self):
        """Test leading forced runner position when runners are on first and second"""
        self.state.bases = [True, True, False]
        self.assertEqual(self.state._leading_forced_runner_position(), 1)
    
    def test_leading_forced_runner_position_runners_on_first_and_third(self):
        """Test leading forced runner position when runners are on first and third"""
        self.state.bases = [True, False, True]
        self.assertEqual(self.state._leading_forced_runner_position(), 0)
    
    def test_leading_forced_runner_position_runners_on_second_and_third(self):
        """Test leading forced runner position when runners are on second and third"""
        self.state.bases = [False, True, True]
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
    
    def test_leading_forced_runner_position_bases_loaded(self):
        """Test leading forced runner position when bases are loaded"""
        self.state.bases = [True, True, True]
        self.assertEqual(self.state._leading_forced_runner_position(), 2)
    
    def test_lead_vs_forced_runner_comparisons(self):
        """Test scenarios where lead and forced runners differ"""
        # Runner on second only - lead runner is on second, but no forced runner
        self.state.bases = [False, True, False]
        self.assertEqual(self.state._leading_runner_position(), 1)
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
        
        # Runner on third only - lead runner is on third, but no forced runner
        self.state.bases = [False, False, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
        self.assertEqual(self.state._leading_forced_runner_position(), -1)
        
        # Runners on first and third - lead runner is on third, forced runner is on first
        self.state.bases = [True, False, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
        self.assertEqual(self.state._leading_forced_runner_position(), 0)
        
        # Runners on second and third - lead runner is on third, but no forced runner
        self.state.bases = [False, True, True]
        self.assertEqual(self.state._leading_runner_position(), 2)
        self.assertEqual(self.state._leading_forced_runner_position(), -1)


if __name__ == '__main__':
    unittest.main()
