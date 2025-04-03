"""
    Name: datetime.py
    Purpose: Compare the systems' time settings.
    Author: Jeffery Yoder <jeffery.yoder@oracle.com>
"""
from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_time_data(directory_path, result_dict, include_list):
    """Open the file and load the dictionary."""

    try:
        with open(
                directory_path + "date",
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                name = line.split(":")[0].strip()
                if name in include_list:
                    result_dict[name] = line.split(":")[1].strip()
    except OSError as error:
        perror(error, "open")
        return 1
    #
    # On older OS versions the date file contains just the date.
    #
    if len(result_dict) == 0:
        for name in include_list:
            result_dict[name] = "MISSING"

    #
    # On older OS versions the date file contains just the date.
    #
    if len(result_dict) == 0:
        for name in include_list:
            result_dict[name] = "MISSING"

    return 0


# --------------------------------------------------
@register
def compare_time(first_dir, second_dir, args):
    """Compares the data between the two dictionaries and prints the
       results."""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    include_list = [
        "Time zone",
        "System clock synchronized",
        "NTP service",
        "RTC in local TZ"
    ]
    first = ""
    second = ""

    if gather_time_data(first_dir, first_dict, include_list):
        return 1

    if gather_time_data(second_dir, second_dict, include_list):
        return 1

    table = Table([" ", "Name:>", "First Report", "Second Report"])

    for name in include_list:
        try:
            if first_dict[name] != second_dict[name]:
                first, second = compare_strings(
                    first_dict[name],
                    second_dict[name]
                )
                table.row(">", name, first, second)
            else:
                if detail:
                    table.row(" ", name, first_dict[name], second_dict[name])
        except KeyError:
            print("INFO: Skipping time comparison due to KeyError.")
            return 1

    if table.rows:
        print("\n\nTime Comparison" + "_" * 65)
        table.write()
    else:
        print("INFO: No differences found in time comparison.")

    return 0


# --------------------------------------------------
def gather_uptime_data(directory_path, result_list):
    """Open the file and load the list."""

    try:
        with open(
                directory_path + "uptime",
                "r",
                encoding="utf-8"
        ) as file_handle:
            for line in file_handle:
                result_list.extend(line.replace(",", "").split())
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_uptime(first_dir, second_dir, args):
    """Compares the data between the two lists and displays the results."""
    detail = args.detail

    first_list = []
    second_list = []
    first = ""
    second = ""

    if gather_uptime_data(first_dir, first_list):
        return 1

    if gather_uptime_data(second_dir, second_list):
        return 1

    table = Table([" ", "First Report", "Second Report"])

    if len(first_list) == 10:
        first = first_list[2]
    else:
        first = f"{first_list[2]} {first_list[3]}, {first_list[4]}"

    if len(second_list) == 10:
        second = second_list[2]
    else:
        second = f"{second_list[2]} {second_list[3]}, {second_list[4]}"

    if first != second:
        first, second = compare_strings(first, second)
        table.row(">", first, second)
    else:
        if detail:
            table.row("", first, second)

    if table.rows:
        print("\n\nUptime Comparison" + "_" * 63)
        table.write()
    else:
        print("INFO: No differences found in uptime comparison.")

    return 0
