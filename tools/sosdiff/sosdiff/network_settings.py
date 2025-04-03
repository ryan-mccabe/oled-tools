"""
    Name: network_settings.py
    Purpose: Compare the systems' network settings data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from pathlib import Path
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the files and load the dictionary."""

    file_path = "sos_commands/networking/"

    for path_name in \
            Path(directory_path, file_path).glob('ethtool_-[gikl]_*'):
        file_name = str(path_name).split('/')[-1]
        result_dict[file_name] = []
        combined_set.add(file_name)
        if "_lo" not in file_name:
            try:
                with open(
                        str(path_name),
                        "r",
                        encoding="utf-8"
                ) as file_handle:
                    for line in file_handle:
                        if line != "\n":
                            result_dict[file_name].append(line.rstrip())
            except OSError as error:
                perror(error, "open")
                return 1

    return 0


# --------------------------------------------------
@register
def compare_network_settings(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    first = ""
    second = ""
    combined_set = set()
    max_lines = 0

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

    table = Table([" ", "File Name", "First Report", "Second Report"])

    for name in sorted(combined_set):

        if name in first_dict.keys() and name in second_dict.keys():
            if len(second_dict[name]) > len(first_dict[name]):
                max_lines = len(second_dict[name])
            else:
                max_lines = len(first_dict[name])

            if first_dict[name] != second_dict[name]:
                for i in range(0, max_lines):
                    if i+1 > len(first_dict[name]):
                        first_dict[name].append("MISSING")
                    if i+1 > len(second_dict[name]):
                        second_dict[name].append("MISSING")
                    first = first_dict[name][i].expandtabs(4)
                    second = second_dict[name][i].expandtabs(4)
                    if first != second:
                        first, second = compare_strings(first, second)
                        table.row(">", name, first, second)
                    else:
                        table.row(" ", name, first, second)
            else:
                if detail:
                    for i in range(0, max_lines):
                        first = first_dict[name][i].expandtabs(4)
                        second = second_dict[name][i].expandtabs(4)
                        table.row(" ", name, first, second)

    if table.rows:
        print("\n\nNetwork Settings Comparison" + "_" * 53)
        table.write()
    else:
        print("INFO: No differences found in network settings comparison.")

    return 0
