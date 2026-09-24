"""Put the reconstruction service dir on sys.path so tests can import the package."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
