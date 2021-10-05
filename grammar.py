"""Grammar structure
M Young, June-August 2020
"""
import re
import logging
import sys
from typing import List, Dict, Optional, Set

import pygramm.config as config

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransformBase:
    """Abstract base class for transforms.
    RHSItem objects are responsible for walking
    the tree and calling 'apply' at each node.
    For any node that should not be transformed,
    'apply' should return the node as-is, i.e.,
    if <we should do something here>:
        return <some transformation of item>
    else:
        return item
    """
    def apply(self, item: 'RHSItem') -> 'RHSItem':
        raise NotImplementedError(f"{self.__class__} needs 'apply' method")

    def setup(self, g: "Grammar"):
        """Optional setup step"""
        pass

    def teardown(self, g: "Grammar"):
        """Optional teardown step"""
        pass

    def transform_all_rhs(self, g: "Grammar"):
        """Transform RHS of each production."""
        self.setup(g)
        for name in g.symbols:
            sym = g.symbols[name]
            rhs = sym.expansions
            transformed = rhs.xform(self)
            if rhs is not transformed:
                sym.expansions = transformed
        self.teardown(g)

LB = "{"  # For LaTeXifying in f-strings
RB = "}"
def ltxesc(s: str) -> str:
    """Escape or otherwise transform characters that are special to LaTeX"""
    escapes = { # "<": "\\langle{}", ">": "\\rangle{}",
                "\\": "\\textbackslash ",  # MUST be first
                # The first six can simply be escaped ...
                "&": "\\&", "%": "\\%", "$": "\\$",
                "{": "\\{", "}": "\\}",
                "_": "\\_", "#": "\\#",
                # The remainder have special commands
                "<": "$<$", ">": "$>$",
                "|": "\\(\\mid{}\\)",
                "^": "\\textasciicircum",
                }
    for special in escapes:
        if special in s:
            s = s.replace(special, escapes[special])
    return s

class RHSItem(object):
    """Abstract base class for components of the
    right hand side of a production:
    terminal symbols, non-terminal symbols,
    choices, and repetitions (kleene stars)
    """

    def min_tokens(self) -> int:
        """Minimum length of this item in number
        of tokens.  Override in each concrete class.
        Returns CURRENT ESTIMATE of minimum length, which
        becomes accurate only after calc_min_tokens.
        """
        raise NotImplementedError("min_tokens not implemented")

    def pot_tokens(self) -> int:
        """A lower bound on the number of tokens that
        CAN be generated by this node, i.e., there must be
        some way to expand this element into at least
        pot_tokens() tokens. Override in each class.
        """
        raise NotImplementedError("pot_tokens not implemented (guaranteed potential tokens")

    def choices(self, budget: int = config.HUGE) -> List["RHSItem"]:
        """List of choices for this item."""
        raise NotImplementedError("choices not implemented")

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")

    def is_terminal(self) -> bool:
        """False for everything except literals"""
        return False

    def is_nullable(self) -> bool:
        """An item is nullable if it can expand into
        zero tokens.
        """
        return self.min_tokens() == 0

    def __str__(self) -> str:
        raise NotImplementedError(f"Missing __str__ method in {self.__class__}!")

    # Alternative to rep and str, emit for LaTeX formatting
    def latex(self) -> str:
        raise NotImplementedError(f"Missing latex method in {self.__class__}!")

    def xform(self, t: TransformBase):
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        raise NotImplementedError(f"Needs transformation hook")


class _Symbol(RHSItem):
    def __init__(self, name: str):
        self.name = name
        self._min_length = None
        self._pot_tokens = None
        self.expansions = None  # Filled in in finalization

    def __str__(self) -> str:
        return self.name

    def latex(self) -> str:
        return f"\\nonterminal{LB}{ltxesc(self.name[1:-1])}{RB}"

    def __repr__(self) -> str:
        return f"_Symbol({repr(self.name)})"

    def set_min_length(self, n_tokens: int):
        """Set by grammar.calc_min_lengths
        AFTER the full grammar has been constructed
        """
        self._min_length = n_tokens

    def min_tokens(self) -> int:
        assert self._min_length is not None, \
                "Grammar has not been finalized (_calc_min_tokens has not run)"
        return self._min_length

    def pot_tokens(self) -> int:
        assert self._pot_tokens is not None, \
                "Grammar has not been finalized (_calc_pot_tokens has not run)"
        return self._pot_tokens

    # Symbols and alternations provide a 'choices' operation
    def choices(self, budget: int = config.HUGE) -> List[RHSItem]:
        # Note 'expansions' is a single RHS item that
        # may be a '_Choice' or something else; so at this
        # point just one alternative
        return [self.expansions]

    def xform(self, t: TransformBase) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        return t.apply(self)

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")


class _Literal(RHSItem):

    def __init__(self, text: str):
        # self.text = text.encode().decode('unicode-escape')
        # Any conversion from escaped to unicode should take
        # place BEFORE we get here
        self.text = text
        #  Length, repr, and string have a non-trivial cost for
        #  unicode, which becomes problematic for big character ranges.
        #  We need to cache them and compute them only once, on demand (lazily)
        self._len_cache: Optional[int] = None
        self._repr_cache: Optional[str] = None
        self._str_cache: Optional[str] = None
        # log.debug(f"Creating new literal {self} length {len(self.text)} chars")

    def __str__(self) -> str:
        if self._str_cache is None:
            # Internal form is unicode string.  We need it
            # in a printable form.
            escaped = self.text.encode("unicode_escape").decode('ascii')
            #   Literal should already be a unicode string
            # We must further escape a quotation mark if present
            escaped = escaped.replace('"', r'\"')
            self._str_cache = f'"{escaped}"'
        return self._str_cache

    def latex(self) -> str:
        return f"\\literal{LB}{ltxesc(str(self)[1:-1])}{RB}"  # We use escaping rather than \verb||

    def __repr__(self) -> str:
        if self._repr_cache is None:
            escaped = self.text.encode("unicode_escape").decode('ascii')
            self._repr_cache = f'_Literal("{escaped}")'
        return self._repr_cache

    def _len(self):
        """We cache it because computing length of unicode literals is a non-trivial cost"""
        if self._len_cache is None:
            self._len_cache = len(bytes(self.text, 'utf-8')) if config.LEN_BASED_SIZE else 1
        return self._len_cache

    def min_tokens(self) -> int:
        return self._len()

    def pot_tokens(self) -> int:
        return self._len()

    def is_terminal(self) -> bool:
        """False for everything except literals"""
        return True

    def xform(self, t: TransformBase) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        return t.apply(self)

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")

    def choices(self, budget: int = config.HUGE) -> List["RHSItem"]:
        """List of choices for this item."""
        raise NotImplementedError("choices not implemented")


class _Seq(RHSItem):
    """Sequence of grammar items"""
    def __init__(self):
        self.items = []

    def append(self, item: RHSItem):
        self.items.append(item)

    def __str__(self) -> str:
        if len(self.items) == 0:
            return "/* empty */"
        return " ".join(str(item) for item in self.items)

    def latex(self) -> str:
        if len(self.items) == 0:
            return "\\(\\lambda\\)"
        else:
            return " ".join(item.latex() for item in self.items)

    def __repr__(self) -> str:
        items = ", ".join(repr(i) for i in self.items)
        return f"_Seq([{items}])"

    def min_tokens(self) -> int:
        return sum(item.min_tokens() for item in self.items)

    def pot_tokens(self) -> int:
        # DEBUG
        for item in self.items:
            assert item.pot_tokens() is not None, "Oops, here's the stinker"
        return sum(item.pot_tokens() for item in self.items)

    def xform(self, t: TransformBase) -> RHSItem:
        """Recursively transforms children before self"""
        for i in range(len(self.items)):
            item = self.items[i]
            transformed = item.xform(t)
            if item is not transformed:
                self.items[i] = transformed
        return t.apply(self)

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")

    def choices(self, budget: int = config.HUGE) -> List["RHSItem"]:
        """List of choices for this item."""
        raise NotImplementedError("choices not implemented")


class _Kleene(RHSItem):
    """Repetition"""
    def __init__(self, child: RHSItem):
        self.child = child
        # In prep for choices method,
        # A* == (AA*)|(/* empty */)
        self._base_case = _Seq()
        self._recursive_case = _Seq()
        self._recursive_case.append(self.child)
        self._recursive_case.append(self)

    def __str__(self) -> str:
        return f"({str(self.child)})*"

    def latex(self) -> str:
        return f"\\Kleene{LB}{str(self.child)}{RB}"

    def __repr__(self) -> str:
        return f"_Kleene({repr(self.child)})"

    def min_tokens(self) -> int:
        """Could be repeated 0 times"""
        return 0

    def pot_tokens(self) -> int:
        """If the repeated phrase ensures any tokens at all,
        then we can repeat it to ensure as many tokens as we need
        """
        if self.child.pot_tokens() > 0:
            return config.HUGE
        return 0

    # A* is like choice between empty and AA*
    def choices(self, budget: int = config.HUGE) -> List["RHSItem"]:
        if budget >= self.child.min_tokens():
            return [self._recursive_case, self._base_case]
        else:
            return [self._base_case]

    def xform(self, t: TransformBase) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        transformed = self.child.xform(t)
        if self.child is not transformed:
            self.child = transformed
        return t.apply(self)

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")


class _Choice(RHSItem):

    def __init__(self):
        self.items: List[RHSItem] = []

    def append(self, item: RHSItem):
        self.items.append(item)

    def __str__(self) -> str:
        terms = [str(item) for item in self.items]
        # Fits on one line?
        disjunct_str = " | ".join(terms)
        if len(disjunct_str) < 70:
            return f"({disjunct_str})"
        # Otherwise break it up, one line per choice.
        disjunct_str = "\n\t| ".join(terms)
        return f"( {disjunct_str})"

    def latex(self) -> str:
        disjunct_str = " \\OR ".join(item.latex() for item in self.items)
        return f"{disjunct_str}"

    def __repr__(self) -> str:
        choices = ", ".join(repr(i) for i in self.items)
        return f"_Choice([{choices}])"

    def min_tokens(self) -> int:
        return min(item.min_tokens() for item in self.items)

    def pot_tokens(self) -> int:
        return  max(item.pot_tokens() for item in self.items)

    def choices(self, budget: int = config.HUGE) -> List["RHSItem"]:
        return [item for item in self.items if item.min_tokens() <= budget]

    def xform(self, t: TransformBase) -> RHSItem:
        """Recursively transforms children before self"""
        for i in range(len(self.items)):
            item = self.items[i]
            transformed = item.xform(t)
            if item is not transformed:
                self.items[i] = transformed
        return t.apply(self)

    def expand(self, choice: int = 0) -> List["RHSItem"]:
        """Return the chosen expansion"""
        raise NotImplementedError("expand not implemented")


class _CharRange(_Choice):
    """A choice that was specified as a character range,
    e.g., [a-zA-Z].
    """

    def __init__(self, desc=None):
        super().__init__()
        self.desc = desc
        # Cache and lazily compute min and potential tokens
        self._min_len_cache: Optional[int] = None
        self._pot_len_cache: Optional[int] = None

    def min_tokens(self) -> int:
        # We can cache because the elements are literals,
        # whose length never changes.
        if self._min_len_cache is None:
            self._min_len_cache = min(item.min_tokens() for item in self.items)
        return self._min_len_cache

    def pot_tokens(self) -> int:
        # We can cache because the elements are literals,
        # whose length never changes
        if self._pot_len_cache is None:
            self._pot_len_cache = max(item.pot_tokens() for item in self.items)
        return self._pot_len_cache

    # Print as character range if the original description
    # was given
    def __str__(self) -> str:
        if self.desc:
            return self.desc
        else:
            return super().__str__(self)


class Grammar(object):
    """A grammar is a collection of productions.
    Productions are indexed by non-terminal
    symbols.
    """
    def __init__(self, file_name: str, max_lower_bound=1000):
        """max_lower_bound is the largest *lower bound* we will
        place on the number of tokens in a generated sentence,
        i.e., when we calculate the number of tokens that we
        ensure each symbol can produce, we will assume that anything
        bigger than this can essentially grow to infinity.
        """

        self.gram_name = file_name
        self.ready = False  # Pre-processing done
        self.start: Optional[_Symbol] = None   # Replace with start symbol

        # Merges maps each element of a merge to the
        # representative ("leader") of that merge
        self.merges: Dict[str, str] = dict()

        # Interning (a la Lisp 'intern', Java string tables):  We keep
        # a single representative node for each unique
        # literal and symbol. (Later we may merge identical
        # subtrees.
        self.symbols: Dict[str, _Symbol] = dict()
        self.literals: Dict[str, _Literal] = dict()

        # Parsing BNF produces two tables,
        #  mapping non-terminal symbols to productions
        #  and terminal symbols to strings.
        # Productions is now a temporary and internal
        # variable --- finalization puts the expansion of
        # each item into the _Symbol objects in self.symbols
        #
        self._productions: Dict[str, list] = dict()
        self.max_lower_bound = max_lower_bound

    def add_cfg_prod(self, lhs: _Symbol, rhs: list):
        if self.start is None:
            self.start = lhs
        lhs_ident = lhs.name
        if lhs_ident not in self._productions:
            self._productions[lhs_ident] = []
        self._productions[lhs_ident].append(rhs)

    def dump(self) -> str:
        """Dump the grammar to str with annotation"""
        gram = ""
        for sym_name in self.symbols:
            sym = self.symbols[sym_name]
            gram += f"# {sym_name}, min length {self.symbols[sym_name].min_tokens()}\n"
            gram += f"{sym_name} ::= {sym.expansions} ;\n"
            gram += "\n"
        return gram

    def dump_stdout(self):
        """Dump the grammar to stdout with annotation"""
        print(self.dump())

    def latex(self):
        gram_l = ["\\begin{grammar}"]
        for sym_name in self.symbols:
            sym = self.symbols[sym_name]
            gram_l.append(f"{sym.latex()} " +
                          f"&\\raggedright {sym.expansions.latex()} ;\\tabularnewline")
        gram_l.append("\\end{grammar}")
        return "\n".join(gram_l)

    def merge_symbols(self, symbols: List[str]):
        """Each of the symbols will be mapped to a
        an already chosen leader or to a newly elected
        leader from the list.
        """
        leader = None
        for ident in symbols:
            if ident in self.merges:
                # Use existing unique leader
                if leader is None:
                    leader = self.merges[ident]
                else:
                    assert leader == self.merges[ident]
        if leader is None:
            # Elect new leader
            leader = symbols.pop()
        for ident in symbols:
            if ident != leader:
                self.merges[ident] = leader

    # Each of the subclasses of RHS have a factory method in Grammar.
    # This allows us to instantiate them in the context of a particular
    # Grammar object.  In particular, it allows us merge symbols before
    # instantiating.

    def symbol(self, name: str) -> _Symbol:
        """Unique node for a symbol with this name, after merging"""
        if name in self.merges:
            leader = self.merges[name]
            log.debug(f"Converting {name} to {leader}")
            name = leader
        if name not in self.symbols:
            self.symbols[name] = _Symbol(name)
        return self.symbols[name]

    def literal(self, text: str):
        """Unique node for this literal string"""
        # text = text.encode().decode('unicode-escape')
        # Do the unicode encoding earlier!
        # Must be done only once so that "\\" gets interpreted
        # only once.
        if text not in self.literals:
            self.literals[text] = _Literal(text)
        return self.literals[text]

    @staticmethod
    def seq():
        return _Seq()

    @staticmethod
    def kleene(child: RHSItem):
        return _Kleene(child)

    @staticmethod
    def choice():
        return _Choice()

    # For sentence generation, we need to know the minimum length
    # of a phrase generated for each non-terminal symbol.

    def _calc_min_tokens(self):
        """Calculate the minimum length of each non-terminal,
        updating the initial estimate of HUGE.
        """
        # We will iterate *down* to a fixed point from an
        # initial over-estimate of phrase length
        for name in self.symbols:
            self.symbols[name].set_min_length(config.HUGE)
        changed = True
        # Iterate to fixed point
        while changed:
            log.debug("\n*** Iterating calc_min_tokens ***\n")
            changed = False
            for name in self.symbols:
                sym = self.symbols[name]
                # log.debug(f"Inspecting symbol {sym}")
                prior_estimate = sym.min_tokens()
                new_estimate = sym.expansions.min_tokens()
                if new_estimate < prior_estimate:
                    changed = True
                    sym.set_min_length(new_estimate)
                    log.debug(f"< {new_estimate} (was {prior_estimate}) for {sym}")
                elif new_estimate > prior_estimate:
                    log.debug(f"> {new_estimate} (was {prior_estimate}) for {sym}!")
                else:
                    log.debug(f"= {new_estimate} (was {prior_estimate}) for {sym}")
        # Sanity check:  Did we find a length for each symbol?
        for name in self.symbols:
            assert self.symbols[name].min_tokens() < config.HUGE, \
                    f"Failed to find min length for symbol '{name}'"
            # Should never fail, but ...

        # For sentence generation, we may also want to set lower
        # bounds on sentence length, and n.pot_tokens() == k
        # tells us that this symbol CAN be expanded to at least
        # k tokens.

    def _calc_pot_tokens(self):
        """Calculate a guarantee of the number of tokens that
        is potentially available from each symbol.
        """

        # We will iterate *up* to a fixed point from an
        # initial under-estimate of phrase length
        for name in self.symbols:
            self.symbols[name]._pot_tokens = 0
        changed = True
        # Iterate to fixed point
        while changed:
            changed = False
            for name in self.symbols:
                sym = self.symbols[name]
                prior_estimate = sym.pot_tokens()
                new_estimate = sym.expansions.pot_tokens()
                if new_estimate > self.max_lower_bound:
                    new_estimate = config.HUGE
                if new_estimate > prior_estimate:
                    changed = True
                    sym._pot_tokens = new_estimate

        # Sanity check:  Did we find a length for each symbol?
        for name in self.symbols:
            assert self.symbols[name].min_tokens() < config.HUGE, \
                f"Failed to find min length for {name}"
            # Should never fail, but ...

    def finalize(self):
        """Operations that should be performed on a grammar after all
        productions have been added, and before the grammar is used
        to generate sentences, printed, etc.
        """
        # Connect non-terminals to their right-hand-sides,
        # creating a new _Choice node for non-terminals that
        # have multiple productions.
        for name in self._productions:
            symbol = self.symbols[name]
            expansions = self._productions[name]
            if len(expansions) == 1:
                symbol.expansions = expansions[0]
            elif len(expansions) > 1:
                choices = _Choice()
                for choice in expansions:
                    choices.append(choice)
                self.symbols[name].expansions = choices
        # List ALL symbols without productions
        incomplete = False
        for name, sym in self.symbols.items():
            if sym.expansions is None:
                print(f"*** No productions for {name}", file=sys.stderr)
                incomplete = True
        if incomplete:
            raise Exception(f"Grammar is not complete")
        # Do not use self._productions further; the master copy
        # is in the expansions member of each symbol
        self._productions = []
        # For generation with "budgets" (length limits), we also
        # need to know the minimum number of tokens produced by
        # each non-terminal (and so indirectly by each production)
        self._calc_min_tokens()
        self._calc_pot_tokens()

class GrammarDiagnostics:
    """Helper class for diagnosing and improving grammars,
    e.g., by reporting and/or removing unused symbols.
    """
    def __init__(self, gram: Grammar):
        self.gram = gram

    # Notes on walking the grammar:  We could implement an __iter__ method
    # in each RHS item, but if we did, should the _Symbol class iterate
    # its expansions or not?  Should we build the cycle detection into the
    # walk or not?  Since it is not currently obvious which is the "one right way"
    # to do it, we'll put the walk we need for reachability here (like a "friend"
    # class in C++, although that's not a Python concept) and dispatch on
    # node type.

    def reachable(self) -> Set[_Symbol]:
        """Which non-terminal symbols in the grammar are reachable?"""
        visited = set()
        def walk(item: RHSItem):
            if isinstance(item, _Symbol):
                if item in visited:
                    return
                visited.add(item)
                walk(item.expansions)
            elif isinstance(item,_Seq):
                for e in item.items:
                    walk(e)
            elif isinstance(item, _Choice):
                for e in item.items:
                    walk(e)
            elif isinstance(item, _Kleene):
                walk(item.child)
            elif isinstance(item, _Literal):
                return
            else:
                raise Exception(f"Oops, no walker for {type(item)} ")
        walk(self.gram.start)
        return visited

    def unreachable(self) -> Set[_Symbol]:
        """Which symbols are unreachable?"""
        can_reach: Set[_Symbol] = self.reachable()
        cannot_reach : Set[_Symbol] = set()
        for name, sym in self.gram.symbols.items():
            if sym not in can_reach:
                cannot_reach.add(sym)
        return cannot_reach

    def prune_unreachable(self):
        """Prune unreachable symbols from grammar"""
        symbols = list(self.gram.symbols)
        keep = self.reachable()
        for name, sym in list(self.gram.symbols.items()):
            if sym not in keep:
                del self.gram.symbols[name]
        return


class FactorEmpty(TransformBase):
    """Add a new symbol EMPTY that is used in place
    of any empty sequence on the right-hand-side of a
    production.
    """
    def __init__(self, g: Grammar):
        self.sym = g.symbol("EMPTY")
        self.sym.set_min_length(0)
        # But this one must not be transformed!
        self.sym.expansions = _Literal("DUMMY LITERAL")

    def apply(self, item: 'RHSItem') -> 'RHSItem':
        if isinstance(item, _Seq) and len(item.items) == 0:
            return self.sym
        else:
            return item

    def teardown(self, g: Grammar):
        """Fix AFTER transformation so that we
        don't transform this single instance of
        the empty sequence.
        """
        self.sym.expansions = _Seq()
        g._calc_min_tokens()
        g._calc_pot_tokens()
