"""AI Gateway service."""
import sys
from pathlib import Path

# Shared ORM models live in migrations/ at the repo root. Adding it here
# (once, at package import time) avoids repeating sys.path logic in each module.
_MIGRATIONS = Path(__file__).resolve().parents[3] / "migrations"
if _MIGRATIONS.is_dir() and str(_MIGRATIONS) not in sys.path:
    sys.path.insert(0, str(_MIGRATIONS))
