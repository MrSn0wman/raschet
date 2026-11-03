# -*- coding: utf-8 -*-
"""Compatibility entrypoint: rebuild versioned sources to a dedicated OUT only.

Never synchronizes public HTML in place. Use Lead-owned publish_local_build.py
after independent QA to copy validated generated files without root deletion.
"""
from build_all import main

if __name__ == "__main__":
    main()
