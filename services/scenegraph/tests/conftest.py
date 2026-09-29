import sys
from pathlib import Path

# Make the scenegraph package importable without installation (mirrors
# services/reconstruction/tests/conftest.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
