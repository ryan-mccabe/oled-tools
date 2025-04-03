"""
    Name: mounts.py
    Purpose: Compare the systems' mount points and mount options.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import sys, os, re
from .utils import compare_strings, Table, perror
from .plugin import register

def octunescape(s: str):
    """
    Remove octal escape sequences from a string.
    """
    octesc = re.compile(r'(^|(?<=[^\\]))\\(?P<ord>[0-9]{3})')
    return octesc.sub(lambda m: chr(int(m['ord'], base = 8)), s)

# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the file and load the dictionary."""

    mounts_source = "proc/mounts"

    try:
        with open(directory_path + mounts_source, "r",
                  encoding="utf-8", errors = sys.getfilesystemencodeerrors()
        ) as proc_mounts:
            for line in proc_mounts:
                try:
                    spec, file, vfstype, mountopts, freq, passno = line.split(' ')
                    mount_path = octunescape(file)
                    result_dict[mount_path] = {}
                    for option in mountopts.split(","):
                        if "=" in option:
                            key, value = option.split("=", maxsplit = 1)
                            result_dict[mount_path][key] = value
                        else:
                            result_dict[mount_path][option] = "True"
                    combined_set.add(mount_path)
                except ValueError as e:
                    print(f"ERROR: Cannot parse line {line.strip()!r} in {proc_mounts.name!r}: {e}", file = sys.stderr)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_mounts(first_dir, second_dir, args):
    """Compares the data between the two direcrories and prints the
    results."""

    combined_set = set()
    first_dict = {}
    second_dict = {}
    first = ""
    second = ""

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

#
# Compare mount points.
#
    table = Table([" ", "First Report", "Second Report"])

    for mount in sorted(combined_set):
        if mount not in first_dict:
            first = "MISSING"
        else:
            first = mount
        if mount not in second_dict:
            second = "MISSING"
        else:
            second = mount
        detail = args.detail
        if first != second:
            first, second = compare_strings(first, second)
            table.row(">", first, second)
        else:
            if detail:
                table.row("", first, second)

    if table.rows:
        print("\n\nMounts Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in mounts comparison.")

#
# Compare mount options.
#
    table = Table([" ", "Mount:>", "Option", "First Report", "Second Report"])

    for mount in sorted(combined_set):
        options_set = set()
        #
        # Compare only mounts that are on both systems.
        #
        if mount in first_dict and mount in second_dict:
            for option in first_dict[mount]:
                options_set.add(option)
            for option in second_dict[mount]:
                options_set.add(option)

            for option in options_set:
                if option not in first_dict[mount].keys():
                    first = "MISSING"
                else:
                    first = first_dict[mount][option]
                if option not in second_dict[mount].keys():
                    second = "MISSING"
                else:
                    second = second_dict[mount][option]

                if first != second:
                    first, second = compare_strings(first, second)
                    table.row(">", mount, option, first, second)
                else:
                    if detail:
                        table.row("", mount, option, first, second)

    if table.rows:
        print("\n\nMount Options Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in mount options comparison.")

    return 0
