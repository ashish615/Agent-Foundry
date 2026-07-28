"""Model Registry service."""
import sys
from pathlib import Path

_MIGRATIONS = Path(__file__).resolve().parents[3] / "migrations"
if _MIGRATIONS.is_dir() and str(_MIGRATIONS) not in sys.path:
    sys.path.insert(0, str(_MIGRATIONS))
