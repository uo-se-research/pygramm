# pygramm : Grammar processing in Python

Experiments in processing BNF with Python. 
Work in progress. 

## Why? 

While Ply provides a semi-yaccalike, it has some 
characteristics that bother me.  First, it prioritizes
lexical processing by the length of the pattern, 
not the length of the token ... in violation of the 
"maximum munch" rule.  Second, it tries to do everything
at run time. 

Also I want to experiment with generation of 
sentences as well as parsing, and with LL as well 
as LR parsing. 

## Work in progress

First step is just to read a grammar in BNF and try 
a bit of very simple processing. 

We want to distinguish lexical from CFG productions even for 
sentence generation because we will want different tactics for 
tokens than for RHS.  In CFG we budget for length of sentence. 
In lexical productions we choose between new and previously 
used tokens.  
