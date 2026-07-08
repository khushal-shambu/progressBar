"""Meta-bar logic: increments, yearly reset, emotional clicks."""
from datetime import date
import db
from config import (
    GROWTH_PER_HOUR,
    EMOTIONAL_CLICK_BONUS,
    EMOTIONAL_MAX_PER_DAY,
    PROJECT_DEFEAT_BONUS,
    META_RESET_MONTH,
    META_RESET_DAY,
)


def _last_reset_date(today: date) -> date:
    """The most recent May 28 on or before today."""
    this_year_reset = date(today.year, META_RESET_MONTH, META_RESET_DAY)
    if today >= this_year_reset:
        return this_year_reset
    return date(today.year - 1, META_RESET_MONTH, META_RESET_DAY)


def check_and_apply_reset():
    """Reset meta-bar if we've crossed May 28 since last cycle_start."""
    row = db.get_growth()
    cycle_start = date.fromisoformat(row["cycle_start"])
    today = date.today()
    expected = _last_reset_date(today)
    if cycle_start < expected:
        db.set_growth(0.0, expected.isoformat())
        return True
    return False


def add_hours(hours: float) -> float:
    """Add growth for hours logged. Returns new percent."""
    row = db.get_growth()
    new_pct = min(100.0, row["percent"] + hours * GROWTH_PER_HOUR)
    db.set_growth(new_pct)
    return new_pct


def add_project_defeat_bonus() -> float:
    row = db.get_growth()
    new_pct = min(100.0, row["percent"] + PROJECT_DEFEAT_BONUS)
    db.set_growth(new_pct)
    return new_pct


def try_emotional_click() -> tuple[bool, float, str]:
    """Returns (success, new_percent, message)."""
    today_iso = date.today().isoformat()
    count = db.emotional_clicks_today(today_iso)
    if count >= EMOTIONAL_MAX_PER_DAY:
        row = db.get_growth()
        return False, row["percent"], "Already claimed emotional/financial growth today."
    db.record_emotional_click(today_iso)
    row = db.get_growth()
    new_pct = min(100.0, row["percent"] + EMOTIONAL_CLICK_BONUS)
    db.set_growth(new_pct)
    return True, new_pct, "Growth logged."


def current_percent() -> float:
    return db.get_growth()["percent"]