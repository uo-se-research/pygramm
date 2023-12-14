"""Parse Antlr grammar to produce grammar.Grammar object.
Antlr is a widely used parser generator and so a source of many parsing
grammars.  (Work in progress)
"""

import os

from lark import Lark, Transformer
from . import grammar
from . import config

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

HERE = os.path.abspath(os.path.dirname(__file__))
ANTLR_GRAMM = os.path.join(HERE, "antlr.lark")

def parse(grammar_path: str, len_based_size=False) -> grammar.Grammar:
    """Produce a pygramm Grammar object from an Antlr grammar."""
    config.LEN_BASED_SIZE = len_based_size  # update global accordingly to be used in grammar.
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

    def IDENT(self, data):
        return data.value

    def ident(self, children) -> grammar._Symbol:
        id = children[0]
        log.debug(f"Transforming identifier from {id}")
        sym = self.gram.symbol(id)
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

    def choices(self, children):
        """?choices: seq ("|" seq)* """
        elements = self.gram.choice()
        for child in children:
            elements.append(child)
        return elements

    def spans(self, children):
        """ spans: /[.*]/
        Handler copied from llparse.py.
        """
        s = children[0]
        assert s[0] == "[" and s[-1] == "]"
        choices = grammar._CharRange(desc=s)
        # We need to see each character code as an individual
        # character.
        inner = s[1:-1]
        r = inner.encode().decode(r"unicode-escape")
        # FIXME: This will not handle \\[ correctly
        pos = 0
        while pos < len(r):
            # A span x-y?
            #  x would be at position len(r) - 3 or earlier
            if pos <= len(r) - 3 and r[pos + 1] == '-':
                range_begin = r[pos]
                range_end = r[pos + 2]
                for i in range(ord(range_begin), ord(range_end) + 1):
                    choices.append(self.gram.literal(chr(i)))
                pos += 3
            else:
                choices.append(self.gram.literal(r[pos]))
                pos += 1
        return choices

    def regex(self, children):
        return children[0]

    def negation_unsupported(self, children):
        """char_class:
            _negated char_class -> negation_unsupported
            | spans
        """
        chars = children[0].value
        raise ValueError(f"""
        Negated character classes (~{chars}) should be replaced with
        examples of acceptable characters.
        """)


    def star(self, children):
        """star: _rhs_item "*" """
        kleene = self.gram.kleene(children[0])
        return kleene

    def plus(self, children):
        """x+ is the same as x x *"""
        sequence = self.gram.seq()
        sequence.append(children[0])
        tail = self.gram.kleene(children[0])
        sequence.append(tail)
        return sequence

    def optional(self, children):
        """x? is (x | empty)"""
        empty = self.gram.seq()
        opt = self.gram.choice()
        opt.append(children[0])
        opt.append(empty)
        return opt

    def production(self, children) -> tuple[grammar._Symbol, grammar.RHSItem]:
        log.debug(f"Transforming production {children}")
        lhs, rhs = children
        self.gram.add_cfg_prod(lhs, rhs)
        return lhs, rhs

    def antlr(self, tree):
        return self.gram

    def __default__(self, data, children, meta):
        log.warning(f"Unrecognized node\nData: {data}\nChildren: {children}")
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
spans: /\\[.*\\]/

//# Typical pattern for identifiers.  Antlr uses lexical conventions
//# to distinguish terminals from non-terminals, but we can ignore
//# that distinction.
IDENT: /[_a-zA-Z][_a-zA-Z0-9]*/
"""