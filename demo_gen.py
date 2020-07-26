"""Glue together parsing and random sentence generation"""

import grammar
import llparse
import generator

f = open("data/gram-calc-recursive-2020-06-04_23-31.gram.txt")
gram = llparse.parse(f)
# budget = max(5, 2 * gram.start.min_tokens())
generator.random_sentence(gram, 80)