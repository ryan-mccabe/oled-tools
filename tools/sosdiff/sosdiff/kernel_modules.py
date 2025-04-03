"""
    Name: kernel_modules.py
    Purpose: Compare the installed kernel modules from two different sos
             reports.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import os
from .plugin import register
from .utils import Table, perror, compare_strings


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the file and load the list and set."""

    try:
        with open(
                directory_path + "lsmod",
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                name = line.split()[0]
                if name != "Module":
                    result_dict[name] = ""
                    combined_set.add(name)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
def gather_option_data(directory_path, result_dict, module, option):
    """Open the file and load the list and set."""

    try:
        with open(
                directory_path,
                "r",
                encoding="utf-8"
        ) as file_handle:
            result_dict[module][option] = file_handle.readline().rstrip()
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_kernel_modules(first_dir, second_dir, args):
    """Compares the data between the two lists and prints the results."""
    detail = args.detail

    name = ""
    first_dict = {}
    second_dict = {}
    first_options_dict = {}
    second_options_dict = {}
    combined_set = set()
    first_missing = 0
    second_missing = 0

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

    table = Table([" ", "Name:>", "Loaded", "Loaded"])

    for name in sorted(combined_set):
        differ = 0

        if name in first_dict:
            first_dict[name] = "YES"
        else:
            first_dict[name] = "NO"
            first_missing += 1
            differ += 1

        if name in second_dict:
            second_dict[name] = "YES"
        else:
            second_dict[name] = "NO"
            second_missing += 1
            differ += 1

        if differ:
            table.row(">", name, first_dict[name], second_dict[name])
        else:
            if detail:
                table.row(" ", name, first_dict[name], second_dict[name])

    if table.rows:
        #
        # Print the header.
        #
        print("\n\nKernel Module Comparison" + "_" * 56)

        table.write()

        print(f"Total unique kernel modules: {len(combined_set)}")
        print(f"Modules missing from the first report: {first_missing}")
        print(f"Modules missing from the second report: {second_missing}")
    else:
        print("INFO: No differences found in kernel module comparison.")

#
# Check kernel module options.
#
    table = Table(["", "Module", "Option", "First Report", "Second Report"])
    for module in sorted(combined_set):
        if first_dict[module] == "YES" and second_dict[module] == "YES":
            file_path = "sys/module/" + module + "/parameters/"
            if os.path.isdir(first_dir + file_path) and \
                    os.path.isdir(second_dir + file_path):
                first_options_dict[module] = {}
                for option in os.listdir(first_dir + file_path):
                    gather_option_data(first_dir + file_path + option,
                                       first_options_dict,
                                       module,
                                       option)
                second_options_dict[module] = {}
                for option in os.listdir(second_dir + file_path):
                    gather_option_data(second_dir + file_path + option,
                                       second_options_dict,
                                       module,
                                       option)

    for module in first_options_dict.keys() | second_options_dict.keys():
        for option in first_options_dict[module].keys() | \
                second_options_dict[module].keys():
            #
            # Normalize data
            #
            if option not in first_options_dict[module]:
                first_options_dict[module][option] = "MISSING"
            if option not in second_options_dict[module]:
                second_options_dict[module][option] = "MISSING"

            if first_options_dict[module][option] != \
                    second_options_dict[module][option]:
                first, second = compare_strings(
                    first_options_dict[module][option],
                    second_options_dict[module][option])
                table.row(">", module, option, first, second)
            else:
                if detail:
                    table.row(
                        " ",
                        module,
                        option,
                        first_options_dict[module][option],
                        second_options_dict[module][option])

    if table.rows:
        #
        # Print the header.
        #
        print("\n\nKernel Module Options Comparison" + "_" * 48)

        table.write()
    else:
        print("INFO: No differences found in kernel module options comparison.")

    return 0
