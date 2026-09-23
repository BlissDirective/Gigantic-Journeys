"""Put the traversal service dir on sys.path so tests can ``import movement``."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
