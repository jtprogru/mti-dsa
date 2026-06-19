import pytest

from tasks.interview.plus_one import plus_one
from tasks.interview.second_max import second_max
from tasks.interview.single_number import single_number


@pytest.mark.parametrize(
    "digits, expected",
    [
        ([1, 2, 3], [1, 2, 4]),
        ([1, 2, 9], [1, 3, 0]),
        ([9, 9], [1, 0, 0]),
        ([0], [1]),
        ([9], [1, 0]),
    ],
)
def test_plus_one(digits, expected):
    assert plus_one(digits) == expected


def test_plus_one_does_not_mutate_input():
    digits = [1, 2, 3]
    plus_one(digits)
    assert digits == [1, 2, 3]


@pytest.mark.parametrize(
    "nums, expected",
    [
        ([2, 2, 1], 1),
        ([4, 1, 2, 1, 2], 4),
        ([1], 1),
        ([7, 3, 3, 7, 9], 9),
    ],
)
def test_single_number(nums, expected):
    assert single_number(nums) == expected


@pytest.mark.parametrize(
    "arr, expected",
    [
        ([-2, 3, 0, 1, 5], 3),
        ([1, 1], None),
        ([5, 5, 4], 4),
        ([5, 4, 3], 4),
        ([1], None),
        ([], None),
        ([2, 2, 2], None),
        ([10, 9, 10], 9),
    ],
)
def test_second_max(arr, expected):
    assert second_max(arr) == expected
