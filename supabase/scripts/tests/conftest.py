"""Put supabase/scripts on sys.path so tests can ``import check_rls``."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
