from io import TextIOWrapper
from typing import List
from command import CommandType


class CodeWriter:
    """Translates VM code to Hack assembly
    """

    def __init__(self, fname: str, f: TextIOWrapper):
        self.fname = fname
        self.f = f
        self.label_counters = {}

    def write_arithmetic(self, command: str):
        asm = []
        if command in ['neg', 'not']:
            # Unary command: set M=x
            asm += [
                '@SP',
                'A=M',
                'A=A-1',
                *self.__compile_unary_command(command),
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
        elif command in ['add', 'sub', 'eq', 'gt', 'lt', 'and', 'or']:
            # Binary command: set D=x and M=y
            asm += [
                '@SP',
                'A=M',
                'A=A-1',
                'D=M',
                'A=A-1',
                *self.__compile_binary_command(command),
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
        self.f.write('\n'.join(asm)+'\n')

    def write_pushpop(self, command: CommandType, segment: str, index: int):
        asm = []

        # Pushing constant
        if segment == 'constant' and command == CommandType.PUSH:
            asm += [
                f'@{index}',
                'D=A',
                '@SP',
                'A=M',
                'M=D',
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
            self.f.write('\n'.join(asm)+'\n')
            return

        # Part 1: generate ASM to get addr into D
        if segment in ['argument', 'local', 'this', 'that']:
            reg_map = {
                'argument': 'ARG',
                'local': 'LCL',
                'this': 'THIS',
                'that': 'THAT',
            }
            asm += [
                f'@{reg_map[segment]}',
                'D=M',
                f'@{index}',
                'D=D+A',
            ]
        elif segment in ['pointer', 'temp']:
            reg_map = {
                'pointer': 'THIS',
                'temp': 'R15',
            }
            asm += [
                f'@{reg_map[segment]}',
                'D=A',
                f'@{index}',
                'D=D+A',
            ]
        elif segment == 'static':
            sym = f'{self.fname}.{index}'
            asm += [
                f'@{sym}',
                'D=A',
            ]

        # Part 2: generate push/pop code
        if command == CommandType.PUSH:
            asm += [
                'A=D',
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
        elif command == CommandType.POP:
            asm += [
                '@R13',
                'M=D',
                '@SP',
                'A=M',
                'A=A-1',
                'D=M',
                '@R13',
                'A=M',
                'M=D',
                '@SP',
                'A=M',
                'A=A-1',
                'D=A',
                '@SP',
                'M=D',
            ]

        self.f.write('\n'.join(asm)+'\n')

    def __compile_unary_command(self, command: str) -> List[str]:
        if command == 'neg':
            return [
                'M=!M',
                'M=M+1',
            ]
        elif command == 'not':
            return [
                'M=!M',
            ]

    def __compile_binary_command(self, command: str) -> List[str]:
        if command == 'add':
            return [
                'M=D+M',
            ]
        elif command == 'sub':
            return [
                'M=M-D',
            ]
        elif command in ['eq', 'gt', 'lt']:
            branch_map = {
                'eq': 'JEQ',
                'gt': 'JGT',
                'lt': 'JLT',
            }
            iftrue_label = self.__generate_label('IFTRUE')
            endif_label = self.__generate_label('ENDIF')
            return [
                'M=M-D',
                'D=A',
                '@R13',
                'M=D',
                'A=D',
                'D=M',
                f'@{iftrue_label}',
                f'D;{branch_map[command]}',
                'D=0',
                f'@{endif_label}',
                '0;JMP',
                f'({iftrue_label})',
                'D=0',
                'D=!D',
                f'({endif_label})',
                '@R13',
                'A=M',
                'M=D',
            ]
        elif command == 'and':
            return [
                'M=D&M',
            ]
        elif command == 'or':
            return [
                'M=D|M'
            ]

    def __generate_label(self, prefix='LBL') -> str:
        if prefix not in self.label_counters:
            self.label_counters[prefix] = 0
        else:
            self.label_counters[prefix] += 1
        label = f'{prefix}_{self.label_counters[prefix]}'
        return label
