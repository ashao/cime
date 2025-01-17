#!/usr/bin/env python3

import os
import sys

import unittest
from unittest import mock
from CIME.utils import indent_string, run_and_log_case_status

from . import utils

class TestIndentStr(unittest.TestCase):
    """Test the indent_string function.

    """

    def test_indent_string_singleline(self):
        """Test the indent_string function with a single-line string

        """
        mystr = 'foo'
        result = indent_string(mystr, 4)
        expected = '    foo'
        self.assertEqual(expected, result)

    def test_indent_string_multiline(self):
        """Test the indent_string function with a multi-line string

        """
        mystr = """hello
hi
goodbye
"""
        result = indent_string(mystr, 2)
        expected = """  hello
  hi
  goodbye
"""
        self.assertEqual(expected, result)

class MockTime(object):
    def __init__(self):
        self._old = None

    def __enter__(self):
        self._old = getattr(sys.modules["time"], "strftime")
        setattr(sys.modules["time"], "strftime", lambda *args: "00:00:00 ")

    def __exit__(self, *args, **kwargs):
        setattr(sys.modules["time"], "strftime", self._old)

def match_all_lines(data, lines):
    for line in data:
        for i, x in enumerate(lines):
            if x == line:
                lines.pop(i)

                continue

        if len(lines) == 0:
            return True, []

    return False, lines

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.base_func = lambda *args: None

        def _error_func(*args):
            raise Exception("Something went wrong")

        self.error_func = _error_func

    def assertMatchAllLines(self, tempdir, test_lines):
        with open(os.path.join(tempdir, "CaseStatus")) as fd:
            data = fd.readlines()

        result, missing = match_all_lines(data, test_lines)

        error = []

        if len(missing) != 0:
            error.extend(["Missing Lines", ""])
            error.extend([x.rstrip("\n") for x in missing])
            error.extend(["", "Tempfile contents", ""])
            error.extend([x.rstrip("\n") for x in data])

        self.assertTrue(result, msg="\n".join(error))

    def test_run_and_log_case_status(self):
        test_lines = [
            "00:00:00 default starting \n",
            "00:00:00 default success \n",
        ]

        with utils.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(self.base_func, "default",
                                    caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_on_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit success \n",
        ]

        with utils.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(self.base_func, "case.submit",
                                    caseroot=tempdir, is_batch=True)

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_no_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit success \n",
        ]

        with utils.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(self.base_func, "case.submit",
                                    caseroot=tempdir, is_batch=False)

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_case_submit_error_on_batch(self):
        test_lines = [
            "00:00:00 case.submit starting \n",
            "00:00:00 case.submit error \n",
            "Something went wrong\n",
        ]

        with utils.TemporaryDirectory() as tempdir, MockTime():
            with self.assertRaises(Exception):
                run_and_log_case_status(self.error_func, "case.submit",
                                        caseroot=tempdir, is_batch=True)

            self.assertMatchAllLines(tempdir, test_lines)

    def test_run_and_log_case_status_custom_msg(self):
        test_lines = [
            "00:00:00 default starting starting extra\n",
            "00:00:00 default success success extra\n",
        ]

        starting_func = mock.MagicMock(return_value="starting extra")
        success_func = mock.MagicMock(return_value="success extra")

        def normal_func():
            return "data"

        with utils.TemporaryDirectory() as tempdir, MockTime():
            run_and_log_case_status(normal_func, "default",
                                    custom_starting_msg_functor=starting_func,
                                    custom_success_msg_functor=success_func,
                                    caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)

        starting_func.assert_called_with()
        success_func.assert_called_with("data")

    def test_run_and_log_case_status_custom_msg_error_on_batch(self):
        test_lines = [
            "00:00:00 default starting starting extra\n",
            "00:00:00 default success success extra\n",
        ]

        starting_func = mock.MagicMock(return_value="starting extra")
        success_func = mock.MagicMock(return_value="success extra")

        def error_func():
            raise Exception("Error")

        with utils.TemporaryDirectory() as tempdir, MockTime(), \
                self.assertRaises(Exception):
            run_and_log_case_status(error_func, "default",
                                    custom_starting_msg_functor=starting_func,
                                    custom_success_msg_functor=success_func,
                                    caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)

        starting_func.assert_called_with()
        success_func.assert_not_called()

    def test_run_and_log_case_status_error(self):
        test_lines = [
            "00:00:00 default starting \n",
            "00:00:00 default error \n",
            "Something went wrong\n",
        ]

        with utils.TemporaryDirectory() as tempdir, MockTime():
            with self.assertRaises(Exception):
                run_and_log_case_status(self.error_func, "default",
                                        caseroot=tempdir)

            self.assertMatchAllLines(tempdir, test_lines)

if __name__ == '__main__':
    unittest.main()

