"""Glue together parsing and random sentence generation"""

from pygramm.grammar import Factor_Empty
from pygramm.llparse import *
from pygramm.generator import *
from pygramm.binary_choice import Binary_Choices

f = open("data/english.txt")
gram = parse(f)
xform = Factor_Empty(gram)
xform.transform_all_rhs(gram)

f = open("data/gram-calc-multi-line-2020-06-04_22-59.gram.txt")
gram = parse(f)

# xform = grammar.Factor_Empty(gram)
# xform.transform_all_rhs(gram)

binarize = Binary_Choices(gram)
binarize.transform_all_rhs(gram)

print("*** Grammar (repr): ***")
for name in gram.symbols:
    sym = gram.symbols[name]
    print(f"{sym} ::= {repr(sym.expansions)}")
print("*** *** ***")
# budget = max(5, 2 * gram.start.min_tokens())
random_sentence(gram, 20)
