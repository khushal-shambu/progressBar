"""App-wide constants and paths."""
from pathlib import Path
import os

APP_NAME = "ProgressBar"

# Meta-bar tuning
GROWTH_PER_HOUR = 0.3
EMOTIONAL_CLICK_BONUS = 0.5
EMOTIONAL_MAX_PER_DAY = 1
PROJECT_DEFEAT_BONUS = 2.0
META_RESET_MONTH = 5
META_RESET_DAY = 28

# Timer
TIMER_PROMPT_MINUTES = 90      # non-blocking prompt at 1h30m
TIMER_EXTEND_MINUTES = 90      # extend by this much if user keeps going

# Limits
MAX_ACTIVE_PROJECTS = 5

def _resolve_data_dir() -> Path:
    candidates = [
        Path.home() / "OneDrive" / APP_NAME,
        Path.home() / "OneDrive - Personal" / APP_NAME,
        Path.home() / f".{APP_NAME.lower()}",
    ]
    if os.getenv("PROGRESSBAR_DATA_DIR"):
        return Path(os.getenv("PROGRESSBAR_DATA_DIR"))
    for c in candidates:
        if c.parent.exists():
            return c
    return candidates[-1]

DATA_DIR = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "progressbar.db"