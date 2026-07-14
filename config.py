"""App-wide constants and paths."""
from pathlib import Path
import os
import platform

APP_NAME = "ProgressBar"

# Meta-bar tuning
GROWTH_PER_HOUR = 0.3
EMOTIONAL_CLICK_BONUS = 0.5
EMOTIONAL_MAX_PER_DAY = 1
PROJECT_DEFEAT_BONUS = 2.0
META_RESET_MONTH = 5
META_RESET_DAY = 28

# Timer
TIMER_PROMPT_MINUTES = 90
TIMER_EXTEND_MINUTES = 90

# Limits
MAX_ACTIVE_PROJECTS = 5


if platform.system() == "Windows":
    DATA_DIR = (
        Path.home()
        / "OneDrive - BURNAC PRODUCE LIMITED"
        / "ProgressBar"
    )
else:
    DATA_DIR = (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "OneDrive-BURNACPRODUCELIMITED"
        / "ProgressBar"
    )

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "progressbar.db"