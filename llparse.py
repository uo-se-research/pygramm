"""
An LL parser for BNF
Michal Young, adapted Summer 2020 from CIS 211 projects,
revised in discussion with Ziyad Alsaeed.
"""

from lex import TokenStream, TokenCat
import grammar
from typing import TextIO, List

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class InputError(Exception):
    """Raised when we can't parse the input"""
    pass


def parse(srcfile: TextIO) -> grammar.Grammar:
    """Interface function to LL parser of BNF.
    Populates TERMINALS and NONTERMINALS
    """
    stream = TokenStream(srcfile)
    gram = grammar.Grammar()
    _grammar(stream, gram)
    gram.finalize()
    return gram


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

def _grammar(stream: TokenStream, gram: grammar.Grammar) :
    """
    grammar ::= block ;
    (Implicitly returns dicts in the grammar module)
    """
    _block(stream, gram)
    require(stream, TokenCat.END)
    return


def _block(stream: TokenStream, gram: grammar.Grammar):
    """
    block ::= { production }
    (Adds to dicts in grammar module)
    """
    log.debug(f"Parsing block from token {stream.peek()}")
    while stream.peek().kind == TokenCat.IDENT:
        _statement(stream, gram)
    return


def _statement(stream: TokenStream, gram: grammar.Grammar):
    """
    _statement == production | merge
    (left-factored for lookahead)
    """
    require(stream, TokenCat.IDENT, desc="Statement should begin with symbol")
    lhs_ident = stream.take().value
    prod_type = stream.take()
    if prod_type.kind == TokenCat.BNFPROD:
        rhs = _bnf_rhs(stream, gram)
        gram.add_cfg_prod(lhs_ident, rhs)
    elif prod_type.kind == TokenCat.BNFMERGE:
        merge_list = _merge_symbols(stream)
        # Merges are symmetric, so order doesn't matter
        merge_list.append(lhs_ident)
        gram.merge_symbols(merge_list)
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

def _bnf_rhs(stream: TokenStream, gram: grammar.Grammar) -> grammar.RHSItem:
    choice = _bnf_seq(stream, gram)
    # Special case: Only one alternative
    if stream.peek().kind != TokenCat.DISJUNCT:
        return choice
    choices = gram.choice()
    choices.append(choice)
    while stream.peek().kind == TokenCat.DISJUNCT:
        stream.take()
        choice = _bnf_seq(stream, gram)
        choices.append(choice)
    return choices

def _bnf_seq(stream: TokenStream, gram: grammar.Grammar) -> grammar.RHSItem:
    """Sequence of rhs items"""
    # Could be an empty list ...
    if stream.peek().kind == TokenCat.TERMINATOR:
        return gram.seq()  # The empty sequence
    first = _bnf_primary(stream, gram)
    # Could be a single item
    if stream.peek().kind == TokenCat.TERMINATOR:
        return first
    seq = gram.seq()
    seq.append(first)
    while stream.peek().kind in FIRST_SYM:
        next_item = _bnf_primary(stream, gram)
        seq.append(next_item)
    return seq

#  rhs_primary ::= symbol [ '*' ]  # Kleene

def _bnf_primary(stream: TokenStream, gram: grammar.Grammar) -> grammar.RHSItem:
    """A symbol or group, possibly with kleene star"""
    item = _bnf_symbol(stream, gram)
    # log.debug(f"Primary: {item}")
    if stream.peek().kind == TokenCat.KLEENE:
        token = stream.take()
        return gram.kleene(item)
    else:
        return item

def _bnf_symbol(stream: TokenStream, gram: grammar.Grammar) -> grammar.RHSItem:
    """A single identifier or literal, or a parenthesized group"""
    if stream.peek().kind == TokenCat.LPAREN:
        stream.take()
        subseq = _bnf_rhs(stream, gram)
        require(stream, TokenCat.RPAREN, consume=True)
        # log.debug(f"Subsequence group: {subseq}")
        return subseq
    token = stream.take()
    if token.kind == TokenCat.STRING or token.kind == TokenCat.CHAR:
        # log.debug("Forming literal")
        return gram.literal(token.value[1:-1]) # Clips quotes
    elif token.kind == TokenCat.IDENT:
        # log.debug("Forming symbol")
        return gram.symbol(token.value)
    else:
        raise InputError(f"Unexpected input token {token.value}")



def _lex_rhs(stream: TokenStream, gram: grammar.Grammar) -> grammar._Literal:
    """FIXME: How should we define lexical productions?"""
    token = stream.take()
    if (token.kind == TokenCat.STRING or
        token.kind == TokenCat.NUMBER):
        return gram.literal(token.value)
    else:
        raise InputError(f"Lexical RHS should be string literal or integer")


if __name__ == "__main__":
    sample = open("data/with_comments.txt")
    print("Parsing sample")
    gram = parse(sample)
    print("Parsed!")
    gram.dump()

