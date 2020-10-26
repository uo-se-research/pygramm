"""Grammar structure
M Young, June-August 2020
"""
import logging

from typing import List, Dict, Optional

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


HUGE = 999_999_999   # Larger than any sentence we will generate


class Transform_Base:
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
        """Transform RHS of each production.  Does
        not prune productions (yet).
        """
        self.setup(g)
        for name in g.symbols:
            sym = g.symbols[name]
            rhs = sym.expansions
            transformed = rhs.xform(self)
            if rhs is not transformed:
                sym.expansions = transformed
        self.teardown(g)


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

    def choices(self, budget: int = HUGE) -> List["RHSItem"]:
        """List of choices for this item.
        FIXME: What does a sequence return?  First item or
        whole sequence?  
        """
        raise NotImplementedError("n_choices not implemented")

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

    def xform(self, t: Transform_Base):
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        raise NotImplementedError(f"Needs transformation hook")


class _Symbol(RHSItem):
    def __init__(self, name: str):
        self.name = name
        self._min_length = None
        self.expansions = []  # Filled in in finalization

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"_Symbol({repr(self.name)})"

    def set_min_length(self, n_tokens: int):
        """Set by grammar.calc_min_lengths
        AFTER the full grammar has been constructed
        """
        self._min_length = n_tokens

    def min_tokens(self) -> int:
        assert self._min_length is not None, \
                "Grammar.min_lengths must be called after grammar construction"
        return self._min_length

    # Symbols and alternations provide a 'choices' operation
    def choices(self, budget: int) -> List[RHSItem]:
        # Note 'expansions' is a single RHS item that
        # may be a '_Choice' or something else; so at this
        # point just one alternative
        return [self.expansions]

    def xform(self, t: Transform_Base) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        return t.apply(self)


class _Literal(RHSItem):

    def __init__(self, text: str):
        self.text = text

    def __str__(self) -> str:
        return f'"{self.text}"'

    def __repr__(self) -> str:
        return f'_Literal("{self.text}")'

    def min_tokens(self) -> int:
        return 1

    def is_terminal(self) -> bool:
        """False for everything except literals"""
        return True

    def xform(self, t: Transform_Base) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        return t.apply(self)


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

    def __repr__(self) -> str:
        items = ", ".join(repr(i) for i in self.items)
        return f"_Seq([{items}])"

    def min_tokens(self) -> int:
        return sum(item.min_tokens() for item in self.items)

    def xform(self, t: Transform_Base) -> RHSItem:
        """Recursively transforms children before self"""
        for i in range(len(self.items)):
            item = self.items[i]
            transformed = item.xform(t)
            if item is not transformed:
                self.items[i] = transformed
        return t.apply(self)


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

    def __repr__(self) -> str:
        return f"_Kleene({repr(self.child)})"

    def min_tokens(self) -> int:
        """Could be repeated 0 times"""
        return 0

    # A* is like choice between empty and AA*
    def choices(self, budget: int) -> List["RHSItem"]:
        if budget >= self.child.min_tokens():
            return [self._recursive_case, self._base_case]
        else:
            return [self._base_case]

    def xform(self, t: Transform_Base) -> RHSItem:
        """Apply the transformation x to node.
        Should walk (postorder) and then apply.
        """
        transformed = self.child.xform(t)
        if self.child is not transformed:
            self.child = transformed
        return t.apply(self)


class _Choice(RHSItem):

    def __init__(self):
        self.items: List[RHSItem] = []

    def append(self, item: RHSItem):
        self.items.append(item)

    def __str__(self) -> str:
        disjunct_str = " | ".join(str(item) for item in self.items)
        return f"({disjunct_str})"

    def __repr__(self) -> str:
        choices = ", ".join(repr(i) for i in self.items)
        return f"_Choice([{choices}])"

    def min_tokens(self) -> int:
        return min(item.min_tokens() for item in self.items)

    def choices(self, budget: int) -> List["RHSItem"]:
        return [item for item in self.items    \
                if item.min_tokens() <= budget]

    def xform(self, t: Transform_Base) -> RHSItem:
        """Recursively transforms children before self"""
        for i in range(len(self.items)):
            item = self.items[i]
            transformed = item.xform(t)
            if item is not transformed:
                self.items[i] = transformed
        return t.apply(self)


class Grammar(object):
    """A grammar is a collection of productions.
    Productions are indexed by non-terminal
    symbols.
    """
    def __init__(self):
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

    def add_cfg_prod(self, lhs: _Symbol, rhs: list):
        if self.start is None:
            self.start = lhs
        lhs_ident = lhs.name
        if not lhs_ident in self._productions:
            self._productions[lhs_ident] = []
        self._productions[lhs_ident].append(rhs)

    def dump(self):
        """Dump the grammar to stdout with annotation"""
        for sym_name in self.symbols:
            sym = self.symbols[sym_name]
            print(f"# {sym_name}, min length {self.symbols[sym_name].min_tokens()}")
            print(f"{sym_name} ::= {sym.expansions}")
            print()

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
        if text not in self.literals:
            self.literals[text] = _Literal(text)
        return self.literals[text]

    def seq(self):
        return _Seq()

    def kleene(self, child: RHSItem):
        return _Kleene(child)

    def choice(self):
        return _Choice()

    # For sentence generation, we need to know the minimum length
    # of a phrase generated for each non-terminal symbol.

    def _calc_min_tokens(self):
        """Calculate the minimum length of each non-terminal,
        updating the initial estimate of HUGE.  This 
        """
        # We will iterate *down* to a fixed point from an
        # initial over-estimate of phrase length
        for name in self.symbols:
            self.symbols[name].set_min_length(HUGE)
        changed = True
        # Iterate to fixed point
        while changed:
            changed = False
            for name in self.symbols:
                sym = self.symbols[name]
                prior_estimate = sym.min_tokens()
                new_estimate = sym.expansions.min_tokens()
                if new_estimate < prior_estimate:
                    changed = True
                    sym.set_min_length(new_estimate)
        # Sanity check:  Did we find a length for each symbol?
        for name in self.symbols:
            assert self.symbols[name].min_tokens() < HUGE, \
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
            else:
                raise Exception(f"No productions for {name}")
        # Do not use self._productions further; the master copy
        # is in the expansions member of each symbol
        self._productions = []
        # For generation with "budgets" (length limits), we also
        # need to know the minimum number of tokens produced by
        # each non-terminal (and so indirectly by each production)
        self._calc_min_tokens()


class Factor_Empty(Transform_Base):
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
