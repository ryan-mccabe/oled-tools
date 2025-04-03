"""
    Name: systemd.py
    Purpose: sosdiff systemd units check
    Author : Jeffery Yoder <jeffery.yoder@oracle.com>
"""

from .plugin import register
from .utils import compare_strings, Table, perror


# --------------------------------------------------
def gather_data(directory_path, results_dict):
    """Populate the passed list with data from the file in the passed
    directory."""

    file_name = "sos_commands/systemd/systemctl_list-units"

    #
    # Unit types to include in the report.
    #
    include_list = [
        "automount",
        "mount",
        "path",
        "service",
        "socket",
        "swap",
        "target",
        "timer",
    ]

    try:
        with open(
                directory_path + file_name,
                "r",
                encoding="utf-8",
        ) as file_handle:
            for line in file_handle:
                #
                # Exclude blank lines
                #
                if not line.strip():
                    continue
                try:
                    unit, loaded, state, substate, desc = line.split(maxsplit=4)
                    #
                    # Include only unit types we are interested in.
                    #
                    unit_name, unit_type = unit.rsplit(".", maxsplit=1)
                    if unit_type in include_list:
                        results_dict[unit] = " ".join([loaded, state, substate])
                except ValueError as error:
                    # This command output has the legend and headers included.
                    # Just ignore errors.
                    continue
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


# --------------------------------------------------
@register
def compare_systemd(first_dir, second_dir, args):
    """Collect services, targets, and timers"""
    detail = args.detail

    first_dict = {}
    second_dict = {}
    combined_set = set()
    exclude_list = ["user", "systemd-cryptsetup"]
    table = Table(["", "Unit Name:>", "First Report", "Second Report"])

    #
    # Build a dictionary from the first and second set of data.
    #
    if gather_data(first_dir, first_dict):
        return 1

    if gather_data(second_dir, second_dict):
        return 1

    #
    # Generate a unique list of service names.
    #
    combined_set = first_dict.keys() | second_dict.keys()

    #
    # Iterate through the unique list.
    #
    for name in sorted(combined_set):

        excluded = 0

        #
        # Exclude some service names.
        #
        for exclude in exclude_list:
            if name.startswith(exclude):
                excluded += 1
        if not excluded:
            if name not in first_dict:
                first_dict[name] = "MISSING"
            if name not in second_dict:
                second_dict[name] = "MISSING"

            if first_dict[name] != second_dict[name]:
                first, second = compare_strings(
                    first_dict[name], second_dict[name]
                )
                table.row(">", name, first, second)
            else:
                if detail:
                    table.row("", name, first_dict[name], second_dict[name])

    #
    # If there is data in the table, display it.
    #
    if len(table.rows) > 0:
        print("\n\nSystemd Units Comparison" + "_" * 63)
        table.write()
    else:
        print("INFO: No differences found in systemd comparison.")

    return 0
