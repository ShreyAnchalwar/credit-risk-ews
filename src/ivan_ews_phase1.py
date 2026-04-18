"""Backwards-compat shim — preserves the README quickstart
`python src/ivan_ews_phase1.py`. All real code lives in src/ews/."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ews.run import main

if __name__ == "__main__":
    main()
