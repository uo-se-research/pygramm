"""Parse Antlr grammar to produce grammar.Grammar object.
Antlr is a widely used parser generator and so a source of many parsing
grammars.  (Work in progress)
"""

from lark import Lark, Transformer
import grammar

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

ANTLR_GRAMM = "antlr_gramm.py"  ## Should be relative to this file!

def parse(grammar_path: str) -> grammar.Grammar:
    """Produce a pygramm Grammar object from an Antlr grammar."""
    log.debug("Opening Lark grammar for Antlr grammars")
    antlr_parser = Lark(open(ANTLR_GRAMM, "r"))
    log.debug(f"Opening Antlr grammar file {grammar_path}")
    antlr_grammar = "".join(open(grammar_path, "r")).readlines()
    log.debug("Parsing Antlr grammar with Lark")
    tree = antlr_parser(antlr_grammar)
    log.debug("Transforming to grammar.Grammar (NOT DONE")
    return grammar._Literal("NOT DONE")
    return tree # Wrong type for now


class GramBuilder(Transformer):
    """Lark transformer for converting Lark concrete syntax tree
    into our grammar.Grammar object for input generation.
    Method names are symbols in Lark grammar for Antlr grammar (antlr.lark).
    """
    pass


