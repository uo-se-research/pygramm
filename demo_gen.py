"""Glue together parsing and random sentence generation"""

import grammar
import llparse
import generator
import binary_choice

f = open("data/gram-calc-multi-line-2020-06-04_22-59.gram.txt")
gram = llparse.parse(f)

# xform = grammar.Factor_Empty(gram)
# xform.transform_all_rhs(gram)

binarize = binary_choice.Binary_Choices(gram)
binarize.transform_all_rhs(gram)

print("*** Grammar (repr): ***")
for name in gram.symbols:
    sym = gram.symbols[name]
    print(f"{sym} ::= {repr(sym.expansions)}")
print("*** *** ***")
# budget = max(5, 2 * gram.start.min_tokens())
generator.random_sentence(gram, 20)