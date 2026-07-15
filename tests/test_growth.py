from config import GROWTH_PER_HOUR


def test_one_hour_growth():
    assert 1 * GROWTH_PER_HOUR == 0.3


def test_ten_hour_growth():
    assert 10 * GROWTH_PER_HOUR == 3.0


def test_growth_cap():
    current = 99.9
    added = 5

    new_value = min(100.0, current + added)

    assert new_value == 100.0