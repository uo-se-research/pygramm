"""Glue together parsing and random sentence generation"""

from pygramm.grammar import Factor_Empty
from pygramm.llparse import *
from pygramm.generator import *

f = open("data/english.txt")
gram = parse(f)
xform = Factor_Empty(gram)
xform.transform_all_rhs(gram)
print("*** Grammar (repr): ***")
for name in gram.symbols:
    sym = gram.symbols[name]
    print(f"{sym} ::= {repr(sym.expansions)}")
print("*** *** ***")
# budget = max(5, 2 * gram.start.min_tokens())
random_sentence(gram, 20)
