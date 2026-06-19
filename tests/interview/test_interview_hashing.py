import pytest

from tasks.interview.array_intersection import array_intersection
from tasks.interview.contains_duplicate import contains_duplicate
from tasks.interview.first_unique_char import first_unique_char
from tasks.interview.max_consecutive_repeats import max_consecutive_repeats
from tasks.interview.two_sum import two_sum
from tasks.interview.valid_anagram import is_anagram


@pytest.mark.parametrize(
    "nums, expected",
    [
        ([0, 1, 2, 3, 3, 5], True),
        ([0, 1, 2, 3], False),
        ([1, 1], True),
        ([], False),
        ([42], False),
    ],
)
def test_contains_duplicate(nums, expected):
    assert contains_duplicate(nums) == expected


@pytest.mark.parametrize(
    "nums, target, expected",
    [
        ([2, 7, 11, 15], 9, [0, 1]),
        ([3, 2, 4], 6, [1, 2]),
        ([3, 3], 6, [0, 1]),
        ([1, 2, 3], 100, []),
    ],
)
def test_two_sum(nums, target, expected):
    assert two_sum(nums, target) == expected


@pytest.mark.parametrize(
    "nums1, nums2, expected",
    [
        ([1, 2, 2, 1], [2, 2], [2, 2]),
        ([4, 9, 5], [9, 4, 9, 8, 4], [4, 9]),
        ([1, 2, 3], [4, 5], []),
        ([], [1, 2], []),
    ],
)
def test_array_intersection(nums1, nums2, expected):
    # Порядок результата не специфицирован — сравниваем как мультимножества.
    assert sorted(array_intersection(nums1, nums2)) == sorted(expected)


@pytest.mark.parametrize(
    "s, expected",
    [
        ("leetcode", 0),
        ("loveleetcode", 2),
        ("aabb", -1),
        ("", -1),
        ("z", 0),
    ],
)
def test_first_unique_char(s, expected):
    assert first_unique_char(s) == expected


@pytest.mark.parametrize(
    "s, t, expected",
    [
        ("anagram", "nagaram", True),
        ("rat", "car", False),
        ("ab", "a", False),
        ("", "", True),
    ],
)
def test_is_anagram(s, t, expected):
    assert is_anagram(s, t) == expected


@pytest.mark.parametrize(
    "s, expected",
    [
        ("aafbaaaaffc", {"a": 4, "f": 2, "b": 1, "c": 1}),
        ("", {}),
        ("aaaa", {"a": 4}),
        ("abc", {"a": 1, "b": 1, "c": 1}),
    ],
)
def test_max_consecutive_repeats(s, expected):
    assert max_consecutive_repeats(s) == expected
