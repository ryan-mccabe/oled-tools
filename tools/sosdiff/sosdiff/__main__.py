#
# Copyright (c) 2024, Oracle and/or its affiliates.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
#
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.

"""
    Main module for the sosdiff command
    Purpose:    Do diff checking between sosreports
    Author:     John Sobecki <john.sobecki@oracle.com>
"""

import os
import sys
import argparse

from . import utils
from .plugin import all_plugins
from sosdiff import __version__ as VERSION

def get_args():
    """Get command-line arguments"""

    parser = argparse.ArgumentParser(
        prog='sosdiff',
        description='sosdiff - Compare 2 sosreports',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('dir1',
                        type=str,
                        help='First sos report directory')

    parser.add_argument('dir2',
                        type=str,
                        help='Second sos report directory')

    parser.add_argument('-d',
                        '--detail',
                        help='Run with extensive sosreport detailed checking',
                        action='store_true')

    parser.add_argument('-o',
                        '--override',
                        help='Run despite mis-matched OL version or CPU architecture',
                        action='store_true')

    parser.add_argument('-c',
                        '--color',
                        help='Always output color escape sequences',
                        action='store_true')

    parser.add_argument('-v', '--version', action='version', version="%(prog)s " + VERSION)

    return parser.parse_args()

def main():
    """Make sure the arguments are really sosreports"""
    args = get_args()
    dir1 = args.dir1
    if dir1[-1] != '/':
        dir1 = dir1+'/'
    dir2 = args.dir2
    if dir2[-1] != '/':
        dir2 = dir2+'/'
    if args.color:
        utils.COLOR = True

    if not os.path.isdir(dir1) or not os.path.isdir(dir2):
        print("ERROR: Both arguments must be valid directories")
        sys.exit(1)
    if not os.path.isfile(dir1+"uname"):
        print(
            f'ERROR: File not found: {dir1}uname',
            '- this directory may not be an sosreport', file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(dir2+"uname"):
        print(
            f'ERROR: File not found: {dir2}uname',
            '- this directory may not be an sosreport', file=sys.stderr)
        sys.exit(1)

    print("sosdiff", VERSION, " Arguments validated .. beginning analysis ...  ")
    for name, plugin in all_plugins():
        try:
            plugin(dir1, dir2, args)
        except KeyboardInterrupt:
            sys.exit("interrupted")
        except BrokenPipeError:
            break
        except Exception as error:
            print(f"encountered error in {name} {str(error)}")


if __name__ == "__main__":
    main()
