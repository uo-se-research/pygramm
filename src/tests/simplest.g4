// Simplest possible Antlr grammar, developed incrementally

Start: Text?;
Text: "this"* | ("that" "thing" "there")+;

