"""Glue together parsing and random sentence generation"""

from pygramm.llparse import parse
from pygramm.char_classes import  CharClasses
from pygramm.unit_productions import UnitProductions
from pygramm.grammar import FactorEmpty, GrammarDiagnostics

import sys
import argparse

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def cli():
    parser = argparse.ArgumentParser("Prune grammar")
    parser.add_argument("input", type=argparse.FileType("r"), nargs="?",
                        default=sys.stdin)
    parser.add_argument("output", type=argparse.FileType("w"), nargs="?",
                        default=sys.stdout)
    args = parser.parse_args()
    return args

def main():
    args = cli()
    gram = parse(args.input)
    gram.finalize()

    xform = UnitProductions(gram)
    xform.transform_all_rhs(gram)

    xform = CharClasses(gram)
    xform.transform_all_rhs(gram)

    xform = FactorEmpty(gram)
    xform.transform_all_rhs(gram)

    pruner = GrammarDiagnostics(gram)
    reachable = pruner.reachable()
    log.info(f"*** Reachable symbols: {reachable}")
    unreachable = pruner.unreachable()
    log.info(f"***Unreachable symbols: {unreachable}")
    pruner.prune_unreachable()
    print(gram.dump(), file=args.output)

if __name__ == "__main__":
    main()
