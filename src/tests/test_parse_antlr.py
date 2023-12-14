"""Simple tests of parsing an Antlr grammar file to build a pygramm grammar structure"""
import os
# import context  # Hacks the path
import  pygramm.antlr_gramm   # IDE will complain because it knows hacking paths is a BAD idea

GRAM_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'JSON.g4'))
tree = pygramm.antlr_gramm.parse(GRAM_PATH)
print(tree.dump())

