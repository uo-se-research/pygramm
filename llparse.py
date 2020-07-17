"""
An LL parser for BNF
Michal Young, adapted Summer 2020 from CIS 211 projects
"""

from lex import TokenStream, TokenCat
import grammar
from typing import TextIO, List, Dict
# import io
# import traceback
import sys

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class InputError(Exception):
    """Raised when we can't parse the input"""
    pass


def parse(srcfile: TextIO):
    """Interface function to LL parser of BNF.
    Populates TERMINALS and NONTERMINALS
    """
    stream = TokenStream(srcfile)
    _grammar(stream)
    return


def require(stream: TokenStream, category: TokenCat, desc: str = "", consume=False):
    """Requires the next token in the stream to match a specified category.
    Consumes and discards it if consume==True.
    """
    if stream.peek().kind != category:
        raise InputError(f"Expecting {desc or category}, but saw {stream.peek()} instead")
    if consume:
        stream.take()
    return


#
# The grammar comes here.  Currently there are no
# separate lexical productions; the CFG covers both
# syntactic and lexical structure (as that is how Glade
# learned grammars work).  Also to accommodate Glade
# learned grammars, 'merges' may equate some symbols.
# A merge looks like
# <Rep_4361187736> ::: [<Rep_4360470880>, <Alt_4361188688>];
#
#  grammar ::= { statement }
#  statement ::= production TERMINATOR | merge TERMINATOR
#  merge ::= IDENT ':::' '[' IDENT {',' IDENT } ']'
#  production ::= IDENT '::=' bnf_rhs
#  bnf_rhs ::= bnf_seq { '|' bnf_seq }
#  bnf_seq ::= bnf_primary { bnf_primary }
#  bnf_primary ::= symbol [ '*' ]
#  symbol ::= IDENT | STRING | group
#  group ::= '(' bnf_rhs ')'
#

def _grammar(stream: TokenStream) :
    """
    grammar ::= block ;
    (Implicitly returns dicts in the grammar module)
    """
    _block(stream)
    require(stream, TokenCat.END)
    return


def _block(stream: TokenStream):
    """
    block ::= { production }
    (Adds to dicts in grammar module)
    """
    log.debug(f"Parsing block from token {stream.peek()}")
    while stream.peek().kind == TokenCat.IDENT:
        _statement(stream)
    return


def _statement(stream: TokenStream):
    """
    _statement == production | merge
    (left-factored for lookahead)
    """
    require(stream, TokenCat.IDENT, desc="Statement should begin with symbol")
    lhs_ident = stream.take().value
    prod_type = stream.take()
    if prod_type.kind == TokenCat.BNFPROD:
        rhs = _bnf_rhs(stream)
        grammar.add_cfg_prod(lhs_ident, rhs)
    elif prod_type.kind == TokenCat.BNFMERGE:
        merge_list = _merge_symbols(stream)
        # Merges are symmetric, so order doesn't matter
        merge_list.append(lhs_ident)
        grammar.merge_symbols(merge_list)
    require(stream, TokenCat.TERMINATOR, "Statement must end with terminator",
            consume=True)

def _merge_symbols(stream) -> List[str]:
    """IDENT @ ':::' '[' IDENT {',' IDENT } ']' """
    require(stream, TokenCat.LBRACK, consume=True)
    merge_list = [ ]
    # Assume at least one item in merge list
    merge_list.append(stream.take().value)
    while stream.peek().kind == TokenCat.COMMA:
        stream.take()
        merge_list.append(stream.take().value)
    require(stream, TokenCat.RBRACK, consume=True)
    return merge_list


#  bnf_rhs ::= bnf_seq { '|' bnf_seq }
#  bnf_seq ::= bnf_primary { bnf_primary }

# 'first' items of 'symbol'
FIRST_SYM = [TokenCat.IDENT, TokenCat.STRING, TokenCat.CHAR]

def _bnf_rhs(stream: TokenStream) -> grammar.RHSItem:
    choice = _bnf_seq(stream)
    # Special case: Only one alternative
    if stream.peek().kind != TokenCat.DISJUNCT:
        return choice
    choices = grammar.Choice()
    choices.append(choice)
    while stream.peek().kind == TokenCat.DISJUNCT:
        stream.take()
        choice = _bnf_seq(stream)
        choices.append(choice)
    return choices

def _bnf_seq(stream: TokenStream) -> grammar.RHSItem:
    """Sequence of rhs items"""
    # Could be an empty list ...
    if stream.peek().kind == TokenCat.TERMINATOR:
        return grammar.Seq()  # The empty sequence
    first = _bnf_primary(stream)
    # Could be a single item
    if stream.peek().kind == TokenCat.TERMINATOR:
        return first
    seq = grammar.Seq()
    seq.append(first)
    while stream.peek().kind in FIRST_SYM:
        next_item = _bnf_primary(stream)
        seq.append(next_item)
    return seq

#  rhs_primary ::= symbol [ '*' ]  # Kleene

def _bnf_primary(stream: TokenStream) -> grammar.RHSItem:
    """A symbol or group, possibly with kleene star"""
    item = _bnf_symbol(stream)
    # log.debug(f"Primary: {item}")
    if stream.peek().kind == TokenCat.KLEENE:
        token = stream.take()
        return grammar.Kleene(item)
    else:
        return item

def _bnf_symbol(stream: TokenStream) -> grammar.RHSItem:
    """A single identifier or literal, or a parenthesized group"""
    if stream.peek().kind == TokenCat.LPAREN:
        stream.take()
        subseq = _bnf_rhs(stream)
        require(stream, TokenCat.RPAREN, consume=True)
        # log.debug(f"Subsequence group: {subseq}")
        return subseq
    token = stream.take()
    if token.kind == TokenCat.STRING or token.kind == TokenCat.CHAR:
        # log.debug("Forming literal")
        return grammar.Literal(token.value[1:-1]) # Clips quotes
    elif token.kind == TokenCat.IDENT:
        # log.debug("Forming symbol")
        return grammar.mk_symbol(token.value)
    else:
        raise InputError(f"Unexpected input token {token.value}")



def _lex_rhs(stream: TokenStream) -> grammar.Literal:
    """FIXME: How should we define lexical productions?"""
    token = stream.take()
    if (token.kind == TokenCat.STRING or
        token.kind == TokenCat.NUMBER):
        return grammar.Literal(token)
    else:
        raise InputError(f"Lexical RHS should be string literal or integer")


if __name__ == "__main__":
    sample = open("data/gram-calc-recursive-2020-06-04_23-31.gram.txt")
    print("Parsing sample")
    parse(sample)
    print("Parsed!")
    grammar.dump()

