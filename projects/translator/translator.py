import os
import argparse
from command import CommandType
from parse import Parser
from writer import CodeWriter


def translate(path: str, fname: str):
    """Translate VM file name `fname` in directory `path` to an ASM file.
    """
    in_path = os.path.join(path, f'{fname}.vm')
    out_path = os.path.join(path, f'{fname}.asm')
    with open(in_path, 'r') as in_f:
        with open(out_path, 'w') as out_f:
            p = Parser(in_f)
            w = CodeWriter(fname, out_f)
            while p.has_more:
                p.advance()
                if p.command_type == CommandType.ARITHMETIC:
                    w.write_arithmetic(p.arg1)
                elif p.command_type == CommandType.PUSH or p.command_type == CommandType.POP:
                    w.write_pushpop(p.command_type, p.arg1, p.arg2)
                elif p.command_type == CommandType.LABEL:
                    w.write_label(p.arg1)
                elif p.command_type == CommandType.GOTO:
                    w.write_goto(p.arg1)
                elif p.command_type == CommandType.IF:
                    w.write_if(p.arg1)
                elif p.command_type == CommandType.FUNCTION:
                    p.curr_func_name = p.arg1
                    w.write_function(p.arg1, p.arg2)
                elif p.command_type == CommandType.CALL:
                    w.write_call(p.arg1, p.arg2)
                elif p.command_type == CommandType.RETURN:
                    p.curr_func_name = ''
                    w.write_return()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Translate VM code to HACK ASM.')
    parser.add_argument('input', help='Path of the directory/file.')

    args = parser.parse_args()
    path = os.path.dirname(args.input)
    fname, ext = os.path.splitext(os.path.basename(args.input))

    if ext == '':
        # Directory
        for file in os.listdir(path):
            if file.endswith('.vm'):
                fname, _ = os.path.splitext(os.path.basename(file))
                translate(path, fname)
        exit(0)
    elif ext == '.vm':
        # File
        translate(path, fname)
        exit(0)

    print('error: must input a VM file or directory')
    exit(1)
