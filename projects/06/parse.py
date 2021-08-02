from enum import Enum


class CommandType(Enum):
    """Machine code command type
    """
    ADDR = 1
    COMP = 2


class Line:
    """Line of machine code
    """

    def __init__(self, command_type=None, symbol=None, dest=None, comp=None, jump=None):
        self.command_type = command_type
        self.symbol = symbol
        self.dest = dest
        self.comp = comp
        self.jump = jump

    def __repr__(self):
        if self.command_type == CommandType.ADDR:
            return f'A:{self.symbol}'
        elif self.command_type == CommandType.COMP:
            return f'C:{{dest={self.dest}, comp={self.comp}, jump={self.jump}}}'


class Parser:
    """Assembly parser
    """

    def __init__(self, fname: str):
        self.fname = fname
        self.lines = []
        self.prg_idx = 0
        self.var_idx = 0x10
        self.sym_table = {
            'SP': 0,
            'LCL': 1,
            'ARG': 2,
            'THIS': 3,
            'THAT': 4,
            'R0': 0,
            'R1': 1,
            'R2': 2,
            'R3': 3,
            'R4': 4,
            'R5': 5,
            'R6': 6,
            'R7': 7,
            'R8': 8,
            'R9': 9,
            'R10': 10,
            'R11': 11,
            'R12': 12,
            'R13': 13,
            'R14': 14,
            'R15': 15,
            'SCREEN': 16384,
            'KBD': 24576,
        }

        with open(self.fname, 'r') as f:
            self.__raw_lines = [l.strip() for l in f.read().split('\n')]

    def parse(self):
        """Parses machine code lines and symbol table from loaded file
        """

        # First pass: add labels to table
        for l in self.__raw_lines:
            if len(l) == 0 or len(l) >= 2 and l[0:2] == '//':
                # No-op
                pass
            elif len(l) > 0 and l[0] == '@':
                # Address
                self.prg_idx += 1
            elif l[0] == '(' and l[-1] == ')':
                # Label
                label = l[1:len(l)-1]
                self.sym_table[label] = self.prg_idx
            else:
                # Comp
                self.prg_idx += 1

        # Second pass: generate lines
        for l in self.__raw_lines:
            if len(l) == 0 or len(l) >= 2 and l[0:2] == '//':
                # No-op
                pass
            elif len(l) > 0 and l[0] == '@':
                # Address
                addr = l[1:]
                self.lines.append(self.__parse_addr(addr))
            elif l[0] == '(' and l[-1] == ')':
                # Label
                pass
            else:
                # Comp
                self.lines.append(self.__parse_comp(l))

    def __parse_addr(self, addr: str) -> Line:
        if addr.isdigit():
            symbol = int(addr)
        else:
            symbol = addr
            # Add new symbol to table
            if symbol not in self.sym_table:
                self.sym_table[symbol] = self.var_idx
                self.var_idx += 1
        return Line(command_type=CommandType.ADDR, symbol=symbol)

    def __parse_comp(self, line: str) -> Line:
        eq_idx = line.find('=')
        semi_idx = line.find(';')
        comment_start = line.find('//')

        line_end = len(line)
        if comment_start > 0:
            line_end = comment_start

        # Parse dest
        if eq_idx > 0:
            dest = line[0:eq_idx].strip()
        else:
            dest = None

        # Parse jump
        if semi_idx > 0:
            jump = line[semi_idx+1:line_end].strip()
        else:
            jump = None

        # Parse comp
        comp_start = 0
        comp_end = line_end
        if eq_idx > 0:
            comp_start = eq_idx + 1
        if semi_idx > 0:
            comp_end = semi_idx
        comp = line[comp_start:comp_end].strip()

        return Line(command_type=CommandType.COMP, comp=comp, dest=dest, jump=jump)
