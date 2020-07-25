"""Glue together parsing and random sentence generation"""

import grammar
import llparse
import generator

f = open("data/with_comments.txt")
gram = llparse.parse(f)
budget = max(5, 2 * gram.start.min_tokens())
generator.random_sentence(gram, budget)