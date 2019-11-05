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
parser.add_argument('--no-covers',
                    action='store_true',
                    help="passing --no-covers means we won't look for covers"
                    )
my_group = parser.add_mutually_exclusive_group(required=False)
my_group.add_argument('-v', '--verbose', action='store_true')
my_group.add_argument('-s', '--silent', action='store_true')

args = parser.parse_args()
top_path = Path(args.path)

if not top_path.exists():
    print(f'The path {top_path} does not exist.')
    sys.exit()


