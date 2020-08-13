"""Glue together parsing and random sentence generation"""

import grammar
import llparse
import generator

f = open("data/english.txt")
gram = llparse.parse(f)
print("*** Grammar (repr): ***")
for sym in gram.productions:
    for production in gram.productions[sym]:
        print(f"{sym} ::= {repr(production)}")
print("*** *** ***")
# budget = max(5, 2 * gram.start.min_tokens())
generator.random_sentence(gram, 20)