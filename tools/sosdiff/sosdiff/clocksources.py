"""
    Name: clocksources.py
    Purpose: Compare the systems' clocksources data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import os
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the files and load the dictionary."""

    file_path = "sys/devices/system/clocksource/clocksource0/"

    try:
        for file_name in os.listdir(directory_path + file_path):
            try:
                with open(
                        directory_path + file_path + file_name,
                        "r",
                        encoding="utf-8"
                ) as file_handle:
                    for line in file_handle:
                        result_dict[file_name] = line.rstrip()
                        combined_set.add(file_name)
            except OSError as error:
                perror(error, "open")
                return 1
    except FileNotFoundError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_clocksources(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    first = ""
    second = ""
    combined_set = set()

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

    table = Table([" ", "Name", "First Report", "Second Report"])

    for name in sorted(combined_set):
        if name not in first_dict.keys():
            first = "MISSING"
        else:
            first = first_dict[name]

        if name not in second_dict.keys():
            second = "MISSING"
        else:
            second = second_dict[name]

        if first != second:
            first, second = compare_strings(first, second)

            table.row(">", name, first, second)
        else:
            if detail:
                table.row(" ", name, first, second)

    if table.rows:
        print("\n\nClocksource Comparison" + "_" * 59)
        table.write()
    else:
        print("INFO: No differences found in clocksources comparison.")

    return 0
