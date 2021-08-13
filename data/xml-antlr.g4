# An XML grammar slightly adapted from
# https://github.com/antlr/grammars-v4/tree/master/xml
#
# Modifications:
#    - parser and lexer parts combined
#    - no negated regex; no .* for "everything",
#      so we will generate some sample random text
#    - lacking "modes" (like lex "states"), we
#      will add some recursive structure to the lexer
#

# ###############################
# Parser part, from XMLParser.g4
# ###############################
# /*
#  [The "BSD licence"]
#  Copyright (c) 2013 Terence Parr
# All rights reserved.
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# */

/** XML parser derived from ANTLR v4 ref guide book example */

#parser grammar XMLParser;

# options { tokenVocab=XMLLexer; }

document    :   prolog? misc* element misc*;

prolog      :   XMLDeclOpen attribute* SPECIAL_CLOSE ;

content     :   chardata?
                ((element | reference | CDATA | PI | COMMENT) chardata?)* ;

element     :   '<' Name attribute* '>' content '<' '/' Name '>'
            |   '<' Name attribute* '/>'
            ;

reference   :   EntityRef | CharRef ;

attribute   :   Name '=' STRING ; # // Our STRING is AttValue in spec

# /** ``All text that is not markup constitutes the character data of
#  *  the document.''
#  */
chardata    :   TEXT | SEA_WS ;

misc        :   COMMENT | PI | SEA_WS ;

# ##############################
# Lexer part, from XMLLexer.g4
# ##############################

/** XML lexer derived from ANTLR v4 ref guide book example */
# lexer grammar XMLLexer;

# pygramm does not have '.', so we'll define a substitute with an
# assortment of possible values
DOT ::=  some_alpha | some_digit | some_punc | some_multibyte ;
some_alpha ::= [w-zW-Z] ;
some_digit ::= [0-9];
some_punc ::= [;,"':/];
some_multibyte ::= [\u203F-\u2040];

# Note that for generating, as versus for parsing, we don't
# need to distinguish between greedy and non-greedy repetition,
# nor do lexing states ("modes") matter.  Those are for avoiding
# ambiguity in recognizing tokens, which is not an issue in
# sentence generation.

ANY ::= DOT* ;

# We will therefore consistently replace the Antlr construct
# .*? buy ANY .


# // Default "mode": Everything OUTSIDE of a tag
COMMENT     :   '<!--' DOT* '-->' ;
CDATA       :   '<![CDATA[' ANY ']]>' ;
# /** Scarf all DTD stuff, Entity Declarations like <!ENTITY ...>,
#  *  and Notation Declarations <!NOTATION ...>
#  */
DTD         :   '<!' ANY '>'     ; #        -> skip ;
EntityRef   :   '&' Name ';' ;
CharRef     :   '&#' DIGIT+ ';'
            |   '&#x' HEXDIGIT+ ';'
            ;
SEA_WS      :   (' '|'\t'|'\r'? '\n')+ ;

# Modes (lexer states) don't matter in sentence generation.
# BUT this Antlr grammar is throwing away close symbols, so they do matter!
#
OPEN        :   '<'          ; #          -> pushMode(INSIDE) ;
XMLDeclOpen :   '<?xml' S    ; #          -> pushMode(INSIDE) ;
SPECIAL_OPEN:   '<?' Name    ; #          -> more, pushMode(PROC_INSTR) ;

# Pygramm doesn't have negated classes.  Substitute random text,
# at the cost of generating some illegal strings.
#
# TEXT        :   ~[<&]+ ;        // match any 16 bit char other than < and &
TEXT : DOT+ ;

# // ----------------- Everything INSIDE of a tag ---------------------
mode INSIDE;

CLOSE       :   '>'               ; #      -> popMode ;
SPECIAL_CLOSE:  '?>'              ; #     -> popMode ; // close <?xml...?>
SLASH_CLOSE :   '/>'              ; #     -> popMode ;
SLASH       :   '/' ;
EQUALS      :   '=' ;
STRING      :   '"' TEXT '"'
            |   "\'" TEXT "\'"
            ;
Name        :   NameStartChar NameChar* ;
S           :   [ \t\r\n]          ; #     -> skip ;

# fragment
HEXDIGIT    :   [a-fA-F0-9] ;

# fragment
DIGIT       :   [0-9] ;

# fragment
NameChar    :   NameStartChar
            |   '-' | '_' | '.' | DIGIT
            |   '\u00B7'
            |   [\u0300-\u036F]
            |   [\u203F-\u2040]
            ;

# fragment
NameStartChar
            :   [:a-zA-Z]
            |   [\u2070-\u218F]
            |   [\u2C00-\u2FEF]
            |   [\u3001-\uD7FF]
            |   [\uF900-\uFDCF]
            |   [\uFDF0-\uFFFD]
            ;

# // ----------------- Handle <? ... ?> ---------------------
# mode PROC_INSTR;

PI          :   '?>'      ; #              -> popMode ; // close <?...?>
IGNORE      :   ANY       ; #                -> more ;