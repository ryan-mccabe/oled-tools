"""
    Name: slabinfo.py
    Purpose: Compare the systems' slabinfo data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict, combined_set):
    """Open the files and load the dictionary."""

    file_path = "proc/slabinfo"

    try:
        with open(
                directory_path + file_path,
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if "slabinfo" not in line and "# name" not in line:
                    name = line.split()[0]
                    size = int(line.split()[2]) * int(line.split()[3])
                    result_dict[name] = size
                    combined_set.add(name)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_slabinfo(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    first = ""
    second = ""
    combined_set = set()
    missing_flag = 0
    diff = 0
    diff_threshold = 5

    if gather_data(first_dir, first_dict, combined_set):
        return 1

    if gather_data(second_dir, second_dict, combined_set):
        return 1

    table = Table([" ", "Name", "First Report", "Second Report"])

    for name in sorted(combined_set):
        missing_flag = 0
        diff = 0
        if name not in first_dict.keys():
            first = "MISSING"
            missing_flag = 1
        else:
            first = str(first_dict[name])

        if name not in second_dict.keys():
            second = "MISSING"
            missing_flag = 1
        else:
            second = str(second_dict[name])

        if not missing_flag and first != "0" and second != "0":
            diff = first_dict[name] / second_dict[name]
            if diff < 1:
                diff *= 100

        #
        # Display only those values exceeding 5% difference, and those where
        # the value is missing.
        #
        if diff > diff_threshold or missing_flag:
            first, second = compare_strings(first, second)

            table.row(">", name, first, second)
        else:
            if detail:
                table.row(" ", name, first, second)

    if table.rows:
        print("\n\nSlabinfo Comparison" + "_" * 63)
        table.write()
    else:
        print("INFO: No differences found in slabinfo comparison.")

    return 0
