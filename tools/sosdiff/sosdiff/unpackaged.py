"""
    Name: unpackaged.py
    Purpose: Compare the systems' unpackaged data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the file and load the dictionary."""

    file_path = "sos_commands/unpackaged/unpackaged"

    try:
        with open(
                directory_path + file_path, "r", encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if len(line.split()) == 1:
                    result_dict[line.rstrip()] = "INSTALLED"
                    combined_set.add(line.rstrip())
                else:
                    name = line.split()[0]
                    value = " ".join(line.split()[1:len(line.split())])
                    result_dict[name] = value
                    combined_set.add(name)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_unpackaged(first_dir, second_dir, args):
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
        print("\n\nUnpackaged Comparison" + "_" * 59)
        table.write()
    else:
        print("INFO: No differences found in unpackaged comparison.")

    return 0
