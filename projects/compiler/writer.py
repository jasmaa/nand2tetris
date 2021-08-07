from enum import Enum
from typing import TextIO


class Segment(str, Enum):
    """VM memory segment.
    """
    CONST = 'constant'
    ARG = 'argument'
    LOCAL = 'local'
    STATIC = 'static'
    THIS = 'this'
    THAT = 'that'
    POINTER = 'pointer'
    TEMP = 'temp'


class Command(str, Enum):
    """VM arithmetic command.
    """
    ADD = 'add'
    SUB = 'sub'
    NEG = 'neg'
    EQ = 'eq'
    GT = 'gt'
    LT = 'lt'
    AND = 'and'
    OR = 'or'
    NOT = 'not'


class VMWriter:
    """VM code writer.
    """

    def __init__(self, out_f: TextIO):
        self.__out_f = out_f

    def write_push(self, segment: Segment, idx: int):
        """Writes push.
        """
        self.__out_f.write(f'push {segment} {idx}\n')

    def write_pop(self, segment: Segment, idx: int):
        """Writes pop.
        """
        self.__out_f.write(f'pop {segment} {idx}\n')

    def write_arithmetic(self, command: Command):
        """Writes arithmetic command.
        """
        self.__out_f.write(f'{command}\n')

    def write_label(self, label: str):
        """Writes label.
        """
        self.__out_f.write(f'label {label}\n')

    def write_goto(self, label: str):
        """Writes goto.
        """
        self.__out_f.write(f'goto {label}\n')

    def write_if(self, label: str):
        """Writes if goto.
        """
        self.__out_f.write(f'if-goto {label}\n')

    def write_call(self, name: str, n_args: int):
        """Writes function call.
        """
        self.__out_f.write(f'call {name} {n_args}\n')

    def write_function(self, name: str, n_locals: int):
        """Writes function declaration.
        """
        self.__out_f.write(f'function {name} {n_locals}\n')

    def write_return(self):
        """Writes return.
        """
        self.__out_f.write(f'return\n')
