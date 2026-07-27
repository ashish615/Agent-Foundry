"""Make the repo root importable so `from migrations.models import ...` works."""

import sys
import os

# Add repo root to sys.path when tests are run from the migrations/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
