#!/usr/bin/env python3
'''
    Copyright 2022-2023 TopDevPros
    Last modified: 2023-10-01
'''

import os

# get the current directory before we enter the virtual environment
CURRENT_DIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
os.chdir(CURRENT_DIR)
from ve import activate                    # pylint: disable=wrong-import-position
activate()

from solidlibs.os.command import run                          # pylint: disable=wrong-import-position


def main(args):
    ''' Run safelog in a virtualenv. '''

    run('safelog')

if __name__ == "__main__":
    main()
