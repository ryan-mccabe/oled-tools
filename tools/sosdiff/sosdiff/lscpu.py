"""
    Name: lscpu.py
    Purpose: Compare the systems' lscpu data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set, flags_list,
                flags_set):
    """Open the files and load the dictionary."""

    file_path = "sos_commands/processor/lscpu"

    try:
        with open(
                directory_path + file_path,
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if "Flags:" not in line:
                    name = line.split(':')[0]
                    result_dict[name] = line.split(':')[1].strip()
                    combined_set.add(name)
                else:
                    line = line.split(':')[1].strip()
                    for flag in line.split():
                        flags_list.append(flag)
                        flags_set.add(flag)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_lscpu(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    first_flags = []
    second_flags = []
    first = ""
    second = ""
    combined_set = set()
    combined_flags = set()

    if gather_data(first_dir, first_dict, combined_set, first_flags,
                   combined_flags):
        return 1

    if gather_data(second_dir, second_dict, combined_set, second_flags,
                   combined_flags):
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

    for flag in sorted(combined_flags):
        if flag not in first_flags:
            first = "MISSING"
        else:
            first = flag

        if flag not in second_flags:
            second = "MISSING"
        else:
            second = flag

        if first != second:
            first, second = compare_strings(first, second)

            table.row(">", "Flags", first, second)
        else:
            if detail:
                table.row(" ", "Flags", first, second)

    if table.rows:
        print("\n\nlscpu Comparison" + "_" * 63)
        table.write()
    else:
        print("INFO: No differences found in lscpu comparison.")

    return 0
