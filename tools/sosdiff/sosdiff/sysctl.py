"""
    Name: new_sysctl.py
    Purpose: Compare the values from sysctl -a.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import fnmatch

from .plugin import register
from .utils import compare_strings, Table, perror
from .utils import open_package_data


# --------------------------------------------------
@register
def compare_sysctl(first_dir, second_dir, args):
    """Parses through the data collected and compares the results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    combined_set = set()
    exclude_list = []

    #
    # Load the exclude list.
    #
    try:
        with open_package_data(
                "sysctl_exclude.txt",
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if not line.startswith("#"):
                    exclude_list.append(line.rstrip())
    except OSError as error:
        perror(error, "open")
        return 1
    #
    # Populate the dictionaries.  Be sure to pass along any failures to the
    # calling function.
    #
    failed = gather_sysctl_data(first_dir, first_dict, exclude_list)
    if failed:
        return failed

    failed = gather_sysctl_data(second_dir, second_dict, exclude_list)
    if failed:
        return failed

    #
    # Get a unique list of names.
    #
    for name in first_dict:
        combined_set.add(name)

    for name in second_dict:
        combined_set.add(name)

    table = Table(["", "Name:>", "First Report", "Second Report"])

    #
    # Walk the list of unique names and populate the table.
    #
    for name in sorted(combined_set):
        if name not in first_dict:
            first_dict[name] = "MISSING"

        if name not in second_dict:
            second_dict[name] = "MISSING"

        if first_dict[name] != second_dict[name]:
            first, second = compare_strings(
                first_dict[name].expandtabs(4),
                second_dict[name].expandtabs(4)
            )
            table.row(">", name, first, second)
        else:
            if detail:
                table.row(" ", name, first_dict[name], second_dict[name])

    if table.rows:
        #
        # Print the module header.
        #
        print("\n\nSysctl Comparison" + "_" * 63)

        #
        # Print the data.
        #
        table.write()
    else:
        #
        # Print one-liner stating no differences.
        #
        print("INFO: No differences found in sysctl comparison.")

    return None


# --------------------------------------------------
def gather_sysctl_data(directory, results, excludes):
    """Opens the necessary files and loads the data."""

    file_name = "sos_commands/kernel/sysctl_-a"

    #
    # Open the file and load the results for settings that are not excluded.
    #
    try:
        with open(
                directory + file_name,
                'r',
                encoding='utf-8'
        ) as file_handle:
            for line in file_handle:
                excluded = 0
                #
                # Has to be in the "name = value" format.
                #
                if "=" in line:
                    name = line.split("=")[0].rstrip()
                    setting = line.split("=")[1].strip()
                    for excluded_name in excludes:
                        if fnmatch.fnmatch(name, excluded_name):
                            excluded += 1
                    if not excluded:
                        results[name] = setting
        return 0
    except OSError as error:
        perror(error, "open")
        return 1
