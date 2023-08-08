"""Path hack:  Make ../x.py be importable as pygramm.x
"""

import sys, os
pygramm_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.abspath(pygramm_folder))