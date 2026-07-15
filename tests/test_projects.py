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