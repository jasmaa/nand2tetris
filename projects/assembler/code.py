from parse import CommandType, Line
from typing import Dict, List


comp2bin = {
    '0': '0101010',
    '1': '0111111',
    '-1': '0111010',
    'D': '0001100',
    'A': '0110000',
    '!D': '0001101',
    '!A': '0110001',
    '-D': '0001111',
    '-A': '0110011',
    'D+1': '0011111',
    'A+1': '0110111',
    'D-1': '0001110',
    'A-1': '0110010',
    'D+A': '0000010',
    'D-A': '0010011',
    'A-D': '0000111',
    'D&A': '0000000',
    'D|A': '0010101',

    'M': '1110000',
    '!M': '1110001',
    '-M': '1110011',
    'M+1': '1110111',
    'M-1': '1110010',
    'D+M': '1000010',
    'D-M': '1010011',
    'M-D': '1000111',
    'D&M': '1000000',
    'D|M': '1010101',
}

dest2bin = {
    None: '000',
    'null': '000',
    'M': '001',
    'D': '010',
    'MD': '011',
    'A': '100',
    'AM': '101',
    'AD': '110',
    'AMD': '111',
}

jump2bin = {
    None: '000',
    'null': '000',
    'JGT': '001',
    'JEQ': '010',
    'JGE': '011',
    'JLT': '100',
    'JNE': '101',
    'JLE': '110',
    'JMP': '111',
}


def assemble(lines: List[Line], sym_table: Dict[str, int]) -> List[str]:
    """Assemble lines to machine code list
    """
    return [assemble_line(l, sym_table) for l in lines]


def assemble_line(line: Line, sym_table: Dict[str, int]) -> str:
    """Assemble single line to machine code
    """
    if line.command_type == CommandType.ADDR:
        if type(line.symbol) == int:
            val = line.symbol
        else:
            val = sym_table[line.symbol]
        bin_str = '{0:b}'.format(val)
        padding = '0'*(15-len(bin_str))
        return f'0{padding}{bin_str}'

    elif line.command_type == CommandType.COMP:
        return f'111{comp2bin[line.comp]}{dest2bin[line.dest]}{jump2bin[line.jump]}'
