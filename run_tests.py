import unittest
import sys

# Import all test modules
from tests.test_game_objects import *
from tests.test_game import *
from tests.test_game_interface import *

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all tests from each module
    suite.addTests(loader.loadTestsFromModule(sys.modules[__name__]))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite) 