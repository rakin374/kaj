# Kaj Checkpoint 1 — Source Locations, Tokens, and Lexer

**Audience:** Codex / implementation agent  
**Repository:** Kaj  
**Checkpoint:** 1  
**Goal:** Implement lexical analysis for the pure Kaj language core.

## Primary instruction

Implement Kaj Checkpoint 1 completely.

The authoritative specification is:

```text
docs/language/lexical-structure.md
```

Read that file before making implementation decisions. If this brief conflicts with it, `docs/language/lexical-structure.md` wins.

Do **not** begin parser or AST implementation during this checkpoint.

## Goal

At the end of this checkpoint, Kaj must transform raw `.kaj` source text into a token stream with exact source spans and structured lexical diagnostics.

```text
Kaj source
    ↓
source tracking
    ↓
lexer
    ↓
tokens + diagnostics
```

Example:

```kaj
let price = -19.99
```

must become conceptually:

```text
LET
IDENTIFIER("price")
EQUAL
MINUS
DECIMAL("19.99")
EOF
```

The lexer does not build an AST and does not decide program semantics.

## Scope

Implement only:

- source locations and spans
- structured lexical diagnostics
- token kinds and token values
- keyword recognition
- identifiers
- integers
- decimals
- strings and escapes
- punctuation
- operators
- comments
- whitespace handling
- source-position tracking
- lexical error recovery
- EOF handling
- automated tests

Do not implement:

- parser
- AST
- name resolution
- type checking
- interpreter/runtime
- formatter
- string interpolation semantics
- multiline strings
- Unicode identifiers
- bytes literals
- hex/binary/octal numbers
- scientific notation
- agent keywords
- capabilities
- tasks/effects
- asset-language features

## Required structure

Create or use:

```text
src/
└── kaj/
    ├── __init__.py
    ├── source/
    │   ├── __init__.py
    │   └── span.py
    ├── diagnostics/
    │   ├── __init__.py
    │   └── diagnostic.py
    └── lexer/
        ├── __init__.py
        ├── token.py
        └── lexer.py

tests/
├── source/
│   └── test_span.py
└── lexer/
    ├── test_identifiers.py
    ├── test_keywords.py
    ├── test_numbers.py
    ├── test_strings.py
    ├── test_operators.py
    ├── test_comments.py
    ├── test_locations.py
    ├── test_diagnostics.py
    └── test_lexer.py
```

If a compatible diagnostics structure already exists, reuse it rather than creating duplication. Do not create placeholder packages for future checkpoints.

## SourceLocation

Implement an immutable model equivalent to:

```python
@dataclass(frozen=True)
class SourceLocation:
    offset: int
    line: int
    column: int
```

Rules:

```text
offset = zero-based
line   = one-based
column = one-based
```

The first character is:

```text
offset=0, line=1, column=1
```

## SourceSpan

Implement an immutable model equivalent to:

```python
@dataclass(frozen=True)
class SourceSpan:
    start: SourceLocation
    end: SourceLocation
```

Spans are half-open:

```text
[start, end)
```

For `let` at the beginning of the file:

```text
start.offset = 0
end.offset   = 3
```

Never use inclusive end positions.

## Source identity

The lexer should be able to retain a filename/source label:

```python
Lexer(source, filename="example.kaj")
```

Do not require the lexer itself to read from disk. It operates on source text supplied by callers.

## Diagnostic model

Implement a small structured diagnostic value with at least:

```text
code
message
span
```

A suitable shape is:

```python
@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    span: SourceSpan
```

Normal malformed Kaj input must not surface as arbitrary Python exceptions.

Required stable codes:

```text
LEX_INVALID_CHARACTER
LEX_UNTERMINATED_STRING
LEX_INVALID_ESCAPE
LEX_INVALID_NUMBER
LEX_UNTERMINATED_COMMENT
```

Tests should primarily assert codes and spans, not exact prose.

## TokenKind

Implement a `TokenKind` enum with these required kinds.

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

Do not add speculative agent keywords.

## Token model

Implement an immutable token equivalent to:

```python
@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    span: SourceSpan
    value: object | None = None
```

Requirements:

- `kind`: lexical category
- `lexeme`: exact source substring
- `span`: exact source range
- `value`: decoded/parsed value where useful

Examples:

```text
INTEGER
lexeme="123"
value=123
```

```text
STRING
lexeme=""hello""
value="hello"
```

Preserve the original lexeme.

## LexerResult

Return tokens and diagnostics together.

Prefer a structure equivalent to:

```python
@dataclass(frozen=True)
class LexerResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic]
```

The lexer should not stop at the first recoverable lexical error.

## Lexer API

Provide behavior conceptually equivalent to:

```python
lexer = Lexer(source, filename="example.kaj")
result = lexer.tokenize()

result.tokens
result.diagnostics
```

Keep the external API small.

## Position advancement

Centralize character advancement so offset/line/column updates are not duplicated throughout the lexer.

Ordinary character:

```text
offset += 1
column += 1
```

Newline:

```text
offset += 1
line += 1
column = 1
```

Tab:

```text
offset += 1
column += 1
```

Handle `\n`, `\r`, and `\r\n` predictably. If CRLF is treated as one logical line break, do so consistently and test it.

## Whitespace

Skip:

```text
space
tab
carriage return
newline
```

Do not emit whitespace or newline tokens. Do not implement indentation semantics or semicolon insertion.

## Identifiers

Implement:

```text
[A-Za-z_][A-Za-z0-9_]*
```

Examples:

```text
foo
user_name
_result
foo2
ParserState
```

Scan the complete identifier first, then check the keyword table.

Do not implement Unicode identifiers.

## Keywords

Use one centralized mapping such as:

```python
KEYWORDS: dict[str, TokenKind] = {
    "let": TokenKind.LET,
    ...
}
```

Keyword matching is exact and case-sensitive:

```text
let     -> LET
letter  -> IDENTIFIER
Let     -> IDENTIFIER
LET     -> IDENTIFIER
```

Do not use a large repeated `if/elif` chain for keyword recognition.

## Integers

Implement unsigned base-10 integers:

```text
[0-9]+
```

Python `int` is appropriate and provides arbitrary precision.

Do not impose 32-bit or 64-bit limits.

## Negative numbers

A leading minus is always a separate token.

```kaj
-42
```

must be:

```text
MINUS
INTEGER
```

and:

```kaj
-3.14
```

must be:

```text
MINUS
DECIMAL
```

Unary negation belongs to the parser.

## Decimals

Implement:

```text
DIGIT+ "." DIGIT+
```

Examples:

```text
0.0
0.5
3.14
10.0
```

Use `decimal.Decimal` from the original lexeme.

Correct:

```python
Decimal("19.99")
```

Do not convert through `float`.

## Invalid numbers

The spec rejects:

```text
1.
.5
1.2.3
```

Report:

```text
LEX_INVALID_NUMBER
```

for malformed numeric forms.

Do not silently tokenize `1.` as `INTEGER("1")` + `DOT` if it is clearly a malformed decimal attempt.

Likewise, do not silently split `1.2.3` into a misleading valid sequence.

Choose a deterministic recovery strategy and test it.

Do not extend numeric syntax beyond the spec.

Deferred numeric forms include:

```text
1_000
0xff
0b1010
0o755
1e6
1.0e-3
```

## Strings

Implement ordinary double-quoted strings:

```kaj
"hello"
```

Store:

```text
lexeme = exact source spelling including quotes
value  = decoded contents
```

Unicode contents are valid:

```kaj
"hello"
"বাংলা"
"你好"
"👋"
```

## String escapes

Support exactly:

```text
"    double quote
\    backslash

    newline
    carriage return
	    tab
```

Unknown escapes produce:

```text
LEX_INVALID_ESCAPE
```

A reasonable recovery strategy is to report the bad escape and continue scanning the same string until closing quote/newline/EOF.

## Unterminated strings

Ordinary strings cannot contain raw source newlines.

Both a newline before the closing quote and EOF before the closing quote produce:

```text
LEX_UNTERMINATED_STRING
```

The lexer must recover without crashing.

## String interpolation

Do not implement interpolation yet.

```kaj
"Hello, {name}"
```

must remain one `STRING` token. The braces and identifier inside it are not separately tokenized.

## Deferred string/bytes syntax

Do not implement:

- multiline strings
- raw strings
- triple-quoted strings
- bytes literal syntax

## Line comments

Implement:

```kaj
// comment
```

Continue until newline or EOF. Skip comments entirely from the parser-visible token stream.

## Block comments

Implement:

```kaj
/*
comment
*/
```

They may span lines and must update source positions correctly.

Nested block comments are **not** supported. The first `*/` closes the active comment.

EOF before closing `*/` produces:

```text
LEX_UNTERMINATED_COMMENT
```

Do not add formatter trivia/comment-preservation architecture during this checkpoint.

## Punctuation

Implement:

```text
( ) { } [ ] , : .
```

with their defined token kinds.

## Operators and longest match

Implement every operator listed in the spec.

Always consume the longest valid token:

```text
** before *
== before =
!= before unsupported !
<= before <
>= before >
+= before +
-= before -
*= before *
/= before /
-> before -
=> before =
```

Examples:

```text
** must not become STAR STAR
== must not become EQUAL EQUAL
-> must not become MINUS GREATER
```

Kaj uses keyword boolean operators:

```text
and
or
not
```

Do not implement:

```text
&&
||
!
```

Standalone `!` is invalid; `!=` is valid.

## EOF

Every `tokenize()` result must contain exactly one EOF token.

Even empty input produces:

```text
EOF
```

The EOF span should be zero-width at end of source:

```text
start == end
```

Do not emit multiple EOF tokens.

## Error recovery

Collect multiple diagnostics where practical.

Example:

```kaj
let x = @
let y = "\q"
```

should ideally report both:

```text
LEX_INVALID_CHARACTER
LEX_INVALID_ESCAPE
```

Every error path must either advance the input or terminate. Never permit an infinite loop on malformed input.

## Internal design guidance

A hand-written lexer is appropriate.

Reasonable internal helpers include:

```text
current
peek
peek_next
advance
match
make_token
skip_whitespace_and_comments
scan_identifier
scan_number
scan_string
emit_diagnostic
```

These names are suggestions, not required API.

Prefer readable code over general frameworks.

Do not add parser generators, plugin systems, visitors, compiler-pass abstractions, or token inheritance hierarchies.

## Testing requirements

Tests must verify token meaning **and** source-location correctness.

### Source spans

Test:

- first token begins at offset 0 / line 1 / column 1
- token end positions are exclusive
- spaces update columns correctly
- newlines update line/column correctly
- multiline block comments update positions
- tabs increment column by one
- EOF has correct zero-width span
- CRLF behavior if explicitly supported

### Identifiers

Test:

```text
foo
_user
foo2
ParserState
```

Also:

```text
let
letter
returnValue
matching
```

Only exact keywords become keyword tokens.

### Keywords

Test every keyword from the spec and verify case sensitivity.

### Numbers

Test:

```text
0
1
42
very large integer
0.0
0.5
3.14
10.0
-42
-3.14
1.
.5
1.2.3
```

Verify decimal token values are exact `Decimal` instances/values.

### Strings

Test:

- empty string
- ASCII string
- Unicode string
- escaped quote
- escaped backslash
- newline escape
- carriage-return escape
- tab escape
- invalid escape
- unterminated at newline
- unterminated at EOF

Verify lexeme and decoded value differ where escapes occur.

### Operators

Test every punctuation/operator and explicit longest-match behavior.

A compact case may include:

```text
+ - * / % ** = == != < <= > >= += -= *= /= -> =>
```

### Comments

Test:

- line comment before code
- line comment after code
- line comment at EOF
- single-line block comment
- multiline block comment
- block comment between tokens
- unterminated block comment
- non-nested block-comment behavior

Comments must not appear in parser-visible tokens.

### Diagnostics

At minimum test:

```text
@
!
invalid escape
unterminated string
invalid number
unterminated comment
```

Assert diagnostic code and source span.

Also include a source containing multiple lexical errors to verify recovery.

### General lexer cases

Test:

- empty source
- whitespace-only source
- comment-only source
- exactly one EOF
- realistic Kaj source

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

## Quality gates

All new code must:

- use type annotations
- pass pytest
- pass Ruff
- pass mypy under repository configuration
- avoid dead code
- avoid speculative abstractions
- avoid parser/AST behavior

Prefer immutable dataclasses for source/token/diagnostic value objects where appropriate.

## Public API hygiene

Expose useful names via package `__init__.py` only when helpful.

For example:

```python
from kaj.lexer import Lexer, Token, TokenKind
```

is reasonable.

Do not export internal scanning helpers.

## Documentation discipline

`docs/language/lexical-structure.md` is authoritative.

Do not rewrite it just to match an implementation mistake.

If implementation uncovers a genuinely underspecified case:

1. choose the smallest sensible interpretation;
2. record the decision in `.dev/plans/pure-language-v0.md`;
3. update `docs/language/lexical-structure.md` if the decision establishes public Kaj behavior;
4. add a conformance test.

Never silently diverge from the spec.

## Update the active plan

Maintain:

```text
.dev/plans/pure-language-v0.md
```

during implementation.

Record:

```text
Current checkpoint
Status
Completed
Decisions made during implementation
Known issues
Verification
```

When Checkpoint 1 finishes, mark it complete.

`.dev` remains implementation-state documentation, not the authoritative language reference.

## Suggested implementation order

1. Inspect:
   - `pyproject.toml`
   - `docs/language/lexical-structure.md`
   - `.dev/plans/pure-language-v0.md`
   - existing `src/kaj`
   - existing tests

2. Implement `SourceLocation` and `SourceSpan`.

3. Add span/location tests.

4. Implement minimal structured diagnostics.

5. Implement `TokenKind`, `Token`, and `LexerResult`.

6. Implement lexer cursor/advancement, EOF, and whitespace.

7. Implement punctuation/operators with longest matching.

8. Implement identifiers and centralized keyword lookup.

9. Implement integers, exact decimals, and malformed-number diagnostics.

10. Implement strings, escapes, Unicode contents, and string diagnostics.

11. Implement line/block comments and unterminated-comment diagnostics.

12. Verify error recovery cannot stall.

13. Complete conformance coverage.

14. Run all quality gates.

15. Update `.dev/plans/pure-language-v0.md`.

Do not proceed to Checkpoint 2.

## Verification commands

Run at minimum:

```bash
pytest
ruff check .
mypy src
```

Also verify Checkpoint 0 behavior remains intact:

```bash
kaj --version
python -m kaj
```

Preserve the repository's already-established CLI behavior rather than redesigning it.

Do not add a lexer CLI command unless separately required.

## Acceptance examples

### A

```kaj
let x = 10
```

Expected kinds:

```text
LET
IDENTIFIER
EQUAL
INTEGER
EOF
```

### B

```kaj
var price = 19.99
```

Expected:

```text
VAR
IDENTIFIER
EQUAL
DECIMAL
EOF
```

### C

```kaj
let x = -42
```

Expected:

```text
LET
IDENTIFIER
EQUAL
MINUS
INTEGER
EOF
```

### D

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Must match the authoritative lexical spec.

### E

```kaj
if x >= 10 and x != 20 {
    print("hello")
}
```

Must recognize `IF`, `GREATER_EQUAL`, `AND`, `BANG_EQUAL`, `STRING`, and surrounding tokens correctly.

### F

```kaj
// comment
let x = 10 /* another comment */
```

Comments must not appear in the parser-visible token stream.

### G

```kaj
let x = @
```

Must produce:

```text
LEX_INVALID_CHARACTER
```

with the correct source span.

## Definition of done

Checkpoint 1 is complete only when:

```text
[ ] docs/language/lexical-structure.md was treated as authoritative

[ ] SourceLocation implemented
[ ] SourceSpan implemented
[ ] offsets zero-based
[ ] lines one-based
[ ] columns one-based
[ ] spans end-exclusive

[ ] Diagnostic implemented
[ ] required diagnostic codes implemented

[ ] TokenKind implemented
[ ] Token implemented
[ ] LexerResult or equivalent implemented

[ ] identifiers implemented
[ ] keyword recognition implemented
[ ] integers implemented
[ ] arbitrary-size integers supported
[ ] decimals implemented using exact Decimal values
[ ] negative numbers tokenize as MINUS + number

[ ] strings implemented
[ ] Unicode string contents supported
[ ] required escapes supported
[ ] invalid escapes diagnosed
[ ] unterminated strings diagnosed

[ ] punctuation implemented
[ ] operators implemented
[ ] longest-match behavior implemented

[ ] whitespace skipped
[ ] newlines skipped as syntax
[ ] line comments skipped
[ ] block comments skipped
[ ] unterminated comments diagnosed

[ ] invalid characters diagnosed
[ ] invalid numbers diagnosed
[ ] reasonable recovery implemented
[ ] lexer cannot infinite-loop on malformed input

[ ] every tokenization has exactly one EOF
[ ] EOF span is correct

[ ] source-location tests pass
[ ] lexer tests pass
[ ] diagnostic tests pass

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] Checkpoint 0 behavior still works
[ ] no parser implementation added
[ ] no AST implementation added
[ ] no deferred syntax added

[ ] .dev/plans/pure-language-v0.md updated
```

## Completion report

When finished, report:

```text
Checkpoint 1 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Implemented:
- ...

Diagnostics:
- ...

Tests added:
- ...

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj bootstrap CLI: PASS/FAIL

Decisions or deviations:
- ...

Known issues:
- ...
```

If anything remains incomplete, state it explicitly.

## Final constraint

Do not advance to Checkpoint 2.

Checkpoint 1 ends at:

```text
Kaj source
    ↓
Lexer
    ↓
Token stream + lexical diagnostics
```

There must be no AST or parser behavior until the next checkpoint is separately specified.
