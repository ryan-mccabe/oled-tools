"""
    Name: hardware.py
    Purpose: Compare the systems' hardware
    Author: John Sobecki <john.sobecki@oracle.com>
"""
import string
from .plugin import register
from .utils import compare_strings, Table, perror

# --------------------------------------------------
def gather_data(directory_path, result_list, combined_set):
    """Open the file and load the dictionary."""

    file_path = "lspci"

    try:
        with open(
                directory_path + file_path, "r", encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if line[0] in string.hexdigits:
                    result_list.append(line.split()[1]+" "+line.split()[2]+" "+line.split()[3])
                    combined_set.add(line.split()[1]+" "+line.split()[2]+" "+line.split()[3])
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_lspci(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    combined_set = set()
    first_list = []
    second_list = []
    first = ""
    second = ""

    if gather_data(first_dir, first_list, combined_set):
        return 1

    if gather_data(second_dir, second_list, combined_set):
        return 1

    table = Table([" ", "First Report", "Second Report"])

    for hardware in sorted(combined_set):
        #first = ""
        #second = ""
        if hardware not in first_list:
            first = "MISSING"
        else:
            first = hardware
        if hardware not in second_list:
            second = "MISSING"
        else:
            second = hardware

        if first != second:
            first, second = compare_strings(first, second)
            table.row(">", first, second)
        else:
            if detail:
                table.row("", first, second)

    if table.rows:
        print("\n\nlspci Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in lspci comparison.")

    return 0
