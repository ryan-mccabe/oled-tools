"""
    Name: meminfo.py
    Purpose: Compare the values from /proc/meminfo
    Author: Luis Gomez <luis.en.gomez@oracle.com>
"""


from .plugin import register
from .utils import compare_strings
from .utils import bold
from .utils import Table, perror
from .utils import open_package_data


def gather_mem_values(directory_path, results):
    """ Function to get values from /proc/meminfo """
    file_path = "proc/meminfo"
    try:
        with open(directory_path + file_path, "r", encoding="utf-8") as file_handle:
            for line in file_handle:
                key = line.rstrip().split(":")[0]
                results[key] = line.rstrip().split(":")[1].lstrip()
    except OSError as error:
        perror(error, "open")
        return 1

    return 0


def load_thresholds(values):
    """Function to load thresholds from meminfo_params.txt"""
    try:
        with open_package_data("meminfo_params.txt", "r", encoding="utf-8") as file_handle:
            for line in file_handle:
                if not line.startswith("#") and ":" in line:
                    cur_value = line.rstrip().split(":")[1].lstrip()
                    if "kB" in cur_value:
                        str_value = cur_value.lstrip().split("kB")[0].rstrip()
                        if str_value.isdigit() == 0:
                            print("WARNING: Malformed threshold line: ", line)
                            return
                    if "%" in cur_value:
                        str_value = cur_value.lstrip().split("%")[0].rstrip()
                        if str_value.isdigit() == 0:
                            print("WARNING: Malformed threshold line: ", line)
                            return
                    values[line.rstrip().split(":")[0]] = cur_value
    except OSError as error:
        perror(error, "open")


def eval_threshold(name, values, first_dict, second_dict):
    """Determine if current value is over threshold"""
    first_threshold = 0
    second_threshold = 0
    first_value = 0
    second_value = 0
    if first_dict[name].lstrip().split("kB")[0].rstrip().isdigit():
        first_value = int(first_dict[name].lstrip().split("kB")[0])
    if second_dict[name].lstrip().split("kB")[0].rstrip().isdigit():
        second_value = int(second_dict[name].lstrip().split("kB")[0])
    overusage = 0
    if "kB" in values[name]:
        first_threshold = second_threshold = int(values[name].lstrip().split("kB")[0])
    if "%" in values[name]:
        if "MemTotal" in first_dict:
            mem_total = 0
            if first_dict["MemTotal"].lstrip().split("kB")[0].rstrip().isdigit():
                mem_total = int(first_dict["MemTotal"].lstrip().split("kB")[0])
            first_threshold = (
                mem_total
                * float(values[name].lstrip().split("%")[0])
                / 100.0
            )
        if "MemTotal" in second_dict:
            mem_total = 0
            if second_dict["MemTotal"].lstrip().split("kB")[0].rstrip().isdigit():
                mem_total = int(second_dict["MemTotal"].lstrip().split("kB")[0])
            second_threshold = (
                mem_total
                * float(values[name].lstrip().split("%")[0])
                / 100.0
            )

    if first_value > first_threshold:
        overusage = overusage | 1

    if second_value > second_threshold:
        overusage = overusage | 2
    return overusage


def combine_dict(combined_ordered_dict, first_dict, second_dict):
    """
    Get a unique list of names and add to combined dict.
    Combined changed from set to dict to preserve order of insertion.
    """
    combined_ordered_dict.clear()
    for name in first_dict:
        combined_ordered_dict[name] = 0
    for name in second_dict:
        combined_ordered_dict[name] = 0


@register
def compare_meminfo(dir1, dir2, args):
    """
    Diffs the contents of files named "/proc/meminfo" in the given directories.
    Abort if major differences exist.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.

    Raises:
        OSError: If either "/proc/meminfo" file is not found.
    """
    detail_flag = args.detail
    first_dict = {}
    second_dict = {}
    combined_ordered_dict = {
        "MemTotal": 0,
        "MemFree": 0,
        "SwapTotal": 0,
        "SwapFree": 0,
        "Slab": 0,
        "Percpu": 0,
        "HugePages_Total": 0,
        "HugePages_Free": 0,
    }
    threshold_values = {}
    if gather_mem_values(dir1, first_dict):
        return 1

    if gather_mem_values(dir2, second_dict):
        return 1

    load_thresholds(threshold_values)

    if detail_flag:
        combine_dict(combined_ordered_dict, first_dict, second_dict)

    table = Table(["", "Name:>", "First Report:>", "Second Report:>", "Diff:>"])

    for name in combined_ordered_dict:
        first_value=0
        second_value=0
        value_diff=0
        overusage=0

        if name not in first_dict:
            first_dict[name] = "MISSING"
        else:
            if first_dict[name].lstrip().split("kB")[0].rstrip().isdigit():
                first_value = int(first_dict[name].lstrip().split("kB")[0])

        if name not in second_dict:
            second_dict[name] = "MISSING"
        else:
            if second_dict[name].lstrip().split("kB")[0].rstrip().isdigit():
                second_value = int(second_dict[name].lstrip().split("kB")[0])

        if name in threshold_values:
            overusage = eval_threshold(
                name,
                threshold_values,
                first_dict,
                second_dict,
            )

        value_diff = second_value - first_value

        if first_dict[name] != second_dict[name]:
            first, second = compare_strings(first_dict[name], second_dict[name])
            if overusage & 1:
                first = first + bold(" > " + threshold_values[name])
            if overusage & 2:
                second = second + bold(" > " + threshold_values[name])

            table.row(">", name, first, second,str(value_diff)+" kB")
        else:
            if detail_flag:
                table.row(" ", name, first_dict[name], second_dict[name], str(value_diff)+" kB")

    if table.rows:
        #
        # Print the module header.
        #
        print("\n\nMeminfo Comparison" + "_" * 63)

        #
        # Print the data.
        #
        table.write()
        return 0

    print("INFO: No differences found in meminfo comparison.")
    return 0
