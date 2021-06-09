"""A substitute for random.choice that (choose from a list) with learnable bias.
Keeps a side table of weights which can be incremented (rewarded) or decremented (penalized)
and biases future choices toward those biases.
"""
import random
from typing import List

class _BiasCore:
    """Core shared state of the biased chooser.  When a chooser is
    forked, we keep a reference to this part.
    """

    def __init__(self, default_weight=0.5, initial_weights={},
                 reward_delta=0.05, penalty_delta=0.05):
        assert 0.0 < default_weight < 1.0, "default weights must be in open interval 0.0..1.0"
        self.default_weight = default_weight
        self.weights = initial_weights.copy()
        assert 0.0 < reward_delta < 1.0
        assert 0.0 < penalty_delta < 1.0
        self.reward_delta = reward_delta
        self.penalty_delta = penalty_delta

    def weight(self, item: object, context=None) -> float:
        """Current weight of an item, initialized if needed.
        (Context ignored in this version, but can be overridden
        in a subclass.)
        """
        if item not in self.weights:
            self.weights[item] = self.default_weight
        return self.weights[item]

    def choose(self, choices: List[object], context=None):
        """Make a biased choice among choices."""
        if not choices:
            return None
        sum_weight = sum(self.weight(item, context) for item in choices)
        r = random.random()  # In open interval 0.0 .. 1.0
        bound = 0.0  # Sum of adjusted weights so far
        for choice in choices:
            bound += self.weight(choice, context) / sum_weight
            if r <= bound:
                return choice
        # Infinitessimal possibility of roundoff error
        return choices[-1]

    def reward(self, item: object):
        """Choose this one more often"""
        old_weight = self.weight(item)
        new_weight = old_weight + self.reward_delta * (1.0 - old_weight)
        self.weights[item] = new_weight

    def penalize(self, item: object):
        """Choose this one less often"""
        old_weight = self.weight(item)
        new_weight = old_weight - self.penalty_delta * old_weight
        self.weights[item] = new_weight


class _BigramCore(_BiasCore):
    """Biased chooser core that keeps track of bigrams
    in addition to individual items.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bigram_weights = {}
        # If we have a recorded preference for a bigram, how
        # should we combine it with the weight for the individual
        # item?
        self.bigram_priority = 0.9

    def weight(self, item: object, context=None) -> float:
        """Current weight of an item, initialized if needed."""
        bigram = (context, item)
        if item not in self.weights:
            self.weights[item] = self.default_weight
        item_weight = self.weights[item]
        if bigram not in self.bigram_weights:
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

    def __init__(self, default_weight=0.5, initial_weights={},
                 reward_delta=0.05, penalty_delta=0.05, forked=False):
        if not forked:
            self.core = _BiasCore(default_weight, initial_weights,
                                  reward_delta, penalty_delta)
            self.history = []

    def fork(self) -> 'Bias':
        forked = Bias()
        forked.core = self.core
        forked.history = self.history.copy()
        return forked

    def weight(self, item: object) -> float:
        """Current weight of an item, initialized if needed."""
        return self.core.weight(item)

    def choose(self, choices: List[object]):
        """Make a biased choice among choices."""
        choice = self.core.choose(choices)
        self.history.append(choice)
        return choice

    def reward(self):
        """These were good choices"""
        for item in self.history:
            self.core.reward(item)

    def penalize(self):
        """Choose this one less often"""
        for item in self.history:
            self.core.penalize(item)


class BigramBias(Bias):
    """Provides a 'choice' method like random.choice but weighted.
    Choices must be hashable.  Bigrams:  Context is one prior item. 
    """

    def __init__(self, default_weight=0.5, initial_weights={},
                 reward_delta=0.05, penalty_delta=0.05, forked=False):
        if not forked:
            self.core = _BigramCore(default_weight, initial_weights,
                                  reward_delta, penalty_delta)
            self.history = []

    def fork(self) -> 'BigramBias':
        forked = BigramBias()
        forked.core = self.core
        forked.history = self.history.copy()
        return forked

    def weight(self, item: object, context=None) -> float:
        """Current weight of an item, initialized if needed."""
        return self.core.weight(item, context)

    def choose(self, choices: List[object]):
        """Make a biased choice among choices."""
        prior = None
        if self.history:
            prior = self.history[-1]
        choice = self.core.choose(choices, prior)
        self.history.append(choice)
        return choice

    def reward(self):
        """These were good choices"""
        prior = None
        for item in self.history:
            self.core.reward(item, prior=prior)
            prior = item

    def penalize(self):
        """Choose this one less often"""
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
    #chooser = Bias(reward_delta=0.25, penalty_delta=0.25)
    root_chooser = BigramBias()
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




