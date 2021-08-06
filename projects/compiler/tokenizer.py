from enum import Enum, auto
from typing import TextIO


class TokenType(Enum):
    """Token type
    """
    KEYWORD = auto()
    SYMBOL = auto()
    IDENTIFIER = auto()
    INT_CONST = auto()
    STRING_CONST = auto()


class Keyword(str, Enum):
    """Keyword
    """
    CLASS = 'class'
    METHOD = 'method'
    FUNCTION = 'function'
    CONSTRUCTOR = 'constructor'
    INT = 'int'
    BOOLEAN = 'boolean'
    CHAR = 'char'
    VOID = 'void'
    VAR = 'var'
    STATIC = 'static'
    FIELD = 'field'
    LET = 'let'
    DO = 'do'
    IF = 'if'
    ELSE = 'else'
    WHILE = 'while'
    RETURN = 'return'
    TRUE = 'true'
    FALSE = 'false'
    NULL = 'null'
    THIS = 'this'


class Tokenizer:
    """Tokenizes Jack code.
    """

    def __init__(self, f: TextIO):
        self.has_more = True
        self.token_type = None
        self.keyword = None
        self.symbol = None
        self.identifier = None
        self.int_val = None
        self.string_val = None
        self.__text = f.read()

    def advance(self):
        self.token_type = None
        self.keyword = None
        self.symbol = None
        self.identifier = None
        self.int_val = None
        self.string_val = None

        is_comment = True
        while is_comment:
            # Exits at end of tokens
            if len(self.__text) == 0:
                self.has_more = False
                return

            # Remove comments
            self.__text = self.__text.strip()
            is_comment = self.__remove_comment()
            self.__text = self.__text.strip()

        # Detect keyword
        for keyword in Keyword:
            if len(self.__text) >= len(keyword) and self.__text[:len(keyword)] == keyword:
                self.token_type = TokenType.KEYWORD
                self.keyword = keyword
                self.__text = self.__text[len(keyword):]
                return

        # Detect symbol
        if len(self.__text) >= 1 and self.__text[0] in '{}()[].,;+-*/&|<>=~':
            self.token_type = TokenType.SYMBOL
            self.symbol = self.__text[0]
            self.__text = self.__text[1:]
            return

        p = 0
        acc = ''

        # Detect int
        while p < len(self.__text) and self.__text[p].isdigit():
            acc += self.__text[p]
            p += 1
        if p != 0:
            self.token_type = TokenType.INT_CONST
            self.int_val = int(acc)
            self.__text = self.__text[p:]
            return

        # Detect string
        if self.__text[p] == '"':
            p += 1
            while p < len(self.__text) and self.__text[p] != '"':
                acc += self.__text[p]
                p += 1
            p += 1
            self.token_type = TokenType.STRING_CONST
            self.string_val = acc
            self.__text = self.__text[p:]
            return

        # Detect identifier
        while p < len(self.__text) and self.__text[p].isidentifier():
            acc += self.__text[p]
            p += 1
        if p != 0:
            self.token_type = TokenType.IDENTIFIER
            self.identifier = acc
            self.__text = self.__text[p:]
            return

    def __remove_comment(self) -> bool:
        # Remove single-line comment
        p = 0
        if len(self.__text) >= 2 and self.__text[:2] == '//':
            p += 2
            while p < len(self.__text) and self.__text[p] != '\n':
                p += 1
            p += 1
            self.__text = self.__text[p:]
            return True

        # Remove multi-line comment and doc comment
        p = 0
        if len(self.__text) >= 2 and self.__text[:2] == '/*':
            p += 2
            while p < len(self.__text):
                p += 1
                if len(self.__text[p:]) >= 2 and self.__text[p:p+2] == '*/':
                    break
            p += 2
            self.__text = self.__text[p:]
            return True

        return False
