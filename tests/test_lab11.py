import random

import pytest

from labs.lab11 import (
    BloomFilter,
    ConsistentHashRing,
    hash_key,
    hash_str,
    naive_node,
    naive_rebalanced_fraction,
    ring_rebalanced_fraction,
)


def _make_keys(count: int) -> list:
    """Детерминированный набор строковых ключей key-0..key-(count-1)."""
    keys = []
    i = 0
    while i < count:
        keys.append(f"key-{i}")
        i += 1
    return keys


class TestHashFunctions:
    def test_hash_str_deterministic(self):
        assert hash_str("abc") == hash_str("abc")

    def test_hash_str_salt_changes_result(self):
        assert hash_str("abc", salt=0) != hash_str("abc", salt=1)

    def test_hash_str_in_64bit_range(self):
        h = hash_str("a-fairly-long-string-key-for-overflow-check")
        assert 0 <= h < (1 << 64)

    def test_hash_str_different_strings_differ(self):
        assert hash_str("abc") != hash_str("acb")

    def test_hash_key_matches_str_of_key(self):
        assert hash_key(42) == hash_str("42")


class TestNaiveSharding:
    def test_naive_node_deterministic(self):
        assert naive_node("key-1", 4) == naive_node("key-1", 4)

    def test_naive_node_in_range(self):
        for i in range(100):
            assert 0 <= naive_node(f"key-{i}", 4) < 4

    def test_naive_node_invalid_num_nodes(self):
        with pytest.raises(ValueError):
            naive_node("key", 0)

    def test_naive_rebalances_almost_everything(self):
        # При N -> N+1 в схеме hash % N переезжает подавляющее большинство ключей.
        keys = _make_keys(5000)
        fraction = naive_rebalanced_fraction(keys, num_nodes=4)
        assert fraction > 0.5  # на деле близко к 1 - 1/(N+1)

    def test_naive_rebalanced_fraction_empty(self):
        assert naive_rebalanced_fraction([], num_nodes=4) == 0.0


class TestConsistentHashRing:
    def test_invalid_replicas_raises(self):
        with pytest.raises(ValueError):
            ConsistentHashRing(replicas=0)

    def test_get_node_on_empty_ring_raises(self):
        ring = ConsistentHashRing(replicas=10)
        with pytest.raises(ValueError):
            ring.get_node("key-1")

    def test_get_node_deterministic(self):
        ring = ConsistentHashRing(replicas=50)
        for node in ["a", "b", "c"]:
            ring.add_node(node)
        assert ring.get_node("key-42") == ring.get_node("key-42")

    def test_get_node_returns_known_node(self):
        nodes = ["a", "b", "c"]
        ring = ConsistentHashRing(replicas=50)
        for node in nodes:
            ring.add_node(node)
        for key in _make_keys(200):
            assert ring.get_node(key) in nodes

    def test_add_node_idempotent(self):
        ring = ConsistentHashRing(replicas=10)
        ring.add_node("a")
        size_once = len(ring)
        ring.add_node("a")  # повторное добавление не дублирует точки
        assert len(ring) == size_once
        assert ring.nodes() == ["a"]

    def test_replicas_create_multiple_points(self):
        ring = ConsistentHashRing(replicas=20)
        ring.add_node("a")
        assert len(ring) == 20  # одна нода -> replicas точек на кольце

    def test_remove_node_present(self):
        ring = ConsistentHashRing(replicas=10)
        ring.add_node("a")
        ring.add_node("b")
        assert ring.remove_node("a") is True
        assert "a" not in ring.nodes()
        assert len(ring) == 10  # остались точки только ноды b

    def test_remove_node_absent(self):
        ring = ConsistentHashRing(replicas=10)
        ring.add_node("a")
        assert ring.remove_node("missing") is False

    def test_remove_node_reassigns_its_keys(self):
        nodes = ["a", "b", "c"]
        ring = ConsistentHashRing(replicas=50)
        for node in nodes:
            ring.add_node(node)
        keys = _make_keys(300)
        ring.remove_node("b")
        # ключи бывшей ноды b теперь обслуживают a или c, без падений
        for key in keys:
            assert ring.get_node(key) in ["a", "c"]

    def test_ring_moves_small_fraction_on_add(self):
        # Ключевое свойство: при добавлении ноды на кольце переезжает малая доля.
        keys = _make_keys(5000)
        nodes = ["a", "b", "c", "d"]
        fraction = ring_rebalanced_fraction(keys, nodes, "e", replicas=100)
        assert fraction < 0.5  # ожидаем ~1/5 = 20%

    def test_ring_beats_naive_on_rebalance(self):
        # Прямое сравнение: кольцо ребалансит существенно меньше, чем hash % N.
        keys = _make_keys(5000)
        nodes = ["a", "b", "c", "d"]
        ring = ring_rebalanced_fraction(keys, nodes, "e", replicas=100)
        naive = naive_rebalanced_fraction(keys, num_nodes=4)
        assert ring < naive

    def test_more_replicas_more_even_distribution(self):
        keys = _make_keys(6000)
        nodes = ["a", "b", "c", "d"]

        def skew(replicas):
            ring = ConsistentHashRing(replicas=replicas)
            for node in nodes:
                ring.add_node(node)
            dist = ring.distribution(keys)
            counts = [dist[n] for n in nodes]
            return max(counts) - min(counts)

        assert skew(100) < skew(1)  # больше виртуальных нод -> меньше перекос


class TestBloomFilter:
    def test_invalid_size_raises(self):
        with pytest.raises(ValueError):
            BloomFilter(size=0)

    def test_invalid_num_hashes_raises(self):
        with pytest.raises(ValueError):
            BloomFilter(size=100, num_hashes=0)

    def test_empty_filter_contains_nothing(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        assert bloom.contains("anything") is False
        assert bloom.fill_ratio() == 0.0
        assert len(bloom) == 0

    def test_add_then_contains(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        bloom.add("hello")
        assert bloom.contains("hello") is True

    def test_no_false_negatives(self):
        # Главное свойство: всё добавленное обязано находиться (нет ложноотрицательных).
        bloom = BloomFilter(size=2048, num_hashes=4)
        added = _make_keys(300)
        for item in added:
            bloom.add(item)
        for item in added:
            assert bloom.contains(item) is True

    def test_not_everything_is_positive(self):
        # На небольшом наполнении фильтр НЕ должен отвечать True на всё подряд:
        # хотя бы какие-то чужие элементы дают False.
        bloom = BloomFilter(size=4096, num_hashes=4)
        for item in _make_keys(50):
            bloom.add(item)
        probes = [f"other-{i}" for i in range(500)]
        negatives = 0
        for item in probes:
            if not bloom.contains(item):
                negatives += 1
        assert negatives > 0  # не все True -> ложноположительных не 100%

    def test_false_positives_possible(self):
        # На сильно забитом маленьком фильтре ложноположительные обязаны появиться.
        random.seed(42)
        bloom = BloomFilter(size=64, num_hashes=3)
        added = [f"item-{i}" for i in range(40)]
        for item in added:
            bloom.add(item)
        probes = [f"probe-{i}" for i in range(500)]
        false_positives = 0
        for item in probes:
            if item not in added and bloom.contains(item):
                false_positives += 1
        assert false_positives > 0

    def test_len_counts_adds(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        bloom.add("a")
        bloom.add("b")
        assert len(bloom) == 2

    def test_fill_ratio_increases(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        assert bloom.fill_ratio() == 0.0
        bloom.add("x")
        assert bloom.fill_ratio() > 0.0

    def test_estimated_fpr_empty_is_zero(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        assert bloom.estimated_false_positive_rate() == 0.0

    def test_estimated_fpr_grows_with_load(self):
        bloom = BloomFilter(size=1024, num_hashes=3)
        for item in _make_keys(50):
            bloom.add(item)
        low = bloom.estimated_false_positive_rate()
        for item in [f"more-{i}" for i in range(200)]:
            bloom.add(item)
        high = bloom.estimated_false_positive_rate()
        assert 0.0 < low < high < 1.0
