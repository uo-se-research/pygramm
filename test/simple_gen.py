"""Simple smoke test for generated tokens"""

import sys
sys.path.append("../..")

from src import grammar, generator


def gen_x() -> str:
    """Simplest possible generating function"""
    return "x"

def main():
    # S ::= I | S I
    gram = grammar.Grammar("no file")
    gram.add_cfg_prod(gram.symbol("S"),
                      gram.symbol("I"))
    recursive = gram.seq()
    recursive.append(gram.symbol("S"))
    recursive.append(gram.symbol("I"))
    gram.add_cfg_prod(gram.symbol("S"),
                      recursive)
    gram.add_cfg_prod(gram.symbol("I"),
                      grammar.FGenerated(gen_x))

    gram.finalize()

    for i in range(10):
        txt = generator.random_sentence(gram)


if __name__ == "__main__":
    main()

