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

        # Detect all possible
        keyword = self.__detect_keyword()
        symbol = self.__detect_symbol()
        int_val = self.__detect_int()
        string_val = self.__detect_string()
        identifier = self.__detect_identifier()

        longest = max(keyword, symbol, int_val,
                      string_val, identifier, key=len)

        # Prefer longest text matched
        if longest == keyword:
            self.token_type = TokenType.KEYWORD
            self.keyword = keyword
            self.__text = self.__text[len(longest):]
        elif longest == symbol:
            self.token_type = TokenType.SYMBOL
            self.symbol = symbol
            self.__text = self.__text[len(longest):]
        elif longest == int_val:
            self.token_type = TokenType.INT_CONST
            self.int_val = int_val
            self.__text = self.__text[len(longest):]
        elif longest == string_val:
            self.token_type = TokenType.STRING_CONST
            self.string_val = string_val
            self.__text = self.__text[len(longest)+2:]
        elif longest == identifier:
            self.token_type = TokenType.IDENTIFIER
            self.identifier = identifier
            self.__text = self.__text[len(longest):]

    def __detect_keyword(self) -> str:
        for keyword in Keyword:
            if len(self.__text) >= len(keyword) and self.__text[:len(keyword)] == keyword:
                return keyword
        return ''

    def __detect_symbol(self) -> str:
        if len(self.__text) >= 1 and self.__text[0] in '{}()[].,;+-*/&|<>=~':
            return self.__text[0]
        return ''

    def __detect_int(self) -> str:
        p = 0
        acc = ''
        while p < len(self.__text) and self.__text[p].isdigit():
            acc += self.__text[p]
            p += 1
        return acc

    def __detect_string(self) -> str:
        p = 0
        acc = ''
        if self.__text[p] == '"':
            p += 1
            while p < len(self.__text) and self.__text[p] != '"':
                acc += self.__text[p]
                p += 1
            p += 1
        return acc

    def __detect_identifier(self) -> str:
        p = 0
        acc = ''
        while p < len(self.__text) and self.__text[p].isidentifier():
            acc += self.__text[p]
            p += 1
        return acc

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
