"""Grammar structure
M Young, June 2020
"""
from typing import List, Dict

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# Parsing BNF produces two tables,
#  mapping non-terminal symbols to productions
#  and terminal symbols to strings
TERMINALS : Dict[str, list] = dict()
NONTERMINALS : Dict[str, list] = dict()
MIN_LENGTHS : Dict[str, int] = dict()
# Merges maps each element of a merge to the
# representative ("leader") of that merge
MERGES: Dict[str, str] = dict()

def merge_symbols(symbols: List[str]):
    """Each of the symbols will be mapped to a
    an already chosen leader or to a newly elected
    leader from the list.
    """
    leader = None
    for ident in symbols:
        if ident in MERGES:
            # Use existing unique leader
            if leader is None:
                leader = MERGES[ident]
            else:
                assert leader == MERGES[ident]
    if leader is None:
        # Elect new leader
        leader = symbols.pop()
    for ident in symbols:
        if ident != leader:
            MERGES[ident] = leader


HUGE = 999_999_999   # Larger than any sentence we will generate

def calc_min_tokens():
    """Calculate the minimum length of each non-terminal,
    updating the initial estimate of HUGE.
    """
    changed = True
    # Iterate to fixed point
    while changed:
        changed = False
        for symbol in NONTERMINALS:
            prior_estimate = MIN_LENGTHS[symbol]
            for rhs in NONTERMINALS[symbol]:
                new_estimate = rhs.min_tokens()
                if new_estimate < prior_estimate:
                    changed = True
                    prior_estimate = new_estimate
                    MIN_LENGTHS[symbol] = new_estimate


class RHSItem(object):
    """Abstract base class for components of the
    right hand side of a production:
    terminal symbols, non-terminal symbols,
    and repetitions (kleene stars)
    """

    def min_tokens(self) -> int:
        """Minimum length of this item in number
        of tokens.  Override in each concrete class.
        Returns CURRENT ESTIMATE of minimum length, which
        becomes accurate only after calc_min_tokens.
        """
        raise NotImplementedError("min_tokens not implemented")

    def is_nullable(self) -> bool:
        """An item is nullable if it can expand into
        zero tokens.
        """
        return self.min_tokens() == 0

    def __str__(self) ->str:
        raise NotImplementedError(f"Missing __str__ method in {self.__class__}!")


class Symbol(RHSItem):
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def min_tokens(self) -> int:
        try:
            return MIN_LENGTHS[self.name]
        except KeyError:
            raise KeyError(f"No productions for symbol {self.name}")

SYMBOLS: Dict[str, Symbol] = dict()

def mk_symbol(name: str) -> Symbol:
    """Factory for symbols; only one instance per name,
    with merging.
    """
    if name in MERGES:
        leader = MERGES[name]
        log.debug(f"Converting {name} to {leader}")
        name = leader
    if name not in SYMBOLS:
        SYMBOLS[name] = Symbol(name)
    return SYMBOLS[name]


class Literal(RHSItem):

    def __init__(self, text: str):
        self.text = text

    def __str__(self) -> str:
        return f'"{self.text}"'

    def min_tokens(self) -> int:
        return 1


class Seq(RHSItem):
    """Sequence of grammar items"""
    def __init__(self):
        self.items = [ ]

    def append(self, item: RHSItem):
        self.items.append(item)

    def __str__(self) -> str:
        return " ".join(str(item) for item in self.items)

    def min_tokens(self) -> int:
        return sum(item.min_tokens() for item in self.items)


class Kleene(RHSItem):
    """Repetition"""
    def __init__(self, child: RHSItem):
        self.child = child

    def __str__(self) -> str:
        return f"({str(self.child)})*"

    def min_tokens(self) -> int:
        """Could be repeated 0 times"""
        return 0

class Choice(RHSItem):

    def __init__(self):
        self.items: List[RHSItem] = []

    def append(self, item: RHSItem):
        self.items.append(item)

    def __str__(self) -> str:
        disjunct_str = " | ".join(str(item) for item in self.items)
        return f"({disjunct_str})"

    def min_tokens(self) -> int:
        return min(item.min_tokens() for item in self.items)



def add_cfg_prod(lhs_ident: str, rhs: list):
    if not lhs_ident in NONTERMINALS:
        NONTERMINALS[lhs_ident] = []
        MIN_LENGTHS[lhs_ident] = HUGE  # Initial estimate
    NONTERMINALS[lhs_ident].append(rhs)

def add_lex_prod(lhs_ident: str, rhs: str):
    raise NotImplemented("Lexical productions have not been implemented")

def dump():
    """Dump the grammar to stdout with annotation"""
    calc_min_tokens()
    for symbol in NONTERMINALS:
        print(f"# {symbol}, min length {MIN_LENGTHS[symbol]}")
        for rhs in NONTERMINALS[symbol]:
            print(f"{symbol} ::= {str(rhs)} ; \n#[length {rhs.min_tokens()}]")
        print()


