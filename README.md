# pygramm : Grammar processing in Python

PyGramm is a grammar processing package specialized for generating 
(rather than parsing) text described by BNF grammars.  It is used
in particular for grammar-based fuzzing in the tools SlackLine and 
TreeLine.

## Why? 

There are several alternatives for generating Python parsers,
including Ply, Antlr, and (our favorite) Lark.  While there are
advantages to being as compatible as possible with the grammar
syntax accepted by these tools (as well as Yacc/Bison
and CUP), the API and underlying data structures for a sentence
_generator_ differ significantly from those for a _parser_. 

- Ambiguity doesn't matter.
- Completeness might not matter, or might be counter-productive.
  For example, we probably don't want to exhaustively sample the
  space of possible integer literals.  We almost certainly don't
  want to generate all and only legal comments. 
- Some lexical rules are actually more difficult to precisely describe
  in a grammar, because of the "maximum munch" rule.  For example, 
  in a typical programming language, white space must separate an 
  identifier from a following keyword (and vice versa), but not from 
  a following punctuation mark, even though grammatically keywords 
  and punctuation are equivalent.

For fuzzing, we have a few peculiar requirements on the API: 

- We want to limit the length of generated strings.
- We might consider "length" to be the number of characters, or the 
  number of bytes, or the number of tokens.  Ideally we should be 
  able to choose. 
- We might want to generate a variant of a text we have generated 
  previously, possibly by splicing subtrees of the derivation tree,
  a la Nautilus.  And if we do, we'll still care about length. 
- We'll almost certainly want to avoid generating the same text
  repeatedly, so we'll need some (relatively cheap) way of recording 
  previously generated texts or derivation trees. 
- We might want to keep track of which previously generated texts or 
  fragments have been judged 'good' in some way in the past, e.g., 
  because they increased coverage or execution time in generated tests.

## How it works

Internal structure (`grammar.py`) represents the BNF 
  structure directly.  The Grammar object contains a list
  of symbols, each of which has a single `expansion` 
  (which could be a sequence or a choice).  The following two
  grammars will produce precisely the same internal form:
  ```
  S ::= "a";
  S ::= "b";
  ```
  and 
  ```
  S ::= "a" | "b";
  ```

A phrase generator (`generator.py`), together with some
  grammar analysis in `grammar.py`, can produce sentences
  within a given length limit (the _budget_) with or without
  direction.  See `choicebot.py` for an example of how
  grammar choices can be controlled. 

## Organization

PyGramm was initially distributed in source form, and incorporated in 
SlackLine and TreeLine as a git submodule.  That proved unwieldy because
of conflicts between typical structures of Git repositories and the 
organization assumed in Python packages.  For that reason we are now 
producing a PyPi package (installable with pip).  See the
[project organization](doc/project-structure.md)
for details, including how to extend PyGramm for your needs.
  
### To Do

Initially PyGramm uses BNF throughout, without a distinction between 
lexical and syntactic structure, although the input grammar can use 
some extensions to BNF including Kleene star (repetition).  

We anticipated from the beginning that distinguishing lexical from 
syntactic structure would probably be useful.  Experience with 
PyGramm in SlackLine and TreeLine supports this.  We think, in 
particular, that heuristics for generating new terminal symbols
(e.g., identifiers) should probably be different from those for varying 
syntactic structure.  

