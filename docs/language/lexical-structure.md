# Kaj Lexical Structure

**Status:** Authoritative for the current Kaj v0 implementation  
**Scope:** Pure language core — lexical analysis only

This document defines how Kaj source text is divided into tokens before parsing.

Unless this document is explicitly updated, the lexer implementation and lexer conformance tests must follow these rules.

---

## 1. Purpose

The Kaj lexer transforms source text into a sequence of tokens.

```text
Kaj source text
    ↓
Lexer
    ↓
Token stream
    ↓
Parser
```

Example source:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Conceptual token stream:

```text
FN
IDENTIFIER("add")
LEFT_PAREN
IDENTIFIER("a")
COLON
IDENTIFIER("Int")
COMMA
IDENTIFIER("b")
COLON
IDENTIFIER("Int")
RIGHT_PAREN
ARROW
IDENTIFIER("Int")
LEFT_BRACE
RETURN
IDENTIFIER("a")
PLUS
IDENTIFIER("b")
RIGHT_BRACE
EOF
```

The lexer does not decide whether a sequence of otherwise valid tokens forms a valid Kaj program. That is the parser's responsibility.

---

## 2. Source Encoding

Kaj source files are Unicode text and should be read as UTF-8.

The canonical source file extension is:

```text
.kaj
```

Strings may contain Unicode text.

For Kaj v0, identifiers are restricted to ASCII characters as defined later in this document.

---

## 3. Source Locations

Every token and lexical diagnostic must contain a source span.

A source location consists of:

```text
offset
line
column
```

Rules:

```text
offset    zero-based
line      one-based
column    one-based
```

The first source character is therefore:

```text
offset = 0
line   = 1
column = 1
```

---

## 4. Source Spans

A source span contains:

```text
start
end
```

Spans use half-open interval semantics:

```text
[start, end)
```

The start is inclusive and the end is exclusive.

For source text:

```text
let
```

the offsets are:

```text
start.offset = 0
end.offset   = 3
```

This allows spans to map directly onto source slices.

---

## 5. Whitespace

The following are whitespace:

```text
space
tab
carriage return
newline
```

Whitespace separates tokens but does not produce tokens.

For example:

```kaj
let x = 10
let y = 20
```

and:

```kaj
let x = 10 let y = 20
```

produce equivalent token sequences.

Whether both are valid programs is a parser concern.

---

## 6. Newlines

Newlines are whitespace, not syntax tokens.

Kaj does not use indentation or newline tokens to define blocks.

Blocks are delimited by braces:

```kaj
if condition {
    do_work()
}
```

The lexer must still update line and column information when encountering newlines.

Kaj v0 accepts `\n`, `\r`, and `\r\n` line endings. A `\r\n` pair counts as one logical
line break, advances the source offset by two, and resets the column to one.

---

## 7. Tabs

Tabs are whitespace.

For Kaj v0 source tracking:

> A tab advances the source column by exactly one.

The lexer does not attempt to calculate editor-specific visual tab width.

---

## 8. Semicolons

Semicolons are not required by Kaj syntax.

Kaj v0 does not define semicolon-based statement termination, and the lexer must not invent implicit semicolon tokens from newlines.

---

## 9. Identifiers

Kaj v0 identifiers use:

```text
[A-Za-z_][A-Za-z0-9_]*
```

Valid examples:

```kaj
foo
user
user_name
_result
foo2
ParserState
```

Invalid identifier starts include:

```text
2foo
@user
$value
```

---

## 10. Unicode Identifiers

Unicode identifiers are deferred.

For Kaj v0:

```kaj
let café = 1
```

is not a valid identifier under the lexical grammar.

Unicode remains valid inside strings.

---

## 11. Keywords

After scanning an identifier lexeme, the lexer checks it against the keyword table.

Kaj v0 keywords:

```text
let
var
fn
return

if
else
while
for
in

break
continue

true
false
none

and
or
not

type
enum
newtype
match

import
```

Keyword matching is exact and case-sensitive.

Example:

```text
let     -> LET
letter  -> IDENTIFIER("letter")
Let     -> IDENTIFIER("Let")
```

---

## 12. Reserved Future Words

Do not reserve speculative future keywords.

In particular, these agent/capability terms are not lexer keywords yet:

```text
task
step
goal
success
require
invariant
expect
verify
observe
ask
choose
confirm
inform
handoff
use
uses
```

They may become keywords only when their language features are formally introduced.

---

## 13. Boolean Literals

Kaj defines:

```kaj
true
false
```

They produce:

```text
TRUE
FALSE
```

Their semantic type is handled later.

---

## 14. None Literal

Kaj uses:

```kaj
none
```

which produces:

```text
NONE
```

Its relationship to `Optional<T>` is a semantic/type-system concern.

---

## 15. Integer Literals

Kaj v0 supports unsigned decimal integer literals:

```text
DIGIT+
```

where `DIGIT` is `0-9`.

Valid examples:

```kaj
0
1
10
123456
999999999999999999999999999999
```

Kaj `Int` is intended to support arbitrary precision, so the lexer must not impose machine-width integer limits.

---

## 16. Negative Numbers

Negative numbers are not single lexer tokens.

```kaj
-42
```

must produce:

```text
MINUS
INTEGER("42")
```

Negation is parser-level unary syntax.

The same rule applies to:

```kaj
-value
-foo()
a - 42
```

---

## 17. Decimal Literals

Kaj v0 supports unsigned decimal literals of the form:

```text
DIGIT+ "." DIGIT+
```

Valid:

```kaj
0.0
0.5
3.14
10.0
100.125
```

Invalid in Kaj v0:

```text
1.
.5
1.2.3
```

Decimal literals represent Kaj's exact decimal numeric category.

The lexer must not convert them through binary floating-point.

---

## 18. Deferred Numeric Syntax

These forms are deferred:

```text
1_000
0xff
0b1010
0o755
1e6
1.0e-3
42f32
42f64
```

They are not part of Kaj v0.

---

## 19. Numeric Token Values

Tokens may carry both `lexeme` and parsed `value`.

Example:

```text
INTEGER
lexeme = "123"
value  = 123
```

For decimals:

```text
DECIMAL
lexeme = "19.99"
value  = exact decimal representation of 19.99
```

Precision must not be lost.

---

## 20. String Literals

Kaj v0 strings use double quotes:

```kaj
"hello"
```

Strings may contain Unicode:

```kaj
"Hello"
"বাংলা"
"你好"
"👋"
```

A string token should preserve both its source lexeme and decoded value.

---

## 21. String Escapes

Kaj v0 supports:

```text
\"    double quote
\\    backslash
\n    newline
\r    carriage return
\t    tab
```

Example:

```kaj
"hello\nworld"
```

Unknown escapes are lexical errors.

Example:

```kaj
"\q"
```

must produce:

```text
LEX_INVALID_ESCAPE
```

---

## 22. Unterminated Strings

A string beginning with `"` must end with a matching `"` before a raw newline or EOF.

Example:

```kaj
"hello
```

must produce:

```text
LEX_UNTERMINATED_STRING
```

The lexer must not crash.

---

## 23. Raw Newlines in Ordinary Strings

Ordinary double-quoted strings do not span source lines in Kaj v0.

This is invalid:

```kaj
"hello
world"
```

and must produce:

```text
LEX_UNTERMINATED_STRING
```

Multiline string syntax is deferred.

---

## 24. String Interpolation

String interpolation is not lexically interpreted in Checkpoint 1.

```kaj
"Hello, {name}"
```

is one `STRING` token whose decoded value is:

```text
Hello, {name}
```

Interpolation semantics may be added later.

---

## 25. Multiline Strings

Triple-quoted or other multiline string syntax is deferred.

---

## 26. Bytes Literals

Kaj includes a `Bytes` type in the broader design, but Kaj v0 does not define bytes literal syntax.

Do not assume syntax such as:

```text
b"hello"
```

until explicitly specified.

---

## 27. Line Comments

Line comments begin with:

```text
//
```

and continue to the end of the current line.

Example:

```kaj
// comment
let x = 10
```

Comments do not produce parser-visible tokens.

---

## 28. Block Comments

Block comments begin with:

```text
/*
```

and end with:

```text
*/
```

Example:

```kaj
/*
comment
*/
let x = 10
```

They may span multiple lines and are skipped by the lexer.

---

## 29. Nested Block Comments

Nested block comments are not supported in Kaj v0.

The first `*/` terminates the active block comment.

---

## 30. Unterminated Block Comments

If EOF is reached before a block comment closes, emit:

```text
LEX_UNTERMINATED_COMMENT
```

The lexer must not crash.

---

## 31. Comment Preservation

Comments are skipped by the Kaj v0 parser-visible token stream.

Future formatter work may introduce separate trivia/comment preservation.

Checkpoint 1 must not complicate the token stream solely for that future requirement.

---

## 32. Punctuation Tokens

Kaj v0 recognizes:

```text
(    LEFT_PAREN
)    RIGHT_PAREN

{    LEFT_BRACE
}    RIGHT_BRACE

[    LEFT_BRACKET
]    RIGHT_BRACKET

,    COMMA
:    COLON
.    DOT
```

---

## 33. Arithmetic Operators

Kaj v0 recognizes:

```text
+    PLUS
-    MINUS
*    STAR
/    SLASH
%    PERCENT
**   STAR_STAR
```

Longest-match rules apply.

---

## 34. Assignment and Equality Operators

Kaj v0 recognizes:

```text
=     EQUAL
==    EQUAL_EQUAL
!=    BANG_EQUAL
```

Longest-match rules apply.

---

## 35. Comparison Operators

Kaj v0 recognizes:

```text
<     LESS
<=    LESS_EQUAL
>     GREATER
>=    GREATER_EQUAL
```

---

## 36. Compound Assignment Operators

Kaj v0 tokenizes:

```text
+=    PLUS_EQUAL
-=    MINUS_EQUAL
*=    STAR_EQUAL
/=    SLASH_EQUAL
```

Tokenization does not itself guarantee semantic validity in every context.

---

## 37. Arrow Tokens

Kaj recognizes:

```text
->    ARROW
=>    FAT_ARROW
```

The lexer only identifies them; parser rules determine their meaning.

---

## 38. Boolean Operators

Kaj uses keyword boolean operators:

```kaj
and
or
not
```

Kaj v0 does not define these symbolic alternatives:

```text
&&
||
!
```

A standalone unsupported `!` is invalid unless it participates in `!=`.

---

## 39. Longest-Match Rule

When token forms share a prefix, consume the longest valid token.

Examples:

```text
== before =
!= before unsupported !
<= before <
>= before >
+= before +
-= before -
*= before *
/= before /
** before *
-> before -
=> before =
```

---

## 40. Token Representation

A token conceptually contains:

```text
kind
lexeme
span
value
```

Representative implementation shape:

```python
@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    span: SourceSpan
    value: object | None = None
```

The exact Python representation is internal, but this information must be available.

---

## 41. Initial Token Kinds

### Special

```text
EOF
```

### Literals

```text
INTEGER
DECIMAL
STRING
```

### Identifier

```text
IDENTIFIER
```

### Keywords

```text
LET
VAR
FN
RETURN

IF
ELSE
WHILE
FOR
IN

BREAK
CONTINUE

TRUE
FALSE
NONE

AND
OR
NOT

TYPE
ENUM
NEWTYPE
MATCH

IMPORT
```

### Punctuation

```text
LEFT_PAREN
RIGHT_PAREN
LEFT_BRACE
RIGHT_BRACE
LEFT_BRACKET
RIGHT_BRACKET
COMMA
COLON
DOT
```

### Operators

```text
PLUS
MINUS
STAR
SLASH
PERCENT
STAR_STAR

EQUAL
EQUAL_EQUAL
BANG_EQUAL

LESS
LESS_EQUAL
GREATER
GREATER_EQUAL

PLUS_EQUAL
MINUS_EQUAL
STAR_EQUAL
SLASH_EQUAL

ARROW
FAT_ARROW
```

---

## 42. EOF

Every tokenization must terminate with exactly one:

```text
EOF
```

The EOF token may use a zero-width span at the end-of-source location.

---

## 43. Invalid Characters

A character that cannot begin or continue a valid token must produce:

```text
LEX_INVALID_CHARACTER
```

Example:

```kaj
let x = @
```

The diagnostic should span `@`.

The lexer should recover and continue where reasonably possible.

---

## 44. Invalid Numbers

Malformed numeric sequences recognized as invalid numeric syntax must produce:

```text
LEX_INVALID_NUMBER
```

Examples include:

```text
1.
1.2.3
```

The lexer should avoid silently splitting clearly malformed numeric forms in a way that conceals the error.

---

## 45. Lexical Diagnostics

Checkpoint 1 defines at least these stable diagnostic codes:

```text
LEX_INVALID_CHARACTER
LEX_UNTERMINATED_STRING
LEX_INVALID_ESCAPE
LEX_INVALID_NUMBER
LEX_UNTERMINATED_COMMENT
```

Messages may improve over time, but diagnostic codes should remain stable unless deliberately revised.

Every lexical diagnostic must include a source span.

---

## 46. Error Recovery

Lexical errors should not normally terminate the compiler process.

The lexer should attempt to continue after recoverable errors so multiple diagnostics can be reported.

Conceptually:

```text
source
  ↓
lexer
  ├── tokens
  └── diagnostics
```

---

## 47. Lexer API Expectations

The implementation should support behavior conceptually equivalent to:

```python
lexer = Lexer(source, filename="example.kaj")
result = lexer.tokenize()
```

with:

```text
result.tokens
result.diagnostics
```

The exact implementation type is internal.

---

## 48. Example Tokenizations

### Binding

```kaj
let x = 10
```

```text
LET
IDENTIFIER("x")
EQUAL
INTEGER("10")
EOF
```

### Mutable binding

```kaj
var price = 19.99
```

```text
VAR
IDENTIFIER("price")
EQUAL
DECIMAL("19.99")
EOF
```

### Function

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

```text
FN
IDENTIFIER("add")
LEFT_PAREN
IDENTIFIER("a")
COLON
IDENTIFIER("Int")
COMMA
IDENTIFIER("b")
COLON
IDENTIFIER("Int")
RIGHT_PAREN
ARROW
IDENTIFIER("Int")
LEFT_BRACE
RETURN
IDENTIFIER("a")
PLUS
IDENTIFIER("b")
RIGHT_BRACE
EOF
```

### Condition

```kaj
if x >= 10 and x != 20 {
    print("hello")
}
```

```text
IF
IDENTIFIER("x")
GREATER_EQUAL
INTEGER("10")
AND
IDENTIFIER("x")
BANG_EQUAL
INTEGER("20")
LEFT_BRACE
IDENTIFIER("print")
LEFT_PAREN
STRING(""hello"")
RIGHT_PAREN
RIGHT_BRACE
EOF
```

### Comments

```kaj
// comment
let x = 10 /* another comment */
```

```text
LET
IDENTIFIER("x")
EQUAL
INTEGER("10")
EOF
```

### Unary Minus

```kaj
let x = -42
```

```text
LET
IDENTIFIER("x")
EQUAL
MINUS
INTEGER("42")
EOF
```

---

## 49. Invalid Examples

### Invalid Character

```kaj
let x = @
```

```text
LEX_INVALID_CHARACTER
```

### Invalid Escape

```kaj
let x = "\q"
```

```text
LEX_INVALID_ESCAPE
```

### Unterminated String

```kaj
let x = "hello
```

```text
LEX_UNTERMINATED_STRING
```

### Unterminated Comment

```kaj
/* comment
```

```text
LEX_UNTERMINATED_COMMENT
```

---

## 50. Deferred Lexical Features

The following are explicitly outside Kaj v0 Checkpoint 1:

```text
Unicode identifiers
multiline string literals
string interpolation tokenization
raw strings
bytes literals
hexadecimal literals
binary literals
octal literals
numeric separators
scientific notation
floating-point suffixes
nested block comments
documentation-comment tokenization
formatter trivia preservation
semicolon insertion
indentation-sensitive syntax
```

These must not be added opportunistically during implementation.

---

## 51. Implementation Invariants

The Checkpoint 1 lexer must satisfy these invariants:

1. Every parser-visible source token has a valid source span.
2. Source spans are start-inclusive and end-exclusive.
3. Offsets are zero-based.
4. Lines and columns are one-based.
5. Newlines are whitespace, not tokens.
6. Comments are skipped.
7. Negative numbers use a separate `MINUS` token.
8. Decimal literals are never converted through binary floating point.
9. Keyword matching is exact and case-sensitive.
10. Longest valid token matching is used for operators.
11. Lexical failures produce structured diagnostics rather than arbitrary runtime exceptions.
12. Tokenization ends with exactly one `EOF`.
13. Deferred lexical features are not implemented without updating this specification.

---

## 52. Conformance Expectations

Checkpoint 1 should test at least:

```text
source locations
source spans

identifiers
keyword recognition
keyword-prefix identifiers

integers
arbitrary-size integers
decimals
negative-number tokenization
invalid numeric syntax

strings
Unicode string contents
supported escapes
invalid escapes
unterminated strings

punctuation
single-character operators
multi-character operators
longest-match behavior

line comments
block comments
unterminated block comments

whitespace
newlines
tabs

invalid characters
error recovery

exactly one EOF token
EOF source span
```

---

## 53. Source of Truth

For Kaj v0 lexical behavior:

```text
docs/language/lexical-structure.md
        +
lexer conformance tests
        +
lexer implementation
```

must agree.

If they disagree, that inconsistency is a Kaj project bug.

Changes to lexical behavior should update this document and the corresponding tests.

---

## 54. Checkpoint 1 Definition of Done

```text
[ ] SourceLocation exists
[ ] SourceSpan exists

[ ] TokenKind exists
[ ] Token exists

[ ] identifiers are tokenized
[ ] keywords are recognized
[ ] integers are tokenized
[ ] decimals are tokenized
[ ] strings are tokenized

[ ] punctuation is tokenized
[ ] operators are tokenized
[ ] longest-match behavior is correct

[ ] whitespace is skipped
[ ] newlines are skipped while updating locations
[ ] line comments are skipped
[ ] block comments are skipped

[ ] source offsets are correct
[ ] line numbers are correct
[ ] column numbers are correct
[ ] spans are end-exclusive

[ ] lexer emits structured diagnostics
[ ] invalid characters are diagnosed
[ ] invalid escapes are diagnosed
[ ] unterminated strings are diagnosed
[ ] invalid numbers are diagnosed
[ ] unterminated comments are diagnosed

[ ] lexer recovers from reasonable lexical errors
[ ] every tokenization ends with exactly one EOF token

[ ] lexer tests pass
[ ] pytest passes
[ ] ruff passes
[ ] mypy passes
```

Once these requirements are satisfied, Kaj can proceed to the AST and parser checkpoints without redefining basic lexical behavior.
