from io import TextIOWrapper
from command import CommandType


class Parser:
    """VM code parser
    """

    def __init__(self, f: TextIOWrapper):
        self.f = f
        self.command_type = None
        self.arg1 = None
        self.arg2 = None
        self.has_more = True

    def advance(self):
        self.command_type = None
        self.arg1 = None
        self.arg2 = None

        line = self.f.readline()
        if line == '':
            self.has_more = False
            return
        self.__parse_line(line)

    def __parse_line(self, line: str):
        # Remove whitespace and comments
        line = line.strip()
        line_end = line.find('//')
        if line_end >= 0:
            line = line[:line_end]

        # Ignore empty lines
        if line == '':
            return

        # Parse line
        parts = line.split(' ')
        if parts[0] in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
            # Arithmetic
            self.arg1 = parts[0]
            self.command_type = CommandType.ARITHMETIC
        elif parts[0] == 'pop':
            # Pop
            self.command_type = CommandType.POP
            self.arg1 = parts[1]
            self.arg2 = int(parts[2])
        elif parts[0] == 'push':
            # Push
            self.command_type = CommandType.PUSH
            self.arg1 = parts[1]
            self.arg2 = int(parts[2])
        elif parts[0] == 'label':
            # Label
            self.command_type = CommandType.LABEL
            self.arg1 = parts[1]
        elif parts[0] == 'goto':
            # Goto
            self.command_type = CommandType.GOTO
            self.arg1 = parts[1]
        elif parts[0] == 'if-goto':
            # If
            self.command_type = CommandType.IF
            self.arg1 = parts[1]
        elif parts[0] == 'function':
            # Function
            self.command_type = CommandType.FUNCTION
            self.arg1 = parts[1]
            self.arg2 = int(parts[2])
        elif parts[0] == 'call':
            # Call
            self.command_type = CommandType.CALL
            self.arg1 = parts[1]
            self.arg2 = int(parts[2])
        elif parts[0] == 'return':
            # Return
            self.command_type = CommandType.RETURN
