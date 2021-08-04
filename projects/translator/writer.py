from io import TextIOWrapper
from typing import List
from command import CommandType


class CodeWriter:
    """Translates VM code to Hack assembly.
    """

    def __init__(self, fname: str, f: TextIOWrapper):
        self.fname = fname
        self.f = f
        self.label_counters = {}
        self.curr_func_name = ''

    def write_arithmetic(self, command: str):
        """Writes translated arithmetic instruction.
        """
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
        """Writes translated push or pop instruction.
        """
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

    def write_label(self, label: str):
        """Writes translated label.
        """
        asm = [
            f'({self.curr_func_name}:{label})',
        ]
        self.f.write('\n'.join(asm)+'\n')

    def write_goto(self, label: str):
        """Writes translated goto.
        """
        asm = [
            f'@{self.curr_func_name}:{label}',
            '0;JMP',
        ]
        self.f.write('\n'.join(asm)+'\n')

    def write_if(self, label: str):
        """Writes translated if-goto.
        """
        asm = [
            '@SP',
            'D=M',
            'M=D-1',
            '@SP',
            'A=M',
            'D=M',
            f'@{self.curr_func_name}:{label}',
            'D;JNE',
        ]
        self.f.write('\n'.join(asm)+'\n')

    def write_call(self, function_name: str, num_args: int):
        """Writes translated function call.
        """
        ret_label = self.__generate_label('RET')
        asm = []
        # Push return address and registers
        for var in [ret_label, 'LCL', 'ARG', 'THIS', 'THAT']:
            asm += [
                f'@{var}',
                'D=A',
                '@SP',
                'A=M',
                'M=D',
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
        asm += [
            # Set ARG
            '@SP',
            'D=M',
            '@5',
            'D=D-A',
            f'@{num_args}',
            'D=D-A',
            '@ARG',
            'M=D',
            # Set new LCL
            '@SP',
            'D=M',
            '@LCL',
            'M=D',
            # Jump to function
            f'@{function_name}',
            '0;JMP',
            # Set return label
            f'({ret_label})',
        ]
        self.f.write('\n'.join(asm)+'\n')

    def write_return(self):
        """Write translated return.
        """
        asm = [
            # Store old LCL
            '@LCL',
            'D=M',
            '@R13',
            'M=D',
            # Store return address
            '@5',
            'A=D-A',
            'D=M',
            '@R14',
            'M=D',
            # Reposition return value
            '@SP',
            'A=M',
            'A=A-1',
            'D=M',
            '@ARG',
            'A=M',
            'M=D',
            # Reposition SP after return value
            '@ARG',
            'D=M',
            '@SP',
            'M=D',
            'M=M+1',
        ]
        # Restore THAT, THIS, ARG, and LCL
        for reg in ['THAT', 'THIS', 'ARG', 'LCL']:
            asm += [
                '@R13',
                'M=M-1',
                'A=M',
                'D=M',
                f'@{reg}',
                'M=D',
            ]
        # Jump to return address
        asm += [
            '@R14',
            'A=M',
            '0;JMP',
        ]
        self.f.write('\n'.join(asm)+'\n')

    def write_function(self, function_name: str, num_locals: int):
        """Write translated function declaration.
        """
        asm = [
            f'({function_name})',
        ]
        # Initialize locals
        for _ in range(num_locals):
            asm += [
                '@SP',
                'A=M',
                'M=0',
                'D=A+1',
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
