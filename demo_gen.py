"""Glue together parsing and random sentence generation"""

from pygramm.llparse import *
from pygramm.generator import *
from pygramm.char_classes import  CharClasses
from pygramm.unit_productions import UnitProductions
from pygramm.grammar import FactorEmpty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# f = open("data/gram-wf-original-glade.txt")
f = open("data/gram-calc-multi-line-2020-06-04_22-59.gram.txt")
gram = parse(f)
gram.finalize()

xform = UnitProductions(gram)
xform.transform_all_rhs(gram)

xform = CharClasses(gram)
xform.transform_all_rhs(gram)

xform = FactorEmpty(gram)
xform.transform_all_rhs(gram)

log.debug(f"Grammar is {gram}")

print("*** Grammar (repr): ***")
for name in gram.symbols:
    sym = gram.symbols[name]
    print(f"{sym} ::= {repr(sym.expansions)}")
print("*** *** ***")
print("*** Grammar (str) ***")
print(gram.dump())
print("*** Generated sentence ***")
# budget = max(5, 2 * gram.start.min_tokens())
random_sentence(gram, budget=20, min_length=15)
