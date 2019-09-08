import argparse
import os
import sys


from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('path',
                    metavar='path',
                    type=str,
                    nargs=1,
                    help='the path to a directory containing audiobook files'
                    )
parser.add_argument('--nocovers',
                    action='store_true',
                    dest='nocovers',
                    help="passing --nocovers means we won't look for covers"
                    )

args = parser.parse_args()
top_path = Path(args.path)

if not top_path.exists():
    print(f'The path {top_path} does not exist.')
    sys.exit()


