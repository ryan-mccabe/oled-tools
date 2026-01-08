"""
    Name: cmdline.py
    Purpose: Compare kernel command line arguments.
    Author: Pablo Prado <pablo.prado@oracle.com>
"""
import string
from .plugin import register
from .utils import compare_strings, Table, perror

# --------------------------------------------------
def gather_cmdline(directory_path, result_dict):
    """
    Reads the kernel command line from /proc/cmdline and populates the given
    dictionary (result_dict) with discovered parameters.

    - Each token with '=' is treated as key=value.
    - Each token without '=' is treated as a standalone flag, e.g. 'quiet' => {'quiet': ['yes']}.
    """
    file_path = "proc/cmdline"
    try:
        with open(directory_path + file_path, "r", encoding="utf-8") as file_handle:
            line = file_handle.read().strip()
            if not line:
                return 0

            tokens = line.split()

            for token in tokens:
                if '=' in token:
                    key, val = token.split('=', 1)
                    if key not in result_dict:
                        result_dict[key] = []
                    result_dict[key].append(val)
                else:
                    # For standalone flags
                    if token not in result_dict:
                        result_dict[token] = []
                    result_dict[token].append("YES")

    except OSError as error:
        perror(error, "open")
        return 1

    return 0

# --------------------------------------------------
@register
def compare_cmdline(first_dir, second_dir, args):
    """
    Compare the kernel command lines from two different sos_reports.
    """
    detail = args.detail

    first_dict = {}
    second_dict = {}

    if gather_cmdline(first_dir, first_dict):
        return 1
    if gather_cmdline(second_dir, second_dict):
        return 1

    table = Table(["Name", "First Report", "Second Report"])
    differences_found = False

    all_keys = set(first_dict.keys()).union(second_dict.keys())

    for key in sorted(all_keys):
        first_vals = first_dict.get(key, [])
        second_vals = second_dict.get(key, [])

        # Compare them index-by-index. If lengths differ,
        # mark missing items in the shorter side as "MISSING".
        max_len = max(len(first_vals), len(second_vals))
        for i in range(max_len):
            f_val = first_vals[i] if i < len(first_vals) else "MISSING"
            s_val = second_vals[i] if i < len(second_vals) else "MISSING"

            if f_val != s_val:
                differences_found = True
                f_comp, s_comp = compare_strings(f_val, s_val)
                table.row(f"> {key}", f_comp, s_comp)
            else:
                if detail:
                    table.row(key, f_val, s_val)

    if differences_found or detail:
        print("\n\nKernel Command Line Comparison" + "_" * 64)
        table.write()
    else:
        print("INFO: No differences found in Kernel Command Line comparison.")

    return 0
