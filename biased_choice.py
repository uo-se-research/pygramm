"""A substitute for random.choice that (choose from a list) with learnable bias.
Keeps a side table of weights which can be incremented (rewarded) or decremented (penalized)
and biases future choices toward those biases.
"""
import random
from typing import List

# Tuning constants
#
# The weight that all items start at.  Must be in open interval
# 0.0 .. 1.0.  I can't think of a reason that this would change.
DEFAULT_WEIGHT = 0.5
#
# Default learning rates.  Move current weight what fraction of the way from its
# current value toward 1.0 (if reward) or 0.0 (if penalty).  Small values will learn
# slowly, large values will oscillate.  If rewards are rare, we might want a penalty
# delta that is smaller than the reward delta.
REWARD_DELTA = 0.05
PENALTY_DELTA = 0.05
#
# If we have a bigram xa, and we also have a weight for a regardless of
# prior, how much of the weight value should depend on the bigram weight?
# Since we see individual items more often than we see bigrams, this should
# probably not be 1.0.
BIGRAM_PRIORITY = 0.8

class _BiasCore:
    """Core shared state of the biased chooser.  When a chooser is
    forked, we keep a reference to this part (i.e., it is shared
    among all Bias objects forked from an initial Bias object).
    """

    def __init__(self,
                 default_weight=DEFAULT_WEIGHT,
                 reward_delta=REWARD_DELTA,
                 penalty_delta=PENALTY_DELTA,
                 bigram_priority = BIGRAM_PRIORITY):
        assert 0.0 < default_weight < 1.0, "default weights must be in open interval 0.0..1.0"
        self.default_weight = default_weight
        assert 0.0 < reward_delta < 1.0
        self.reward_delta = reward_delta
        assert 0.0 < penalty_delta < 1.0
        self.penalty_delta = penalty_delta
        self.bigram_priority = bigram_priority
        self.weights = {}
        self.bigram_weights = {}

    def choose(self, choices: List[object], prior=None):
        """Make a biased choice among choices."""
        if not choices:
            return None
        sum_weight = sum(self.weight(item, prior) for item in choices)
        r = random.random()  # In open interval 0.0 .. 1.0
        bound = 0.0  # Sum of adjusted weights so far
        for choice in choices:
            bound += self.weight(choice, prior) / sum_weight
            if r <= bound:
                return choice
        # Infinitessimal possibility of roundoff error
        return choices[-1]

    def weight(self, item: object, prior=None) -> float:
        """Current weight of an item, initialized if needed."""
        bigram = (prior, item)
        if item not in self.weights:
            self.weights[item] = self.default_weight
        item_weight = self.weights[item]
        if bigram not in self.bigram_weights:
            # Haven't seen it in this context; depend on its
            # overall weight from all contexts in which we've seen it.
            return self.weights[item]
        bi_weight = self.bigram_weights[bigram]
        return self.bigram_priority * bi_weight + (1 - self.bigram_priority) * item_weight


    def reward(self, item: object, prior: object=None):
        """Choose this one / this pair more often"""
        old_weight = self.weight(item)
        new_weight = old_weight + self.reward_delta * (1.0 - old_weight)
        self.weights[item] = new_weight
        if not prior:
            # No bigram
            return
        # Record a weight for the bigram
        bigram = (prior, item)
        if bigram in self.bigram_weights:
            old_weight = self.bigram_weights[bigram]
        else:
            old_weight = self.default_weight
        new_weight = old_weight + self.reward_delta * (1.0 - old_weight)
        self.bigram_weights[bigram] = new_weight

    def penalize(self, item: object=None, prior: object=None):
        """Choose this one / these less often"""
        old_weight = self.weight(item)
        new_weight = old_weight - self.penalty_delta * old_weight
        self.weights[item] = new_weight
        if not prior:
            return
        bigram = (prior, item)
        if bigram in self.bigram_weights:
            old_weight = self.bigram_weights[bigram]
        else:
            old_weight = self.default_weight
        new_weight = old_weight - self.penalty_delta * old_weight
        self.bigram_weights[bigram] = new_weight


class Bias:
    """Provides a 'choice' method like random.choice but weighted.
    Choices must be hashable.
    """


    def __init__(self,
                default_weight = DEFAULT_WEIGHT,
                reward_delta = REWARD_DELTA,
                penalty_delta = PENALTY_DELTA,
                bigram_priority = BIGRAM_PRIORITY,
                forked=False):
        if not forked:
            self.core = _BiasCore(default_weight,  reward_delta, penalty_delta, bigram_priority)
            self.history = []

    def fork(self) -> 'Bias':
        forked = Bias(forked=True)
        forked.core = self.core
        forked.history = self.history.copy()
        return forked

    def choose(self, choices: List[object]):
        """Make a biased choice among choices."""
        choice = self.core.choose(choices)
        self.history.append(choice)
        return choice

    def reward(self):
        """These were good choices; make them more often"""
        prior = None
        for item in self.history:
            self.core.reward(item, prior=prior)
            prior = item

    def penalize(self):
        """These were not good choices; avoid them"""
        prior = None
        for item in self.history:
            self.core.penalize(item, prior=prior)
            prior = item



def main():
    """Smoke test, biases letter choice toward end of alphabet.
    We should see random words tend toward later letters after
    a few hundred iterations.
    """
    letters = list("abcdefghijklmnopqrstuvwxyz")
    root_chooser = Bias()
    for epoch in range(100):
        for word in range(1000):
            chooser = root_chooser.fork()
            word_letters = []
            for pos in range(3):   ### Length of word, critical parameter
                xl = chooser.choose(letters)
                word_letters.append(xl)
            word = "".join(word_letters)
            ### Here the reward depends only on the first character,
            ### but we reward bigrams rather than individual characters. 
            if word > "p":
                for letter in word_letters:
                    chooser.reward()
            elif word < "k":
                for letter in word_letters:
                    chooser.penalize()
        print(word)
    print(chooser.core.weights)
    bigram_weights = list(chooser.core.bigram_weights.items())
    print(sorted(bigram_weights))

if __name__ == "__main__":
    main()




