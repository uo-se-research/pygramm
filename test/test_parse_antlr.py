"""Simple tests of parsing an Antlr grammar file to build a pygramm grammar structure"""

# import context
# import sys
# sys.path.append("..")
import lark

antlr_parser = lark.Lark(open("../antlr.lark", "r"))
bibtex_grammar_src = open("bibtex.g4", "r")
tree = antlr_parser.parse("".join(bibtex_grammar_src.readlines()))
print(tree)
