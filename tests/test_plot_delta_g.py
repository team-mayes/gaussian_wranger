import unittest
import os
from nrel_tools.plot_delta_g import main
from nrel_tools.common import diff_lines, silent_remove, capture_stdout, capture_stderr
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.dirname(TEST_DIR)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'plot_delta_g')

FIVE_VALS_LIST = os.path.join(SUB_DATA_DIR, 'ester_list.txt')
FIVE_VALS_PLOT = os.path.join(SUB_DATA_DIR, 'ester_list.png')


class TestPlotDeltaGNoOut(unittest.TestCase):
    # These all test failure cases
    def testNoArgs(self):
        test_input = []
        # main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("A list of data" in output)

    def testHelp(self):
        test_input = ['-h']
        # main(test_input)
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testNoSuchFile(self):
        test_input = ["-l", "ghost.txt"]
        # main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No such file or directory" in output)


class TestPlotDeltaG(unittest.TestCase):
    # These test/demonstrate different options
    def testFiveVals(self):
        test_input = ["-l", FIVE_VALS_LIST, "-d", SUB_DATA_DIR, "-t", "460", "-c"]
        try:
            main(test_input)
            self.assertTrue(os.path.exists(FIVE_VALS_PLOT))
            # self.assertFalse(diff_lines(AE_OUT, GOOD_AE_OUT))
        finally:
            silent_remove(FIVE_VALS_PLOT, disable=DISABLE_REMOVE)
            pass