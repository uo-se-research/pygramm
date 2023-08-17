"""Simple tests of parsing an Antlr grammar file to build a pygramm grammar structure"""

# Allow running as if it were a top-level script despite being in the
# pygramm/test subdirectory
import sys

if __name__ == "__main__":
    sys.path.append("../..")
    __name__ == "pygramm/test/test_parse_antlr"

import lark

antlr_parser = lark.Lark(open("../src/antlr.lark", "r"))
bibtex_grammar_src = open("bibtex.g4", "r")
tree = antlr_parser.parse("".join(bibtex_grammar_src.readlines()))
print(tree)
