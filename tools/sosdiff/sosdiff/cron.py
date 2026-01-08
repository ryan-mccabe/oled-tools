"""
    Name: cron.py
    Purpose: Compare the values for cron tasks
    Author: Luis Gomez <luis.en.gomez@oracle.com>
"""

import os

from .plugin import register
from .utils import compare_multiline_strings
from .utils import Table, perror
from .utils import open_package_data


def load_cron_paths(paths, files):
    """Function to load cron paths from cron_paths.txt"""
    try:
        with open_package_data("cron_paths.txt", "r", encoding="utf-8") as file_handle:
            for line in file_handle:
                if not line.startswith("#"):
                    current_path = line.rstrip()
                    if current_path.endswith("/"):
                        paths.append(current_path)
                    else:
                        files.append(current_path)
    except OSError as error:
        perror(error, "open")


def gather_cron_jobs(directory_path, current_dict, paths, files):
    """Function to get values from specified cron files"""
    local_file_list = files.copy()

    for path in paths:
        try:
            if not os.path.isdir(directory_path + path):
                raise FileNotFoundError(
                    32,
                    "No such file or directory",
                    directory_path + path
                )
        except FileNotFoundError as error:
            perror(error, "open")
            return 1

        file_list = os.listdir(directory_path + path)
        for file in file_list:
            local_file_list.append(path + file)

    for file in local_file_list:
        try:
            with open(directory_path + file, "r", encoding="utf-8") as file_handle:
                file_content = ""
                for line in file_handle:
                    if not line.startswith("#"):
                        file_content = file_content + line
                current_dict[file] = file_content
        except OSError as error:
            perror(error, "open")
            return 1
    return 0


@register
def compare_cron(dir1, dir2, args):
    """
    Diffs the contents of cron files.
    Abort if major differences exist.

    Args:
        dir1: Path to the first directory.
        dir2: Path to the second directory.
    """
    detail_flag = args.detail
    first_dict = {}
    second_dict = {}
    paths = []
    files = []
    load_cron_paths(paths, files)

    if gather_cron_jobs(dir1, first_dict, paths, files):
        return 1

    if gather_cron_jobs(dir2, second_dict, paths, files):
        return 1
    combined_set = first_dict.keys() | second_dict.keys()
    table = Table(["", "File Name:<"])

    for name in sorted(combined_set):

        if name not in first_dict:
            first_dict[name] = "MISSING"

        if name not in second_dict:
            second_dict[name] = "MISSING"

        if first_dict[name] != second_dict[name]:
            first, second = compare_multiline_strings(first_dict[name], second_dict[name])
            table.row(" ", "File: " + name)
            table.row(" ", "First report:")
            table.row(" ", first)
            table.row(" ", "Second report:")
            table.row(" ", second)
            table.row(" ", "")

        else:
            if detail_flag:
                table.row(" ", "File: " + name)
                table.row(" ", "First report:")
                table.row(" ", first_dict[name])
                table.row(" ", "Second report:")
                table.row(" ", second_dict[name])

    if table.rows:
        #
        # Print the module header.
        #
        print("\n\nCron Files Comparison" + "_" * 63)

        #
        # Print the data.
        #
        table.write()
        return 0

    print("INFO: No differences found in cron comparison.")
    return 0
