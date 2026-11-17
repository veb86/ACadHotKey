#!/usr/bin/env python3
"""Verify both complete API generations and the startup autoloader manifest."""
import sys
from release_package import verify_bundle

verify_bundle(sys.argv[1])
print("Complete startup bundle for AutoCAD 2020, 2021, 2022, 2023 and 2024.")
