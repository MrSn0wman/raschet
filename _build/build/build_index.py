# -*- coding: utf-8 -*-
"""Compatibility wrapper; standalone pages now share the autonomous pipeline.

Use build_all.py --site OUT. No old source tree or hardcoded system paths.
"""
from build_all import main

if __name__ == "__main__":
    main()
