"""Parse Antlr grammar to produce grammar.Grammar object.
Antlr is a widely used parser generator and so a source of many parsing
grammars.  (Work in progress)
"""

import os

from lark import Lark, Transformer
import grammar

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

HERE = os.path.abspath(os.path.dirname(__file__))
ANTLR_GRAMM = os.path.join(HERE, "antlr.lark")

def parse(grammar_path: str) -> grammar.Grammar:
    """Produce a pygramm Grammar object from an Antlr grammar."""
    log.debug("Opening Lark grammar for Antlr grammars")
    antlr_parser = Lark(open(ANTLR_GRAMM, "r"))
    log.debug(f"Opening Antlr grammar file {grammar_path}")
    antlr_grammar_f = open(grammar_path, "r")
    antlr_grammar = "".join(antlr_grammar_f.readlines())
    log.debug("Parsing Antlr grammar with Lark")
    tree = antlr_parser.parse(antlr_grammar)
    print(f"Before transformation: \n{tree.pretty()}")
    xform = GramBuilder(grammar_path.rpartition('/')[-1])
    gram = xform.transform(tree)
    gram.finalize()
    print(f"After transformation: \n{gram.dump()}")
    # log.debug("Transforming to grammar.Grammar (NOT DONE")
    # return grammar._Literal("NOT DONE")
    return gram


class GramBuilder(Transformer):
    """Lark transformer for converting Lark concrete syntax tree
    into our grammar.Grammar object for input generation.
    Method names are symbols in Lark grammar for Antlr grammar (antlr.lark).
    """

    def __init__(self, name: str, gram: grammar.Grammar = None):
        if not gram:
            gram = grammar.Grammar(name)
        self.gram = gram

    def literal(self,  children) -> grammar._Literal:
        log.debug(f"Transforming literal from {children}")
        quoted_text: str  = children[0]
        text = quoted_text.strip('"\'')
        return grammar._Literal(text)

    def IDENT(self, data) -> grammar._Symbol:
        log.debug(f"Transforming IDENT from {data}")
        sym = self.gram.symbol(data.value)
        return sym

    def lhs(self, children):
        """lhs -> "fragment"? IDENT"""
        log.debug(f"Transforming lhs with {children}")
        sym = children[0]
        log.debug(f"lhs symbol is {sym}")
        return sym

    def seq(self, children):
        log.debug(f"Production RHS as sequence {children}")
        sequence = grammar.Grammar.seq()
        for child in children:
            sequence.append(child)
        return sequence


    def production(self, children) -> tuple[grammar._Symbol, grammar.RHSItem]:
        log.debug(f"Transforming production {children}")
        lhs, rhs = children
        self.gram.add_cfg_prod(lhs, rhs)
        return lhs, rhs

    def antlr(self, tree):
        return self.gram

    def __default__(self, data, children, meta):
        log.debug(f"Unrecognized node\nData: {data}\nChildren: {children}")
        return data

# From antlr.lark:
"""
antlr: (noise | production)*
production: lhs ":" choices ";"
lhs: "fragment"? IDENT
choices: choices "|" choice | choice
choice:  rhs_item *
rhs_item: star | plus | optional | skip | primary
star: rhs_item "*"
plus: rhs_item "+"
optional: rhs_item "?"
skip:  rhs_item "->" "skip"
primary:  IDENT | token_def | "(" choices ")"


//# Token definitions in Antlr can be strings or regular expressions
token_def:  literal | regex
literal: /["][^"]*["]/ | /['][^']*[']/
regex: char_class
char_class: negated char_class | spans
negated: "~"
spans: /\[.*\]/

//# Typical pattern for identifiers.  Antlr uses lexical conventions
//# to distinguish terminals from non-terminals, but we can ignore
//# that distinction.
IDENT: /[_a-zA-Z][_a-zA-Z0-9]*/
"""