"""Interactive sentence generation:
User prompted for each choice.
"""

import llparse
import generator
import grammar
import random
import argparse

def cli() -> object:
    """Command line interface,
    returns an object with an attribute for each
    command line argument.
    """
    parser = argparse.ArgumentParser("Interactive sentence generator")
    parser.add_argument("grammar", type=argparse.FileType("r"),
                        help="Path to file containing BNF grammar definition"
                        )
    parser.add_argument("budget", type=int,
                        default=50,
                        help="Maximum length string to generate, default 50")
    return parser.parse_args()

def choose_from(choices: list) -> int:
    """Obtain an integer choice from user.
    Returned int should be index of choice.
    """
    while True:
        try:
            for i in range(len(choices)):
                print(f"({i}) {choices[i]}  requires {choices[i].min_tokens()}")
            choice = int(input("Your choice: "))
            if choice in range(len(choices)):
                return choices[choice]
        except Exception:
            pass
        print("Bad choice. Try again.")


def generate_sentence(g: grammar.Grammar, budget: int):
    """A generator of random sentences with external control"""
    state = generator.Gen_State(g, budget)
    while state.has_more():
        print(f"=> {state} margin/budget {state.margin}/{state.budget}")
        if state.is_terminal():
            state.shift()
        else:
            choices = state.choices()
            if len(choices) > 1:
                choice = choose_from(choices)
            else:
                choice = choices[0]
            state.expand(choice)
    print(f"Final: \n{state.text}")

def main():
    args = cli()
    gram = llparse.parse(args.grammar)
    transform = grammar.Factor_Empty(gram)
    transform.transform_all_rhs(gram)
    budget = args.budget
    generate_sentence(gram, budget)

if __name__ == "__main__":
    main()
