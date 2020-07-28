"""Glue together parsing and random sentence generation"""

import grammar
import llparse
import generator

f = open("data/english.txt")
gram = llparse.parse(f)
# budget = max(5, 2 * gram.start.min_tokens())
generator.random_sentence(gram, 20)