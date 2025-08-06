"""
    Name: exadata.py
    Purpose: Compare the systems' imageinfo data.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import re
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, result_dict):
    """Open the file and load the dictionary."""

    file_path = "sos_commands/exadata/imageinfo"

    try:
        with open(
                directory_path + file_path, "r", encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                if ":" in line:
                    name = line.split(":")[0].strip()
                    value = line.split(":")[1].strip()
                    result_dict[name] = value
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
def is_exadata(directory_path):
    """Check if this is an Exadata system."""

    file_path = "installed-rpms"

    try:
        with open(
                directory_path + file_path, "r", encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                match = re.match("exadata", line)
                if match:
                    return 0
    except OSError as error:
        perror(error, "open")

    return 1


# --------------------------------------------------
@register
def compare_exadata(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
    results."""
    detail = args.detail

    if is_exadata(first_dir):
        print(
            f"INFO: {first_dir} does not appear to be from an Exadata system."
        )
        return 1

    if is_exadata(second_dir):
        print(
            f"INFO: {second_dir} does not appear to be from an Exadata system."
        )
        return 1

    first_dict = {}
    second_dict = {}
    first = ""
    second = ""

    if gather_data(first_dir, first_dict):
        return 1

    if gather_data(second_dir, second_dict):
        return 1

    table = Table([" ", "Name:>", "First Report", "Second Report"])

    for name in first_dict:
        if first_dict[name] != second_dict[name]:
            first, second = compare_strings(
                first_dict[name], second_dict[name]
            )
            table.row(">", name, first, second)
        else:
            if detail:
                table.row(" ", name, first_dict[name], second_dict[name])

    if table.rows:
        print("\n\nExadata Comparison" + "_" * 62)
        table.write()
    else:
        print("INFO: No differences found in exadata comparison.")

    return 0
