"""
    Name: kdump.py
    Purpose: Compare the systems' kdump settings.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import re
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the file and load the dictionary."""

    file_path = "etc/kdump.conf"
    tmp_list = []

    try:
        with open(
                directory_path + file_path, "r", encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                match = re.match("^(#|$)", line)
                if not match:
                    tmp_list = line.rstrip().split()
                    tmp_name = "".join(tmp_list[0:1])
                    tmp_setting = " ".join(tmp_list[1:len(tmp_list)])
                    result_dict[tmp_name] = tmp_setting
                    combined_set.add("".join(tmp_list[0:1]))
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_kdump(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    combined_set = set()
    first_dict = {}
    second_dict = {}
    first = ""
    second = ""

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

    table = Table([" ", "Name:>", "First Report", "Second Report"])

    for name in sorted(combined_set):
        if name not in first_dict:
            first_dict[name] = "MISSING"
        if name not in second_dict:
            second_dict[name] = "MISSING"

        if first_dict[name] != second_dict[name]:
            first, second = compare_strings(
                first_dict[name],
                second_dict[name]
            )
            table.row(">", name, first, second)
        else:
            if detail:
                table.row("", name, first_dict[name], second_dict[name])

    if table.rows:
        print("\n\nKdump Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in kdump comparison.")

    return 0
