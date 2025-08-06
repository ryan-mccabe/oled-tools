"""
    Name: kernel_messages.py
    Purpose: Compare messages from dmesg
    Author: Luis Gomez <luis.en.gomez@oracle.com>
"""

from .plugin import register
from .utils import Table, perror

def gather_kernel_histogram(directory_path, results, detail_flag):
    """ Function to generate Kernel messages histogram from /sos_commands/kernel/dmesg """
    file_path = "sos_commands/kernel/dmesg"
    try:
        with open(directory_path + file_path, "r", encoding="utf-8") as file_handle:
            for line in file_handle:
                if "] " not in line:
                    continue
                key = line.split("] ")[1]
                if ": " in key:
                    inc_value = 1
                    if " callbacks suppressed" in key:
                        callbacks = key.split(": ")[1].split(" callbacks suppressed")[0]
                        callbacks = callbacks.lstrip().rstrip()
                        if callbacks.isdigit():
                            inc_value = int(callbacks)

                    key = key.split(": ")[0]
                    if "[" in key and not detail_flag:
                        key = key.split("[")[0] + "[...]"

                    if len(key) > 50:
                        key = key[:50] + "..."

                    if key in results:
                        results[key] = results[key]+inc_value
                    else:
                        results[key] = inc_value

    except OSError as error:
        perror(error, "open")
        return 1

    return 0

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
def compare_kernel_messages(dir1, dir2, args):
    """
    Diffs the contents of dmesg output in the given directories.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.

    Raises:
        OSError: If either "sos_commands/kernel/dmesg" file is not found.
    """
    detail_flag = args.detail
    first_dict = {}
    second_dict = {}
    combined_ordered_dict = {}

    if gather_kernel_histogram(dir1, first_dict, detail_flag):
        return 1

    if gather_kernel_histogram(dir2, second_dict, detail_flag):
        return 1

    combine_dict(combined_ordered_dict, first_dict, second_dict)

    table = Table(["", "Element:>", "First Report:>", "Second Report:>", "Diff:>"])

    for name in combined_ordered_dict:

        if name not in first_dict:
            first_dict[name] = 0

        if name not in second_dict:
            second_dict[name] = 0

        value_diff = second_dict[name] - first_dict[name]

        if first_dict[name] != second_dict[name]:
            table.row(">", name, first_dict[name], second_dict[name],str(value_diff))
        else:
            if detail_flag:
                table.row(" ", name, first_dict[name], second_dict[name], str(value_diff))

    if table.rows:
        #
        # Print the module header.
        #
        print("\n\nKernel Messages Comparison" + "_" * 63)

        #
        # Print the data.
        #
        table.write()
        return 0

    print("INFO: No differences found in Kernel messages comparison.")
    return 0
