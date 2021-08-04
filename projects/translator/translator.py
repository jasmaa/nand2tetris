import os
import argparse
from typing import List
from command import CommandType
from parse import Parser
from writer import CodeWriter


def translate(path: str, in_fnames: List[str], out_fname: str):
    """Translate list of VM files in directory `path` to an ASM file.
    """
    out_path = os.path.join(path, f'{out_fname}.asm')
    with open(out_path, 'w') as out_f:
        w = CodeWriter(out_f)
        for fname in in_fnames:
            w.fname = fname
            in_path = os.path.join(path, f'{fname}.vm')
            with open(in_path, 'r') as in_f:
                p = Parser(in_f)
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
                        if p.arg1 == 'Sys.init':
                            w.write_init()
                        w.write_function(p.arg1, p.arg2)
                    elif p.command_type == CommandType.CALL:
                        w.write_call(p.arg1, p.arg2)
                    elif p.command_type == CommandType.RETURN:
                        p.curr_func_name = ''
                        w.write_return()
        # Output
        w.output()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Translate VM code to HACK ASM.')
    parser.add_argument('input', help='Path of the directory/file.')

    args = parser.parse_args()
    path = os.path.dirname(args.input)
    fname, ext = os.path.splitext(os.path.basename(args.input))

    if ext != '' and ext != '.vm':
        print('error: must input a VM file or directory')
        exit(1)

    in_fnames = []
    if ext == '':
        # Directory
        for filepath in os.listdir(path):
            if filepath.endswith('.vm'):
                fname, _ = os.path.splitext(os.path.basename(filepath))
                in_fnames.append(fname)
        out_fname = os.path.split(path)[-1]
    elif ext == '.vm':
        # File
        in_fnames.append(fname)
        out_fname = fname

    translate(path, in_fnames, out_fname)
