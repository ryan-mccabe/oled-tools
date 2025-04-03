"""
    Name: network_stats.py
    Purpose: Compare the systems' network stats data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from .plugin import register
from .utils import compare_strings, Table, perror, open_package_data


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the files and load the dictionary."""

    include_file = "network_stats_include.txt"
    file_path = "sos_commands/networking/nstat_-zas"
    include_list = []

    try:
        with open_package_data(
                include_file,
                "r",
                encoding="utf8"
        ) as file_handle:
            for line in file_handle:
                if "#" not in line:
                    include_list.append(line.rstrip())
    except OSError as error:
        perror(error, "open")
        return 1

    try:
        with open(
                directory_path + file_path,
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if "#kernel" not in line:
                    name = line.split()[0]
                    if name in include_list:
                        result_dict[name] = line.split()[1]
                        combined_set.add(name)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_network_stats(first_dir, second_dir, args):
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
        print("\n\nNetwork Stats Comparison" + "_" * 56)
        table.write()
    else:
        print("INFO: No differences found in network stats comparison.")

    return 0
