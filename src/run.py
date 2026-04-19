"""Pipeline entry point.

Wrapper that lets you run the EWS pipeline from the repo root without
setting PYTHONPATH:

    python src/run.py

All the actual logic lives in src/ews/*.py; this file just adds src/ to
sys.path and delegates to ews.pipeline.main().
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ews.pipeline import main

if __name__ == "__main__":
    main()
