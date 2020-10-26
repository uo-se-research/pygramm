"""'Stackless' implementation of a sentence generator.
You could call it 'stackless' (there is no explicit stack of
non-terminal symbols in progress) or 'unified stack'
(the "to be expanded" list is manipulated in a FIFO
order, with no boundaries between symbols from expanding
different non-terminals).
"""

from pygramm.grammar import Grammar, RHSItem, _Seq, _Literal
from typing import List

import random

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Close(RHSItem):
    """A pseudo-element that marks the end of an RHS
    expansion, allowing us to integrate a stack into the
    the stackless representation.
    When we expand an RHSItem into a sequence of RHSItems,
    we will mark the end of the sequence with a Close.
    """
    def __init__(self, lhs: RHSItem, expansion: RHSItem):
        self.construct = lhs
        self.expansion = expansion

    # We leave unimplemented some methods that other RHS items must have;
    # we never expand a Close into another construct.

    def __str__(self) -> str:
        """Not shown in standard representation of parse state"""
        return ""


class Gen_State:
    """The state of sentence generation.  Each step of the
    generator transforms the state.
    We keep a prefix (already generated terminals), a suffix
    (symbols yet to be expanded), and some bookkeeping
    for the budget.
    2020-07-29: Adding a stack on the side while retaining
    "almost stackless" representation.
    """

    def __init__(self, gram: Grammar, budget: int):
        self.text = ""
        # Suffix is in reverse order, so that
        # we can push and pop symbols efficiently
        self.suffix: List[RHSItem] = [gram.start]
        # A stack of constructs that are currently being expanded.
        self.stack: List[RHSItem] = []
        # The full budget for a generated sentence; does not change
        self.budget = budget
        # The budget margin, initially for the start symbol.
        # Adjusted with each expansion.
        self.margin = budget - gram.start.min_tokens()
        # And for good measure we'll keep track of how much
        # we've actually generated.  At the end, self.budget_used
        # + self.margin should equal self.budget
        self.budget_used = 0

    def __str__(self) -> str:
        """Looks like foobar @ A(B|C)*Dx,8"""
        suffix = "".join([str(sym) for sym in reversed(self.suffix)])
        # stack = "\n".join([f"[{sym}" for sym in self.stack])
        return f"{self.text} @ {suffix}"

    def _open_nonterm(self, item: RHSItem):
        """We are currently working on this item"""
        self.stack.append(item)

    def _close_nonterm(self):
        """Done working on some item"""
        self.stack.pop()

    def stack_state_str(self) -> str:
        """The stack state is not shown by __str__; use stack_state_str
        to see the entire state
        """
        indent = "   |"  # Indentation for each level
        repr = ""
        level = 0
        for frame in self.stack:
            repr += f"{level * indent}{frame}\n"
            level += 1
        repr += level * indent
        for item in self.suffix:
            if isinstance(item, Close):
                level -= 1
                repr += f"\n{level * indent}"
            else:
                repr += str(item)
        return repr

    # A single step has two parts, because we need to let a
    # an external agent control the expansion.  For
    # alternatives and symbols, part 1 is to
    # generate a set of choices, presented to the external
    # agent.  In part 2 the external agent presents the choice
    # to be taken.  If the first element of the suffix is a
    # terminal symbol, the only operation is to shift it to
    # the end of the prefix.
    # Added 2020-07-29:  'Close' symbols mark the end of
    # a production and trigger popping an element from
    # a stack of currently open RHS elements.  The stack is
    # for bookkeeping only; it does not otherwise affect
    # generation of sentences.
    #

    # Call has_more before attempting a move
    def has_more(self) -> bool:
        """Are there more symbols to shift or expand?
        Called BEFORE a call to choose; side effect of
        sliding past Close symbols and expanding _Seq symbols
        to get to the symbol to consider.
        """
        while len(self.suffix) > 0:
            # Slide over Close and expand _Seq
            sym = self.suffix[-1]
            if isinstance(sym, _Seq):
                self.suffix.pop()
                log.debug(f"Expanding sequence '{sym}'")
                # FIFO access order --- reversed on rest
                for el in reversed(sym.items):
                    self.suffix.append(el)
            elif isinstance(sym, Close):
                self._close_nonterm()
                self.suffix.pop()
            else:
                break
        return len(self.suffix) > 0

    # Terminal symbols can only be shifted to prefix
    def is_terminal(self) -> bool:
        sym = self.suffix[-1]  # FIFO access order
        return isinstance(sym, _Literal)

    def shift(self):
        sym = self.suffix.pop()
        assert isinstance(sym, _Literal)
        self.text += sym.text
        self.budget_used += 1

    # Non-terminal symbols, including kleene star and choices,
    # provide an opportunity for external control of options.
    # Each such element has a method to present a set of
    # choices within budget.
    def choices(self) -> List[RHSItem]:
        """The RHS elements that can be chosen
        for the next step.  (Possibly just one.)
        """
        element = self.suffix[-1]  # FIFO access
        return element.choices(self.margin + element.min_tokens())

    # External agent can pick one of the choices to replace
    # the current symbol.  Budget will be adjusted by minimum
    # cost of that expansion.
    def expand(self, expansion: RHSItem):
        sym = self.suffix.pop()
        log.debug(f"{sym} -> {expansion}")
        self._open_nonterm(sym)
        self.suffix.append(Close(sym, expansion))
        self.suffix.append(expansion)
        # Budget adjustment. Did we use some of the margin?
        spent = expansion.min_tokens() - sym.min_tokens()
        self.margin -= spent


def random_sentence(g: Grammar, budget: int = 20,
                    interpret_escapes: bool = False):
    """A generator of random sentences, without external control"""
    while g.start.min_tokens() > budget:
        log.info(f"Bumping budget by minimum requirement {g.start.min_tokens()}")
        budget += g.start.min_tokens()
    state = Gen_State(g, budget)
    print(f"Initially {state}")
    while state.has_more():
        print(f"=> {state} margin/budget {state.margin}/{state.budget}")
        if state.is_terminal():
            state.shift()
        else:
            print(state.stack_state_str())
            choices = state.choices()
            choice = random.choice(choices)
            log.debug(f"Choosing {choice}")
            state.expand(choice)
    txt = state.text
    if interpret_escapes:
        txt = txt.encode().decode('unicode-escape')
    print(f"Final: \n{state.text}")
