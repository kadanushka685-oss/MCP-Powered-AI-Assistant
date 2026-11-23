"""Lets `pytest` find the project packages (unittest users do not need this file)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
