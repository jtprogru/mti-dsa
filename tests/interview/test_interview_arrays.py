import pytest

from tasks.interview.daily_temperatures import daily_temperatures
from tasks.interview.missing_number import missing_number
from tasks.interview.move_zeroes import move_zeroes
from tasks.interview.remove_duplicates import remove_duplicates
from tasks.interview.reverse_string import reverse_string
from tasks.interview.rotate_array import rotate
from tasks.interview.two_sum_sorted import two_sum_sorted


@pytest.mark.parametrize(
    "nums, expected",
    [
        ([0, 1, 2, 3, 5], 4),
        ([1, 2, 3, 4, 5], 0),
        ([0], 1),
        ([1], 0),
        ([0, 1], 2),
    ],
)
def test_missing_number(nums, expected):
    assert missing_number(nums) == expected


@pytest.mark.parametrize(
    "nums, expected_len, expected_head",
    [
        ([0, 1, 2, 3, 3, 5], 5, [0, 1, 2, 3, 5]),
        ([1, 1, 2], 2, [1, 2]),
        ([], 0, []),
        ([7], 1, [7]),
        ([2, 2, 2], 1, [2]),
    ],
)
def test_remove_duplicates(nums, expected_len, expected_head):
    assert remove_duplicates(nums) == expected_len
    assert nums == expected_head


@pytest.mark.parametrize(
    "nums, k, expected",
    [
        ([1, 2, 3, 4, 5, 6, 7], 3, [5, 6, 7, 1, 2, 3, 4]),
        ([1, 2], 0, [1, 2]),
        ([1, 2, 3], 3, [1, 2, 3]),
        ([1, 2, 3], 4, [3, 1, 2]),
        ([], 2, []),
    ],
)
def test_rotate(nums, k, expected):
    rotate(nums, k)
    assert nums == expected


@pytest.mark.parametrize(
    "a, k, expected",
    [
        ([-1, 2, 5, 8], 7, [-1, 8]),
        ([1, 2, 3, 4], 100, []),
        ([1, 2, 3, 4], 7, [3, 4]),
        ([], 5, []),
    ],
)
def test_two_sum_sorted(a, k, expected):
    assert two_sum_sorted(a, k) == expected


@pytest.mark.parametrize(
    "temps, expected",
    [
        ([13, 12, 15, 11, 9, 12, 16], [2, 1, 4, 2, 1, 1, 0]),
        ([30, 40, 50, 60], [1, 1, 1, 0]),
        ([30, 20, 10], [0, 0, 0]),
        ([], []),
    ],
)
def test_daily_temperatures(temps, expected):
    assert daily_temperatures(temps) == expected


@pytest.mark.parametrize(
    "nums, expected",
    [
        ([0, 1, 0, 3, 12], [1, 3, 12, 0, 0]),
        ([0], [0]),
        ([1, 2, 3], [1, 2, 3]),
        ([0, 0, 1], [1, 0, 0]),
    ],
)
def test_move_zeroes(nums, expected):
    move_zeroes(nums)
    assert nums == expected


@pytest.mark.parametrize(
    "chars, expected",
    [
        (["h", "e", "l", "l", "o"], ["o", "l", "l", "e", "h"]),
        (["H", "a", "n", "n", "a", "h"], ["h", "a", "n", "n", "a", "H"]),
        (["x"], ["x"]),
        ([], []),
    ],
)
def test_reverse_string(chars, expected):
    reverse_string(chars)
    assert chars == expected
