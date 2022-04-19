"""
[Insert description]
"""

import pytest

__author__ = "[Insert your name here]"

# You are welcome to use a different format for your pytest testing; this is
# just a suggested way to do it. Something that you *must* keep with your
# testing, however, is the timeout decorator: "@pytest.mark.timeout(1)".

test_cases = [
    # Insert test cases here.
]


@pytest.mark.timeout(1)
@pytest.mark.parametrize("test_case", test_cases)
def test_function_name(test_case):
    pass
