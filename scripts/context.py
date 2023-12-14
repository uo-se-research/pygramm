"""This path-hacking is recommended by "The Hitchhikers Guide to Python".
In other words, _not my fault_. I know it's ugly and breaks assumptions of IDEs
but this is apparently how it's done.
"""
import os
import sys
# Step-by-step for debugging
_this_dir = os.path.dirname(__file__)
_pygramm_rel = os.path.join(_this_dir, "../src")
_pygramm_abs = os.path.abspath(_pygramm_rel)
sys.path.insert(0, _pygramm_abs)
pass

