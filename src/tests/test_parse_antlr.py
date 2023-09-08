"""Simple tests of parsing an Antlr grammar file to build a pygramm grammar structure"""

# Allow running as if it were a top-level script despite being in the
# pygramm/tests subdirectory
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygramm

import pygramm.antlr_gramm

tree = antlr_gramm.parse("../tests/bibtex.g4")
print(tree)

