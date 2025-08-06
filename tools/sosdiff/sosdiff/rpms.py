"""
    Name: rpms.py
    Purpose: Compare the installed RPMs from two different sos reports.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
import re
import sys
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_rpm_data(directory, results):
    """Open the file and populate the list with RPM data."""

    #
    # Open the first file and parse through the data.
    #
    try:
        with open(
                directory + "installed-rpms",
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                bits = parse_rpm_name(line.rstrip().split(" ")[0])
                if bits:
                    results.append(bits)
                else:
                    print(f'ERROR: can\'t parse "{line}"', file=sys.stderr)
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_rpms(first_dir, second_dir, args):
    """Compare the RPMs"""
    detail = args.detail

    first_list = []
    second_list = []
    combined_set = set()
    first_missing = 0
    second_missing = 0
    different_versions = 0
    result_count = 0

    if gather_rpm_data(first_dir, first_list):
        return 1

    if gather_rpm_data(second_dir, second_list):
        return 1

    first_dict = dict(first_list)
    second_dict = dict(second_list)
    combined_set = first_dict.keys() | second_dict.keys()

    #
    # For each unique name, check for its existence in both lists and compare
    # the versions, building the output line as we go.
    #
    table = Table(["", "RPM Name", "First Report", "Second Report"])
    for name in sorted(combined_set):
        missing_either = False

        if name in first_dict:
            first = first_dict[name]
        else:
            first = "MISSING"
            missing_either = True
            first_missing += 1

        if name in second_dict:
            second = second_dict[name]
        else:
            second = "MISSING"
            missing_either = True
            second_missing += 1

        differ = first != second or missing_either

        # Add in diff formatting
        if not missing_either:
            if first != second:
                different_versions += 1
            first, second = compare_strings(first, second)
        if differ or detail:
            table.row(">" if differ else "", name, first, second)
            result_count += 1

    #
    # If there are any rows to print, print the header and the data.
    #
    if result_count > 0:
        print("\n\nRPM Comparison" + "_" * 66)
        table.write()

        #
        # Print metrics.
        #
        print(f"Total unique RPMs: {len(combined_set)}")
        print(f"Missing from first report: {first_missing}")
        print(f"Missing from second report: {second_missing}")
        print(f"Total mismatched versions: {different_versions}")
    else:
        print("INFO: No differences found in rpm comparison.")

    return 0


# --------------------------------------------------
def parse_rpm_name(rpm_name):
    """Split the name into it's alphabetic and numeric components.  This is a
    close approximation of name and version."""

    match = re.match(r"(.*?)-(\d.*)", rpm_name)
    if match:
        return match.groups()
    return None
