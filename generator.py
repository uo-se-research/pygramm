"""'Stackless' implementation of a sentence generator.
You could call it 'stackless' (there is no explicit stack of
non-terminal symbols in progress) or 'unified stack'
(the "to be expanded" list is manipulated in a FIFO
order, with no boundaries between symbols from expanding
different non-terminals).
"""

import grammar
from typing import List

import random

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Gen_State:
    """The state of sentence generation.  Each step of the
    generator transforms the state.
    We keep a prefix (already generated terminals), a suffix
    (symbols yet to be expanded), and some bookkeeping
    for the budget.
    """

    def __init__(self, gram: grammar.Grammar, budget: int):
        self.text = ""
        # Suffix is in reverse order, so that
        # we can push and pop symbols efficiently
        self.suffix: List[grammar.RHSItem] = [gram.start]
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
        return f"{self.text} @ {suffix}"


    # A single step has two parts, because we need to let a
    # an external agent control the expansion.  For
    # alternatives and symbols, part 1 is to
    # generate a set of choices, presented to the external
    # agent.  In part 2 the external agent presents the choice
    # to be taken.  If the first element of the suffix is a
    # terminal symbol, the only operation is to shift it to
    # the end of the prefix.
    #

    # Call has_more before attempting a move
    def has_more(self) -> bool:
        # We must expand BEFORE checking length,
        # because we could have a sequence of empty sequences
        while len(self.suffix) > 0 and \
                isinstance(self.suffix[-1], grammar._Seq):
            sym = self.suffix.pop()
            log.debug(f"Expanding sequence '{sym}'")
            # FIFO access order --- reversed on rest
            for el in reversed(sym.items):
                self.suffix.append(el)
        return len(self.suffix) > 0


    # Terminal symbols can only be shifted to prefix
    def is_terminal(self) -> bool:
        sym = self.suffix[-1] # FIFO access order
        return isinstance(sym, grammar._Literal)

    def shift(self):
        sym = self.suffix.pop()
        assert isinstance(sym, grammar._Literal)
        self.text += sym.text
        self.budget_used += 1

    # Non-terminal symbols, including kleene star and choices,
    # provide an opportunity for external control of options.
    # Each such element has a method to present a set of
    # choices within budget.
    def choices(self) -> List[grammar.RHSItem]:
        """The RHS elements that can be chosen
        for the next step.  (Possibly just one.)
        """
        element = self.suffix[-1]  # FIFO access
        return element.choices(self.margin + element.min_tokens())

    # External agent can pick one of the choices to replace
    # the current symbol.  Budget will be adjusted by minimum
    # cost of that expansion.
    def expand(self, expansion: grammar.RHSItem):
        sym = self.suffix.pop()
        log.debug(f"{sym} -> {expansion}")
        self.suffix.append(expansion)
        # Budget adjustment. Did we use some of the margin?
        spent = expansion.min_tokens() - sym.min_tokens()
        self.margin -= spent


def random_sentence(g: grammar.Grammar, budget: int=20):
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
            choices = state.choices()
            choice = random.choice(choices)
            log.debug(f"Choosing {choice}")
            state.expand(choice)
    print(f"Final: \n{state.text}")







