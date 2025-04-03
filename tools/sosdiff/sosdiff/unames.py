"""
    Name:       unames.py
    Purpose:    Do sanity checking between sosreports
    Author:     John Sobecki <john.sobecki@oracle.com>
"""
import os
import sys

from .plugin import register
from .utils import compare_strings
from .utils import Table

def versiontuple(vers):
    """ split up the major kernel version string """
    return tuple(map(int, (vers.split("."))))

@register
def compare_unames(dir1, dir2, args):
    """
    Diffs the contents of files named "uname" in the given directories.
    Abort if major differences exist.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
        override_flag: Don't terminate if O/S Release or Arch are different

    Raises:
        FileNotFoundError: If either "uname" file is not found.
   """
    override_flag = args.override
    file1 = os.path.join(dir1, "uname")
    file2 = os.path.join(dir2, "uname")
    try:
        with open(file1, 'r') as sosreport1, open(file2, 'r') as sosreport2:
            str1 = sosreport1.read()
            str2 = sosreport2.read()
            host1 = str1.split()[1]
            host2 = str2.split()[1]
            uname1 = str1.split()[2]
            uname2 = str2.split()[2]
            uname1, uname2 = compare_strings(uname1, uname2)
            table = Table(["", "First Report", "Second Report"])
            table.row(">", host1, host2)
            table.row(">", uname1, uname2)
            table.write()
            release1 = uname1.split(".")[-2]
            release2 = uname2.split(".")[-2]
            if release1 != release2:
                if override_flag:
                    print("O/S releases are not identical but --override specified, Continuing.")
                    return
                print("ERROR: O/S releases not identical and --override not specified, Exiting.")
                sys.exit(1)

            arch1 = uname1.split(".")[-1]
            arch2 = uname2.split(".")[-1]
            if arch1 != arch2:
                if override_flag:
                    print("Computer arch mis-match but --override specified, Continuing.")
                    return
                print("ERROR: Computer arch mis-match and --override not specified, Exiting.")
                sys.exit(1)

    except FileNotFoundError as exception_fn:
        print(f"ERROR: File not found: {exception_fn.filename}")
        raise
