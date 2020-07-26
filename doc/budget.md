# The logic of phrase generation budgets

When we generate a sentence or phrase 
from a sequence of grammar symbols, 
we want to do so within a given budget. 
The budget could be in characters or in 
number of tokens; the only difference 
would be in how we count literals.  Here
we will consider a budget in number 
of tokens. 

## Minimum budgets 

We want to associate with each sequence 
of symbols a *minimum* number of tokens
it must generate.  We can define 
*minbud(s)* recursively:

* *minbud(L) == 1* if L is a literal
* *minbud(A|B) == min(minbud(A), minbud()B)*
* *minbud(S) == sum(minbud(E) for E in S)* if S
  is a sequence.  Note in particular that this 
  gives a budget of 0 for an empty sequence. 
* *minbud(A`*`) == 0* because A could be 
  repeated zero times.  Note this is equivalent to 
  treating A`*` as (AA`*`|/* empty */).
* If A is a non-terminal symbol, then 
  minbud(A) is min(minbud(P) for A -> P)
 
Because a grammar can be recursive, the last
rule could trigger an infinite recursive loop
if we coded it directly.  This can be 
avoided by iterating to a fixed point. 
We begin by assigning each non-terminal a 
very large initial estimate, then repeatedly 
evaluate the last rule without recursion. 
When the estimated minimum budgets for 
each non-terminal symbol do not change, 
the fixed point has been reached, 
and the estimate will be the 
actual minimum budget for each non-terminal. 

# Budgets while generating

We maintain a budget while generating
text from the grammar.  At each step in 
generation, we have a string of 
tokens that has been generated, and a
string of grammar symbols that remain
to be processed, which we will call
the suffix. The invariant we will
maintain is that if the entire budget 
were expended on the first symbol 
in the suffix, we could still stay within
the total original budget by generating
a minimum length string for each of 
the remaining symbols. 

Initially we allocate the whole budget
to the start symbol.  This establishes
the invariant:  If we spent the whole 
budget on the start symbol, we would 
have enough left for the zero symbols
that follow it in the suffix. 

The budget is adjusted when we choose 
an expansion of a symbol or phrase. 
The symbol or phrase has a minimum budget
*m*, and we have a budget *b* to spend
on it.  *b* must be at least *m* if
we have not made a mistake. We consider 
only choices that are at most *b*. 
If we choose *c*, then we reduce the 
budget by *minbud(c) - m*.  

This preserves the invariant.  No other
adjustments are necessary. 

Consider the case that we chose the
shortest expansion *c*.  In this case 
we do not adjust the remaining budget 
at all.  It was adequate for the rest
of the suffix before, and it is still adequate. 

Suppose we instead made a choice *c* 
that has a minbud greater than the minbud
of the symbol or phrase we are replacing. 
It is still less than *b*, so the remaining 
*b* after adjustment is still adequate for 
the suffix. 

If the suffix is ABC, we can think 
of the difference between the current 
budget and minbud(A) as excess capacity. 
The only adjustment we ever need make is 
to account for having used some of this
excess.  Any excess that is not used 
is effectively passed on to be used by 
the next symbol.

(Is this right?  It does not make
sense to me now.)
