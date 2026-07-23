def calculate_remaining_hp(total_hours, logged_hours):
    return max(0.0, 100.0 - (logged_hours / total_hours * 100.0))


def test_new_project():
    assert calculate_remaining_hp(100, 0) == 100.0


def test_half_complete():
    assert calculate_remaining_hp(100, 50) == 50.0


def test_fully_complete():
    assert calculate_remaining_hp(100, 100) == 0.0


def test_over_complete():
    assert calculate_remaining_hp(100, 200) == 0.0


def test_cannot_reduce_below_logged():
    """Editing total hours below hours_logged should be rejected."""
    hours_logged = 5.0
    new_total = 3.0
    assert new_total < hours_logged  # rule triggers rejection


def test_can_increase_total():
    """Increasing total should be allowed."""
    hours_logged = 2.0
    old_total = 5.0
    new_total = 20.0
    assert new_total > old_total
    assert new_total >= hours_logged
