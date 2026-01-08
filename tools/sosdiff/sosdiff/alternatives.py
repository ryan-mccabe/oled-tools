"""
    Name: alternatives.py
    Purpose: Compare the systems' alternatives data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import os
from pathlib import Path
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the files and load the dictionary."""

    file_path = "sos_commands/alternatives/"

    try:
        if not os.path.isdir(directory_path + file_path):
            raise FileNotFoundError(
                32,
                "No such file or directory",
                directory_path + file_path
            )
    except FileNotFoundError as error:
        perror(error, "open")
        return 1

    for file_name in \
            Path(directory_path, file_path).glob('alternatives_--display_*'):
        name = str(file_name).split("--display_")[-1]
        try:
            with open(
                    str(file_name),
                    "r",
                    encoding="utf-8"
            ) as file_handle:
                for line in file_handle:
                    if "link currently points to" in line:
                        result_dict[name] = line.split()[-1].rstrip()
                        combined_set.add(name)
                        continue
        except OSError as error:
            perror(error, "open")
            return 1

    return 0


# --------------------------------------------------
@register
def compare_alternatives(first_dir, second_dir, args):
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
        print("\n\nAlternatives Comparison" + "_" * 59)
        table.write()
    else:
        print("INFO: No differences found in alternatives comparison.")

    return 0
