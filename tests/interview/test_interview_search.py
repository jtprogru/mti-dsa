import pytest

from tasks.interview.common_in_three import common_in_three
from tasks.interview.k_closest import k_closest


@pytest.mark.parametrize(
    "a, b, c, expected",
    [
        ([1, 2, 3, 4, 5, 100], [6, 7, 8, 9, 100], [10, 20, 21, 22, 23, 24, 100], 100),
        ([1, 5, 10], [5], [3, 5, 7], 5),
        ([1, 2], [3, 4], [5, 6], None),
        ([], [1], [1], None),
    ],
)
def test_common_in_three(a, b, c, expected):
    assert common_in_three(a, b, c) == expected


@pytest.mark.parametrize(
    "a, idx, k, expected",
    [
        ([10, 15, 20, 50, 55, 78, 91], 2, 3, [10, 15, 50]),
        ([1, 2, 3, 4, 5], 0, 2, [2, 3]),
        ([1, 2, 3, 4, 5], 4, 2, [3, 4]),
        ([1, 2, 3, 4, 5], 2, 4, [1, 2, 4, 5]),
    ],
)
def test_k_closest(a, idx, k, expected):
    assert k_closest(a, idx, k) == expected
