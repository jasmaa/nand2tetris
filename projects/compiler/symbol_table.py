from enum import Enum
from typing import Tuple, Union


class IdentifierKind(str, Enum):
    """Identifier kind.
    """
    STATIC = 'static'
    FIELD = 'field'
    ARGUMENT = 'argument'
    VAR = 'var'


class SymbolTable:
    """Class and subroutine symbol table.
    """

    def __init__(self):
        self.__class_table = {}
        self.__subroutine_table = {}
        self.__counters = {
            IdentifierKind.STATIC: 0,
            IdentifierKind.FIELD: 0,
            IdentifierKind.ARGUMENT: 0,
            IdentifierKind.VAR: 0,
        }

    def start_subroutine(self):
        """Erases current subroutine scope and starts new subroutine scope.
        """
        self.__subroutine_table = {}
        self.__counters[IdentifierKind.ARGUMENT] = 0
        self.__counters[IdentifierKind.VAR] = 0

    def define(self, name: str, type: str, kind: IdentifierKind):
        """Declare new identifier.
        """
        if kind in [IdentifierKind.STATIC, IdentifierKind.FIELD]:
            # Class scope
            self.__class_table[name] = (
                type, kind, self.__counters[kind]
            )
        elif kind in [IdentifierKind.ARGUMENT, IdentifierKind.VAR]:
            # Subroutine scope
            self.__subroutine_table[name] = (
                type, kind, self.__counters[kind]
            )
        self.__counters[kind] += 1

    def var_count(self, kind: IdentifierKind) -> int:
        """Returns number of variables declared with the specified kind.
        """
        return sum(kind == k for _, k, _ in self.__class_table.values()) + \
            sum(kind == k for _, k, _ in self.__subroutine_table.values())

    def find(self, name: str) -> Union[Tuple[str, IdentifierKind, int], None]:
        """Finds (type, kind, idx) tuple for identifier. Returns None if no identifier found.
        """
        # Search subroutine scope
        for n, v in self.__subroutine_table.items():
            if n == name:
                return v
        # Search class scope
        for n, v in self.__class_table.items():
            if n == name:
                return v
        return None
