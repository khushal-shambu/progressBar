"""App-wide constants and paths."""
from pathlib import Path
import os

APP_NAME = "ProgressBar"

# Meta-bar tuning
GROWTH_PER_HOUR = 0.3            # % added to meta-bar per hour logged
EMOTIONAL_CLICK_BONUS = 0.5      # % added per emotional/financial click
EMOTIONAL_MAX_PER_DAY = 1        # cap on emotional clicks per day
PROJECT_DEFEAT_BONUS = 2.0       # % bonus when a project hits 0%
META_RESET_MONTH = 5             # May
META_RESET_DAY = 28              # 28th

# Limits
MAX_ACTIVE_PROJECTS = 5

# Data location: prefer OneDrive if it exists, else home dir
def _resolve_data_dir() -> Path:
    candidates = [
        Path.home() / "OneDrive" / APP_NAME,
        Path.home() / "OneDrive - Personal" / APP_NAME,
        Path.home() / f".{APP_NAME.lower()}",
    ]
    # Env var override
    if os.getenv("PROGRESSBAR_DATA_DIR"):
        return Path(os.getenv("PROGRESSBAR_DATA_DIR"))
    for c in candidates:
        if c.parent.exists():
            return c
    return candidates[-1]

DATA_DIR = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "progressbar.db"