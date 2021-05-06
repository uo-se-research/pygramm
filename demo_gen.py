"""Glue together parsing and random sentence generation"""

from pygramm.grammar import FactorEmpty
from pygramm.llparse import *
from pygramm.generator import *
from pygramm.binary_choice import Binary_Choices

# f = open("data/english.txt")
# gram = parse(f)
# xform = FactorEmpty(gram)
# xform.transform_all_rhs(gram)

f = open("data/simple_seq.txt")
gram = parse(f)
log.debug(f"Grammar is {gram}")

# xform = grammar.FactorEmpty(gram)
# xform.transform_all_rhs(gram)

binarize = Binary_Choices(gram)
binarize.transform_all_rhs(gram)

print("*** Grammar (repr): ***")
for name in gram.symbols:
    sym = gram.symbols[name]
    print(f"{sym} ::= {repr(sym.expansions)}")
print("*** *** ***")
# budget = max(5, 2 * gram.start.min_tokens())
random_sentence(gram, budget=20, min_length=15)
