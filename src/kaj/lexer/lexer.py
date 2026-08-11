from dataclasses import dataclass
from decimal import Decimal

from kaj.diagnostics import Diagnostic
from kaj.lexer.token import Token, TokenKind
from kaj.source import SourceLocation, SourceSpan

LEX_INVALID_CHARACTER = "LEX_INVALID_CHARACTER"
LEX_UNTERMINATED_STRING = "LEX_UNTERMINATED_STRING"
LEX_INVALID_ESCAPE = "LEX_INVALID_ESCAPE"
LEX_INVALID_NUMBER = "LEX_INVALID_NUMBER"
LEX_UNTERMINATED_COMMENT = "LEX_UNTERMINATED_COMMENT"


KEYWORDS: dict[str, TokenKind] = {
    "let": TokenKind.LET,
    "var": TokenKind.VAR,
    "fn": TokenKind.FN,
    "return": TokenKind.RETURN,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "for": TokenKind.FOR,
    "in": TokenKind.IN,
    "break": TokenKind.BREAK,
    "continue": TokenKind.CONTINUE,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "none": TokenKind.NONE,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "type": TokenKind.TYPE,
    "enum": TokenKind.ENUM,
    "newtype": TokenKind.NEWTYPE,
    "match": TokenKind.MATCH,
    "import": TokenKind.IMPORT,
}

SINGLE_CHARACTER_TOKENS: dict[str, TokenKind] = {
    "(": TokenKind.LEFT_PAREN,
    ")": TokenKind.RIGHT_PAREN,
    "{": TokenKind.LEFT_BRACE,
    "}": TokenKind.RIGHT_BRACE,
    "[": TokenKind.LEFT_BRACKET,
    "]": TokenKind.RIGHT_BRACKET,
    ",": TokenKind.COMMA,
    ":": TokenKind.COLON,
    ".": TokenKind.DOT,
    "+": TokenKind.PLUS,
    "-": TokenKind.MINUS,
    "*": TokenKind.STAR,
    "/": TokenKind.SLASH,
    "%": TokenKind.PERCENT,
    "=": TokenKind.EQUAL,
    "<": TokenKind.LESS,
    ">": TokenKind.GREATER,
}

MULTI_CHARACTER_TOKENS: dict[str, TokenKind] = {
    "**": TokenKind.STAR_STAR,
    "==": TokenKind.EQUAL_EQUAL,
    "!=": TokenKind.BANG_EQUAL,
    "<=": TokenKind.LESS_EQUAL,
    ">=": TokenKind.GREATER_EQUAL,
    "+=": TokenKind.PLUS_EQUAL,
    "-=": TokenKind.MINUS_EQUAL,
    "*=": TokenKind.STAR_EQUAL,
    "/=": TokenKind.SLASH_EQUAL,
    "->": TokenKind.ARROW,
    "=>": TokenKind.FAT_ARROW,
}


@dataclass(frozen=True)
class LexerResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic]


class Lexer:
    def __init__(self, source: str, filename: str = "<source>") -> None:
        self.source = source
        self.filename = filename
        self._offset = 0
        self._line = 1
        self._column = 1
        self._tokens: list[Token] = []
        self._diagnostics: list[Diagnostic] = []

    def tokenize(self) -> LexerResult:
        self._offset = 0
        self._line = 1
        self._column = 1
        self._tokens.clear()
        self._diagnostics.clear()

        while not self._at_end():
            if self._skip_whitespace_or_comment():
                continue

            start = self._location()
            character = self._current()

            if self._is_identifier_start(character):
                self._scan_identifier(start)
            elif character.isascii() and character.isdigit():
                self._scan_number(start)
            elif character == "." and self._peek().isascii() and self._peek().isdigit():
                self._scan_leading_dot_number(start)
            elif character == '"':
                self._scan_string(start)
            else:
                self._scan_symbol(start)

        eof_location = self._location()
        self._tokens.append(Token(TokenKind.EOF, "", SourceSpan(eof_location, eof_location)))
        return LexerResult(tokens=list(self._tokens), diagnostics=list(self._diagnostics))

    def _skip_whitespace_or_comment(self) -> bool:
        character = self._current()
        if character in {" ", "\t", "\n", "\r"}:
            self._advance()
            return True

        if character == "/" and self._peek() == "/":
            self._advance()
            self._advance()
            while not self._at_end() and self._current() not in {"\n", "\r"}:
                self._advance()
            return True

        if character == "/" and self._peek() == "*":
            start = self._location()
            self._advance()
            self._advance()
            while not self._at_end():
                if self._current() == "*" and self._peek() == "/":
                    self._advance()
                    self._advance()
                    return True
                self._advance()
            self._diagnose(
                LEX_UNTERMINATED_COMMENT,
                "Unterminated block comment.",
                start,
            )
            return True

        return False

    def _scan_identifier(self, start: SourceLocation) -> None:
        self._advance()
        while self._is_identifier_continue(self._current()):
            self._advance()
        lexeme = self.source[start.offset : self._offset]
        self._emit(KEYWORDS.get(lexeme, TokenKind.IDENTIFIER), start)

    def _scan_number(self, start: SourceLocation) -> None:
        while self._current().isascii() and self._current().isdigit():
            self._advance()

        if self._current() != ".":
            lexeme = self.source[start.offset : self._offset]
            self._emit(TokenKind.INTEGER, start, int(lexeme))
            return

        self._advance()
        if not (self._current().isascii() and self._current().isdigit()):
            self._consume_numeric_tail()
            self._diagnose(LEX_INVALID_NUMBER, "Invalid decimal literal.", start)
            return

        while self._current().isascii() and self._current().isdigit():
            self._advance()

        if self._current() == ".":
            self._consume_numeric_tail()
            self._diagnose(LEX_INVALID_NUMBER, "Invalid decimal literal.", start)
            return

        lexeme = self.source[start.offset : self._offset]
        self._emit(TokenKind.DECIMAL, start, Decimal(lexeme))

    def _scan_leading_dot_number(self, start: SourceLocation) -> None:
        self._advance()
        self._consume_numeric_tail()
        self._diagnose(LEX_INVALID_NUMBER, "Decimal literals require a leading digit.", start)

    def _consume_numeric_tail(self) -> None:
        while True:
            character = self._current()
            if character == "." or (character.isascii() and character.isdigit()):
                self._advance()
                continue
            return

    def _scan_string(self, start: SourceLocation) -> None:
        self._advance()
        decoded: list[str] = []
        escapes = {'"': '"', "\\": "\\", "n": "\n", "r": "\r", "t": "\t"}

        while not self._at_end():
            character = self._current()
            if character == '"':
                self._advance()
                self._emit(TokenKind.STRING, start, "".join(decoded))
                return
            if character in {"\n", "\r"}:
                self._diagnose(
                    LEX_UNTERMINATED_STRING,
                    "String literal ends at a source newline.",
                    start,
                )
                return
            if character == "\\":
                escape_start = self._location()
                self._advance()
                if self._at_end():
                    self._diagnose(
                        LEX_UNTERMINATED_STRING,
                        "String literal ends after an escape marker.",
                        start,
                    )
                    return
                escaped = self._current()
                if escaped in {"\n", "\r"}:
                    self._diagnose(
                        LEX_UNTERMINATED_STRING,
                        "String literal ends at a source newline.",
                        start,
                    )
                    return
                self._advance()
                replacement = escapes.get(escaped)
                if replacement is None:
                    self._diagnose(
                        LEX_INVALID_ESCAPE,
                        f"Unsupported string escape: \\{escaped}",
                        escape_start,
                    )
                    decoded.append(escaped)
                else:
                    decoded.append(replacement)
                continue
            decoded.append(character)
            self._advance()

        self._diagnose(
            LEX_UNTERMINATED_STRING,
            "String literal reaches the end of source.",
            start,
        )

    def _scan_symbol(self, start: SourceLocation) -> None:
        pair = self._current() + self._peek()
        pair_kind = MULTI_CHARACTER_TOKENS.get(pair)
        if pair_kind is not None:
            self._advance()
            self._advance()
            self._emit(pair_kind, start)
            return

        character = self._advance()
        kind = SINGLE_CHARACTER_TOKENS.get(character)
        if kind is not None:
            self._emit(kind, start)
            return

        self._diagnose(
            LEX_INVALID_CHARACTER,
            f"Invalid character: {character!r}.",
            start,
        )

    def _emit(self, kind: TokenKind, start: SourceLocation, value: object | None = None) -> None:
        span = SourceSpan(start, self._location())
        self._tokens.append(Token(kind, self.source[start.offset : self._offset], span, value))

    def _diagnose(self, code: str, message: str, start: SourceLocation) -> None:
        self._diagnostics.append(
            Diagnostic(code=code, message=message, span=SourceSpan(start, self._location()))
        )

    def _location(self) -> SourceLocation:
        return SourceLocation(self._offset, self._line, self._column)

    def _at_end(self) -> bool:
        return self._offset >= len(self.source)

    def _current(self) -> str:
        return "\0" if self._at_end() else self.source[self._offset]

    def _peek(self) -> str:
        next_offset = self._offset + 1
        return "\0" if next_offset >= len(self.source) else self.source[next_offset]

    def _advance(self) -> str:
        character = self.source[self._offset]
        self._offset += 1
        if character == "\r":
            if not self._at_end() and self.source[self._offset] == "\n":
                self._offset += 1
            self._line += 1
            self._column = 1
        elif character == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return character

    @staticmethod
    def _is_identifier_start(character: str) -> bool:
        return character.isascii() and (character.isalpha() or character == "_")

    @classmethod
    def _is_identifier_continue(cls, character: str) -> bool:
        return cls._is_identifier_start(character) or (character.isascii() and character.isdigit())
