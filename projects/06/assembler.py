import os
import argparse
from code import assemble
from parse import Parser

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Assemble HACK programs.')
    parser.add_argument('input', help='Path of the ASM file.')

    args = parser.parse_args()

    in_fname = args.input
    out_fname = f'{os.path.splitext(os.path.basename(in_fname))[0]}.hack'

    p = Parser(in_fname)
    p.parse()

    bin_lines = assemble(p.lines, p.sym_table)
    with open(out_fname, 'w') as f:
        f.write('\n'.join(bin_lines))
