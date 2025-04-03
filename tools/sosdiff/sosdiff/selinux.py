"""
    Name: selinux.py
    Purpose: Compare the status of SELinux
    Author: Pablo Prado <pablo.prado@oracle.com>
"""
import string
from .plugin import register
from .utils import compare_strings, Table, perror

# --------------------------------------------------
def gather_data(directory_path, result_dict):
    """Open the file and load key-value lines from sestatus into a dictionary."""

    file_path = "sos_commands/selinux/sestatus"

    try:
        with open(directory_path + file_path, "r", encoding="utf-8") as file_handle:
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    result_dict[key] = value

    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_sestatus(first_dir, second_dir, args):
    """Compare the data from two different sos_reports (or directories) 
    for SELinux status information."""
    detail = args.detail

    first_dict = {}
    second_dict = {}

    if gather_data(first_dir, first_dict):
        return 1

    if gather_data(second_dir, second_dict):
        return 1

    table = Table(["Name", "First Report", "Second Report"])

    differences_found = False

    # Combine all keys from both dictionaries to ensure all are covered
    all_keys = set(first_dict.keys()).union(second_dict.keys())

    for key in sorted(all_keys):
        first = first_dict.get(key, "MISSING")
        second = second_dict.get(key, "MISSING")

        if first != second:
            differences_found = True
            first, second = compare_strings(first, second)
            table.row(key, first, second)
        else:
            if detail:
                table.row(key, first, second)

    if differences_found or detail:
        print("\n\nSELinux Status Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in SELinux Status comparison.")

    return 0
