"""
    Name: network-scripts.py
    Purpose: Compare the systems' network-scripts files.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import os

from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the file and load the dictionary."""

    file_path = "etc/sysconfig/network-scripts/"
    include_list = ["ifcfg-", "route-", "rule-"]

    try:
        for file_name in os.listdir(directory_path + file_path):
            for prefix in include_list:
                if file_name.startswith(prefix):
                    combined_set.add(file_name)
                    result_dict[file_name] = {}
                    try:
                        with open(
                                directory_path + file_path + file_name,
                                "r",
                                encoding="utf-8"
                        ) as file_handle:
                            line_no = 1
                            for line in file_handle:
                                if not line.startswith("#"):
                                    try:
                                        if len(line.split("=")) > 2:
                                            key = line.split("=")[0]
                                            value = \
                                                "=".join(
                                                    line.split("=")[1:]
                                                ).rstrip()
                                            result_dict[file_name][key] = value
                                        else:
                                            key = line.split("=")[0]
                                            value = line.split("=")[1].rstrip()
                                            result_dict[file_name][key] = value
                                    except IndexError:
                                        result_dict[file_name][line_no] = \
                                            line.rstrip()
                                        line_no += 1
                    except OSError as error:
                        perror(error, "open")
                        return 1
    except FileNotFoundError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_network_scripts(first_dir, second_dir, args):
    """Compares the data between the two direcrories and prints the
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

    table = Table([" ", "File Name:>", "First Report", "Second Report"])

    for file_name in sorted(combined_set):
        if file_name in first_dict:
            first = "PRESENT"
        else:
            first = "MISSING"

        if file_name in second_dict:
            second = "PRESENT"
        else:
            second = "MISSING"

        if first != second:
            table.row(">", file_name, first, second)
        else:
            if detail:
                table.row(" ", file_name, first, second)

    if table.rows:
        #
        # Print the header.
        #
        print("\n\nNetwork Scripts Comparison" + "_" * 54)

        table.write()
    else:
        print("INFO: No differences found in network scripts comparison.")

    table = Table([" ", "File Name", "Option", "First Report", "Second Report"])

    for file_name in sorted(combined_set):
        if file_name in first_dict and file_name in second_dict:
            for option in first_dict[file_name]:
                if option not in second_dict[file_name]:
                    second_dict[file_name][option] = "MISSING"
            for option in second_dict[file_name]:
                if option not in first_dict[file_name]:
                    first_dict[file_name][option] = "MISSING"

    for file_name in sorted(combined_set):
        if file_name in first_dict and file_name in second_dict:
            for option in first_dict[file_name]:
                if first_dict[file_name][option] != \
                   second_dict[file_name][option]:
                    first, second = compare_strings(
                        first_dict[file_name][option],
                        second_dict[file_name][option])
                    table.row(">", file_name, option, first, second)
                else:
                    if detail:
                        table.row(
                            "",
                            file_name,
                            option,
                            first_dict[file_name][option],
                            second_dict[file_name][option])

    if table.rows:
        #
        # Print the header.
        #
        print("\n\nNetwork Options Comparison" + "_" * 54)

        table.write()
    else:
        print("INFO: No differences found in network options comparison.")

    return 0
