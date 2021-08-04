from io import TextIOWrapper
from typing import List
from command import CommandType


class CodeWriter:
    """Translates VM code to Hack assembly.
    """

    def __init__(self, f: TextIOWrapper):
        self.f = f
        self.fname = ''
        self.label_counters = {}
        self.curr_func_name = ''
        self.asm = []

    def output(self):
        """Output ASM to file.
        """
        self.f.write('\n'.join(self.asm)+'\n')

    def write_arithmetic(self, command: str):
        """Writes translated arithmetic instruction.
        """
        if command in ['neg', 'not']:
            # Unary command: set M=x
            self.asm += [
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
            self.asm += [
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

    def write_pushpop(self, command: CommandType, segment: str, index: int):
        """Writes translated push or pop instruction.
        """
        # Pushing constant
        if segment == 'constant' and command == CommandType.PUSH:
            self.asm += [
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
            return

        # Part 1: generate ASM to get addr into D
        if segment in ['argument', 'local', 'this', 'that']:
            reg_map = {
                'argument': 'ARG',
                'local': 'LCL',
                'this': 'THIS',
                'that': 'THAT',
            }
            self.asm += [
                f'@{reg_map[segment]}',
                'D=M',
                f'@{index}',
                'D=D+A',
            ]
        elif segment in ['pointer', 'temp']:
            reg_map = {
                'pointer': 'THIS',
                'temp': 'R5',
            }
            self.asm += [
                f'@{reg_map[segment]}',
                'D=A',
                f'@{index}',
                'D=D+A',
            ]
        elif segment == 'static':
            sym = f'{self.fname}.{index}'
            self.asm += [
                f'@{sym}',
                'D=A',
            ]

        # Part 2: generate push/pop code
        if command == CommandType.PUSH:
            self.asm += [
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
            self.asm += [
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

    def write_init(self):
        """Writes system init into beginning of ROM.
        """
        # Set SP=256 and call `Sys.init` using `Sys.preinit` as a proxy
        self.asm = [
            '@256',
            'D=A',
            '@SP',
            'M=D',
            '@Sys.preinit',
            '0;JMP',
        ] + self.asm
        self.write_function('Sys.preinit', 0)
        self.write_call('Sys.init', 0)

    def write_label(self, label: str):
        """Writes translated label.
        """
        self.asm += [
            f'({self.curr_func_name}:{label})',
        ]

    def write_goto(self, label: str):
        """Writes translated goto.
        """
        self.asm += [
            f'@{self.curr_func_name}:{label}',
            '0;JMP',
        ]

    def write_if(self, label: str):
        """Writes translated if-goto.
        """
        self.asm += [
            '@SP',
            'D=M',
            'M=D-1',
            '@SP',
            'A=M',
            'D=M',
            f'@{self.curr_func_name}:{label}',
            'D;JNE',
        ]

    def write_call(self, function_name: str, num_args: int):
        """Writes translated function call.
        """
        ret_label = self.__generate_label('RET')
        # Push return address
        self.asm += [
            f'@{ret_label}',
            'D=A',
            '@SP',
            'A=M',
            'M=D',
            'A=A+1',
            'D=A',
            '@SP',
            'M=D',
        ]
        # Push registers
        for var in ['LCL', 'ARG', 'THIS', 'THAT']:
            self.asm += [
                f'@{var}',
                'D=M',
                '@SP',
                'A=M',
                'M=D',
                'A=A+1',
                'D=A',
                '@SP',
                'M=D',
            ]
        self.asm += [
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

    def write_return(self):
        """Write translated return.
        """
        self.asm += [
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
            self.asm += [
                '@R13',
                'M=M-1',
                'A=M',
                'D=M',
                f'@{reg}',
                'M=D',
            ]
        # Jump to return address
        self.asm += [
            '@R14',
            'A=M',
            '0;JMP',
        ]

    def write_function(self, function_name: str, num_locals: int):
        """Write translated function declaration.
        """
        self.asm += [
            f'({function_name})',
        ]
        # Initialize locals
        for _ in range(num_locals):
            self.asm += [
                '@SP',
                'A=M',
                'M=0',
                'D=A+1',
                '@SP',
                'M=D',
            ]

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
