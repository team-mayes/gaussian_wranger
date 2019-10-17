import unittest
import os
from gaussian_wrangler.pdbs2gausscoms import main
from common_wrangler.common import diff_lines, silent_remove, capture_stdout, capture_stderr
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
DISABLE_REMOVE = logger.isEnabledFor(logging.DEBUG)

__author__ = 'hmayes'

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.dirname(TEST_DIR)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
SUB_DATA_DIR = os.path.join(DATA_DIR, 'pdbs2gausscoms')

DEF_INI = os.path.join(SUB_DATA_DIR, 'pdb2gau.ini')
GAU_OUT1 = os.path.join(SUB_DATA_DIR, 'pet_mono_1.com')
GOOD_GAU_OUT1 = os.path.join(SUB_DATA_DIR, 'pet_mono_1_good.com')
GAU_OUT2 = os.path.join(SUB_DATA_DIR, 'pet_mono_2.com')
GOOD_GAU_OUT2 = os.path.join(SUB_DATA_DIR, 'pet_mono_2_good.com')
GAU_OUT3 = os.path.join(SUB_DATA_DIR, 'pet_mono_3.com')
GOOD_GAU_OUT3 = os.path.join(SUB_DATA_DIR, 'pet_mono_3_good.com')

REMOVE_H_INI = os.path.join(SUB_DATA_DIR, 'pdb2gau_h.ini')
REMOVE_H_OUT1 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_1.com')
GOOD_REMOVE_H_OUT1 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_1_good.com')
REMOVE_H_OUT2 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_2.com')
GOOD_REMOVE_H_OUT2 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_2_good.com')
REMOVE_H_OUT3 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_3.com')
GOOD_REMOVE_H_OUT3 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_3_good.com')

MULTI_FIRST_ONLY_INI = os.path.join(SUB_DATA_DIR, 'pdb2gau_multi.ini')
GOOD_KEEP_H_OUT1 = os.path.join(SUB_DATA_DIR, 'pet_mono_f1hs_1_with_good.com')

ALT_INI = os.path.join(SUB_DATA_DIR, 'pdb2gau_2.ini')
ALT_OUT = os.path.join(SUB_DATA_DIR, 'pe_linear.com')
GOOD_ALT_OUT = os.path.join(SUB_DATA_DIR, 'pe_linear_good.com')

MISSING_FILE_INI = os.path.join(SUB_DATA_DIR, 'pdb2gau_missing_file.ini')


class TestPdbs2GausscomsNoOut(unittest.TestCase):
    # These all test failure cases
    def testNoArgs(self):
        with capture_stderr(main, []) as output:
            self.assertTrue("Could not read" in output)
        with capture_stdout(main, []) as output:
            self.assertTrue("optional arguments" in output)

    def testHelp(self):
        test_input = ['-h']
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertFalse(output)
        with capture_stdout(main, test_input) as output:
            self.assertTrue("optional arguments" in output)

    def testMissingFile(self):
        test_input = ["-c", MISSING_FILE_INI]
        if logger.isEnabledFor(logging.DEBUG):
            main(test_input)
        with capture_stderr(main, test_input) as output:
            self.assertTrue("No such file" in output)

    def testAltIni(self):
        test_input = ["-t", 'tests/test_data/pdbs2gausscoms/gau_2.tpl', '-p', 'pe_linear.pdb']
        with capture_stderr(main, test_input) as output:
            self.assertTrue("pe_linear.pdb" in output)


class TestPdbs2Gausscoms(unittest.TestCase):
    # These test/demonstrate different options
    def testDefIni(self):
        test_input = ["-c", DEF_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(GAU_OUT1, GOOD_GAU_OUT1))
            self.assertFalse(diff_lines(GAU_OUT2, GOOD_GAU_OUT2))
            self.assertFalse(diff_lines(GAU_OUT3, GOOD_GAU_OUT3))
        finally:
            silent_remove(GAU_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GAU_OUT2, disable=DISABLE_REMOVE)
            silent_remove(GAU_OUT3, disable=DISABLE_REMOVE)

    def testCommandLineOptions(self):
        test_input = ["-t", "tests/test_data/pdbs2gausscoms/gau.tpl",
                      "-l", "tests/test_data/pdbs2gausscoms/pdb_list.txt"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(GAU_OUT1, GOOD_GAU_OUT1))
            self.assertFalse(diff_lines(GAU_OUT2, GOOD_GAU_OUT2))
            self.assertFalse(diff_lines(GAU_OUT3, GOOD_GAU_OUT3))
        finally:
            silent_remove(GAU_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GAU_OUT2, disable=DISABLE_REMOVE)
            silent_remove(GAU_OUT3, disable=DISABLE_REMOVE)

    def testRemoveH(self):
        test_input = ["-c", REMOVE_H_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(REMOVE_H_OUT1, GOOD_REMOVE_H_OUT1))
            self.assertFalse(diff_lines(REMOVE_H_OUT2, GOOD_REMOVE_H_OUT2))
            self.assertFalse(diff_lines(REMOVE_H_OUT3, GOOD_REMOVE_H_OUT3))
        finally:
            silent_remove(REMOVE_H_OUT1, disable=DISABLE_REMOVE)
            silent_remove(REMOVE_H_OUT2, disable=DISABLE_REMOVE)
            silent_remove(REMOVE_H_OUT3, disable=DISABLE_REMOVE)

    def testFirstOnly(self):
        test_input = ["-c", MULTI_FIRST_ONLY_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(REMOVE_H_OUT1, GOOD_KEEP_H_OUT1))
            self.assertFalse(diff_lines(GAU_OUT1, GOOD_GAU_OUT1))
        finally:
            silent_remove(REMOVE_H_OUT1, disable=DISABLE_REMOVE)
            silent_remove(GAU_OUT1, disable=DISABLE_REMOVE)

    def testAltIni(self):
        test_input = ["-c", ALT_INI]
        try:
            main(test_input)
            self.assertFalse(diff_lines(ALT_OUT, GOOD_ALT_OUT))
        finally:
            silent_remove(ALT_OUT, disable=DISABLE_REMOVE)
            pass

    def testAltIniCommandLine(self):
        # As ALT_INI, but command-line only
        test_input = ["-t", 'tests/test_data/pdbs2gausscoms/gau_2.tpl',
                      '-p', 'tests/test_data/pdbs2gausscoms/pe_linear.pdb']
        try:
            main(test_input)
            self.assertFalse(diff_lines(ALT_OUT, GOOD_ALT_OUT))
        finally:
            silent_remove(ALT_OUT, disable=DISABLE_REMOVE)
            pass

    def testRemoveHCommandLine(self):
        # As ALT_INI, but command-line only
        # make sure old files are cleaned up before starting
        for fname in [REMOVE_H_OUT1, REMOVE_H_OUT2, REMOVE_H_OUT3]:
            silent_remove(fname)

        test_input = ["-t", 'tests/test_data/pdbs2gausscoms/gau.tpl',
                      '-p', 'tests/test_data/pdbs2gausscoms/pet_mono_f1hs.pdb', "-r", "-a"]
        try:
            main(test_input)
            self.assertFalse(diff_lines(REMOVE_H_OUT1, GOOD_REMOVE_H_OUT1))
            self.assertFalse(os.path.isfile(REMOVE_H_OUT2))
            self.assertFalse(os.path.isfile(REMOVE_H_OUT3))
        finally:
            silent_remove(REMOVE_H_OUT1, disable=DISABLE_REMOVE)
            pass
