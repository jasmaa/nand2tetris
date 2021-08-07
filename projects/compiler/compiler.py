import os
import argparse
from typing import List
from engine import CompilationEngine


def compile(path: str, in_fnames: List[str]):
    """Translate list of Jack files in directory `path` to XML files.
    """

    for fname in in_fnames:
        in_path = os.path.join(path, f'{fname}.jack')
        with open(in_path, 'r') as in_f:
            out_path = os.path.join(path, f'{fname}.xml')
            with open(out_path, 'w') as out_f:
                c = CompilationEngine(in_f=in_f, out_f=out_f)
                c.compile_class()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compile Jack programs to XML.')
    parser.add_argument('input', help='Path of the program/directory.')

    args = parser.parse_args()

    args = parser.parse_args()
    path = os.path.dirname(args.input)
    fname, ext = os.path.splitext(os.path.basename(args.input))

    if ext != '' and ext != '.jack':
        print('error: must input a Jack file or directory')
        exit(1)

    in_fnames = []
    if ext == '':
        # Directory
        for filepath in os.listdir(path):
            if filepath.endswith('.jack'):
                fname, _ = os.path.splitext(os.path.basename(filepath))
                in_fnames.append(fname)
    elif ext == '.jack':
        # File
        in_fnames.append(fname)

    compile(path, in_fnames)
