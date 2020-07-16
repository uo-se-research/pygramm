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
# The grammar comes here.  It should follow this ebnf.
# Lexical productions are not yet implemented.
#
#  grammar ::= { production } ;
#  production ::= IDENT '::=' bnf_rhs  TERMINATOR
#  production ::= IDENT ':='  lex_rhs  TERMINATOR
#  bnf_rhs ::=  { rhs_term }
#  rhs_term ::= rhs_primary { '|'  rhs_primary }
#  rhs_primary ::= symbol [ '*' ]
#  symbol ::= IDENT | STRING | group
#  group ::= '(' bnf_rhs ')'
#  lexprod ::=  STRING { '|' STRING }
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
        _production(stream)
    return


def _production(stream: TokenStream):
    """
    production ::= bnfprod | lexprod ;  # Oops, same first
    bnfprod ::= IDENT BNFPROD { symbol } TERMINATOR ;
    lexprod ::= IDENT LEXPROD STRING TERMINATOR;
    """
    require(stream, TokenCat.IDENT, desc="Production should begin with symbol")
    lhs_ident = stream.take()
    prod_type = stream.take()
    if prod_type.kind == TokenCat.BNFPROD:
        rhs = _bnf_rhs(stream)
        grammar.add_cfg_prod(lhs_ident.value, rhs)
    elif prod_type.kind == TokenCat.LEXPROD:
        rhs = _lex_rhs(stream)
        grammar.add_lex_prod(lhs_ident.value, rhs)
    require(stream, TokenCat.TERMINATOR, "Production must end with terminator",
            consume=True)


#  bnf_rhs ::=  { rhs_term }  # Seq
#  rhs_term ::= rhs_primary { '|'  rhs_primary }  # Choice
#  rhs_primary ::= symbol [ '*' ]  # Kleene

# 'first' items of 'symbol'
FIRST_SYM = [TokenCat.IDENT, TokenCat.STRING, TokenCat.CHAR]

def _bnf_rhs(stream: TokenStream) -> grammar.RHSItem:
    """Sequence of rhs items"""
    # Could be an empty list ...
    if stream.peek().kind == TokenCat.TERMINATOR:
        return grammar.Seq()  # The empty sequence
    first = _rhs_term(stream)
    # Could be a single item
    if stream.peek().kind == TokenCat.TERMINATOR:
        return first
    seq = grammar.Seq()
    seq.append(first)
    while stream.peek().kind in FIRST_SYM:
        next_item = _rhs_term(stream)
        seq.append(next_item)
    return seq

#  rhs_term ::= rhs_primary { '|'  rhs_primary }  # Choice

def _rhs_term(stream: TokenStream) -> grammar.RHSItem:
        """Disjunction of items; could be just one"""
        item = _rhs_primary(stream)
        if stream.peek().kind != TokenCat.DISJUNCT:
            return item
        choice = grammar.Choice()
        choice.append(item)
        while stream.peek().kind == TokenCat.DISJUNCT:
            stream.take()
            item = _rhs_primary(stream)
            log.debug(f"Adding choice {item} to choices")
            choice.append(item)
        return choice

#  rhs_primary ::= symbol [ '*' ]  # Kleene

def _rhs_primary(stream: TokenStream) -> grammar.RHSItem:
    """A symbol or group, possibly with kleene star"""
    item = _rhs_symbol(stream)
    log.debug(f"Primary: {item}")
    if stream.peek().kind == TokenCat.KLEENE:
        token = stream.take()
        return grammar.Kleene(item)
    else:
        return item

def _rhs_symbol(stream: TokenStream) -> grammar.RHSItem:
    """A single identifier or literal, or a parenthesized group"""
    if stream.peek().kind == TokenCat.LPAREN:
        stream.take()
        subseq = _bnf_rhs(stream)
        require(stream, TokenCat.RPAREN, consume=True)
        log.debug(f"Subsequence group: {subseq}")
        return subseq
    token = stream.take()
    if token.kind == TokenCat.STRING or token.kind == TokenCat.CHAR:
        log.debug("Forming literal")
        return grammar.Literal(token.value[1:-1]) # Clips quotes
    elif token.kind == TokenCat.IDENT:
        log.debug("Forming symbol")
        return grammar.Symbol(token.value)
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
    sample = open("data/bulk.txt")
    print("Parsing sample")
    parse(sample)
    print("Parsed!")
    grammar.dump()

