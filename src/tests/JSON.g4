
/** Taken from "The Definitive ANTLR 4 Reference" by Terence Parr
 * Modified September 2023 by MY, replace lexical part with fixed choices.
*/

// Derived from https://json.org
grammar JSON;

json
   : value EOF
   ;

obj
   : '{' pair (',' pair)* '}'
   | '{' '}'
   ;

pair
   : STRING ':' value
   ;

arr
   : '[' value (',' value)* ']'
   | '[' ']'
   ;

value
   : STRING
   | NUMBER
   | obj
   | arr
   | 'true'
   | 'false'
   | 'null'
   ;

/* The remainder of the Antlr grammar is a lexical specification, described by regular expressions
 * even though the notation is BNF.  We can largely use it but omit the SAFECODEPOINT which includes
 * a negated character set.
 */

 STRING :  '"' SCHAR* '"' ;
 SCHAR :  [A-Za-z0-9#/_] | UNICODE | HEX ;


UNICODE
   : 'u' HEX HEX HEX HEX
   ;


HEX
   : [0-9a-fA-F]
   ;


NUMBER
   : '-'? INT ('.' [0-9] +)? EXP?
   ;


fragment INT
   // integer part forbids leading 0s (e.g. `01`)
   : '0' | [1-9] [0-9]*
   ;

// no leading zeros

fragment EXP
   // exponent number permits leading 0s (e.g. `1e01`)
   : [Ee] [+\-]? [0-9]+
   ;

// \- since - means "range" inside [...]

WS
   : [ \t\n\r] + -> skip
   ;
