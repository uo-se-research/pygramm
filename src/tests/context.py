"""This path-hacking is recommended by "The Hitchhikers Guide to Python".
In other words, _not my fault_. I know it's ugly and breaks assumptions of IDEs
but this is apparently how it's done.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../pygramm')))
