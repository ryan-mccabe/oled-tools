#!/usr/bin/python3
#
# Copyright (c) 2025, Oracle and/or its affiliates.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
#
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
#
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, see https://www.gnu.org/licenses/.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.

# Author: Partha Satapathy partha.satapathy@oracle.com

"""
Module providing a function to profile workload.
"""


import argparse
import os
import subprocess
import signal
import sys
import platform
import re
import fcntl
from typing import List, Optional, Tuple, Any, TextIO
from datetime import datetime

# version
VERSION = "oled_profile_0_1.2"

# profile_0_1.0
#
# Add base code for profile kernel and application profiler
# Add workload  kern_cpuhp
# Add workload libvirt_cpuhp
# Add workalod qemu_cpuhp
# Add -d as debug mode
#

# profile_0_1.1
#
# Version details and Add -v for version
# Add -L --list to list available workloads
# Add -e --expand with  -l to list functions in the workload
# Add -f --file to provide a file as a function list
# Add -o --output file for logging
# Add -v --version display profile version number
# Add -R, --runs Display currently running traces.
# Add -T --terminat Terminates the sepcified profiling.
# Add timeout to function list and stop tracing on timeout
# Add default loging to /var/oled/profile
# Add a README with example
#

# pylint: disable=broad-exception-caught

KERN_DTFILE_NAME = "dt_trace_kern.d"
DTPATH = "/var/oled/profile/dtscripts/"
DTLOGPATH = "/var/oled/profile/dtlog/"
OLPROF_PATH = "/var/oled/profile/"
OLPROF_RUNS = "/var/oled/profile/profile.run"
INSTPATH = "/usr/libexec/oled-tools/workloads/"
DTPID = 0
MAJOR = 0
MINOR = 0

DATE = datetime.now()
TIME = DATE.strftime("%Y-%m-%d_%H-%M-%S")

DBGFILE = OLPROF_PATH+TIME+"_profile.dbg"

kern_workload_list = [
    'kern_cpuhp'
]

proc_workload_list = [
    'libvirt_cpuhp',
    'qemu_cpuhp'
]

workload: List[str] = []


def get_workload(wlname: str) -> list:
    """
    Get the workload name
    """
    if wlname == "kern_cpuhp":
        return workload

    if wlname == "libvirt_cpuhp":
        return workload

    if wlname == "qemu_cpuhp":
        return workload

    if wlname == "user_workload":
        return workload

    return []


def chk_kern_workload(wlname: str) -> Optional[str]:
    """
    Check the worklaod is a kernel workload.
    """
    if wlname in kern_workload_list:
        return "kern_workload"
    return None


def chk_proc_workload(wlname: str) -> Optional[str]:
    """
    Check the workload is a user peorcess workload.
    """
    if wlname in proc_workload_list:
        return "proc_workload"
    return None


def chk_workload(wlname: str) -> Optional[str]:
    """
    Check the workload is valid.
    """
    if wlname in kern_workload_list:
        return wlname

    if wlname in proc_workload_list:
        return wlname

    return None


def print_workload() -> None:
    """
    Print the available workloads.
    """
    print("")
    print("Kernel workloads:")
    for wll in kern_workload_list:
        print(wll)
    print("")
    print("User workloads:")
    for wll in proc_workload_list:
        print(wll)


def expand_workload(wll: str) -> None:
    """
    Print the available workloads.
    """
    wll_fn_list = get_workload(wll)

    print("Functions in : ", wll)
    for wll_fn in wll_fn_list:
        print(wll_fn)
    print("")


def parse_args() -> argparse.Namespace:
    """
    Parse the CLI arguments
    """
    parser = argparse.ArgumentParser(
        prog='profile',
        description='Trace and profile workload events.')

    # -l and -f are mutually exclusive
    group1 = parser.add_mutually_exclusive_group(required=False)
    group1.add_argument(
        "-l",
        "--workload",
        help="Name of workload")

    group1.add_argument(
        "-f",
        "--workloadfile",
        help="Path to the file containing workload/function list")

    parser.add_argument(
        "-p",
        "--pid",
        help="pid to trace. Must be used with -l or -f")

    parser.add_argument(
        "-d",
        "--debug",
        action='store_true',
        help="Enable debug logging")

    parser.add_argument(
        "-v",
        "--version",
        action='store_true',
        help="Display oled profile version number")

    parser.add_argument(
        "-L",
        "--list",
        action='store_true',
        help="Display available workloads")

    parser.add_argument(
        "-R",
        "--runs",
        action='store_true',
        help="Display currently running traces.")

    parser.add_argument(
        "-T",
        "--terminate",
        help="Terminates the sepcified profiling.")

    parser.add_argument(
        "-e",
        "--expand",
        action='store_true',
        help="Display functions associated with a workload. "
             "Must be used with -l")

    # -P and -o are mutually exclusive
    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument(
        "-o",
        "--outfile",
        help="Output will be redirected to the file specified by OUTFILE.")

    group2.add_argument(
        "-P",
        "--print",
        action='store_true',
        help="Display output on console")

    args = parser.parse_args()

    if not len(sys.argv) - 1:
        print("Workload need to be specified for profile")
        parser.print_help()
        exit_with_msg("", 2)

    other_options = (args.workload or args.pid or args.workloadfile or
                     args.outfile or args.print)
    if args.version and other_options:
        parser.error("-v (--version) cannot be used with other options")

    if args.list and other_options:
        parser.error("-L (--list) cannot be used with other options")

    # Ensure that -v, -L, and -e are not used together
    if args.version and (args.list or args.expand):
        parser.error("-v (--version) cannot be used with -L (--list)"
                     "or -e (--expand)")

    if args.list and args.expand:
        parser.error("-L (--list) cannot be used with -e (--expand)"
                     "or -v (--version)")

    # Ensure -e goes only with -l
    if args.expand and not args.workload:
        parser.error("-e (--expand) must be used with -l (--workload)")

    # Ensure -p only goes with -l or -f
    if args.pid and not (args.workload or args.workloadfile):
        parser.error("-p (--pid) must be used with -l (--workload)"
                     "or -f (--workloadfile)")

    return args


def init_dtpath(dpath: str) -> None:
    """
    Create the directory required to store the trace scripts.
    """
    msg = "Check and create dtrace path : " + dpath
    dbg(msg)
    try:
        os.makedirs(dpath)
    except FileExistsError:
        return
    except PermissionError:
        msg = "Permission denied: Unable to create '{dpath}'."
        exit_with_msg(msg, 1)


def cleanup_trace() -> None:
    """
    Clean up the trace scripts post execution.
    In debug mode we will retain the scripts.
    """
    dpath = DTPATH

    for root, dirs, files in os.walk(dpath):
        for dtfiles in files:
            msg = "\nRemoving : " + os.path.join(root, dtfiles)
            dbg(msg)
            try:
                os.unlink(os.path.join(root, dtfiles))
            except OSError:
                print("Error deleting file.")

        for gdir in dirs:
            msg = "Garbage directories : " + gdir
            dbg(msg)


def exit_with_msg(msg: str = "", error: int = 1) -> None:
    """"
    Error out when something undesired happens
    """
    print(msg)
    sys.exit(error)


def mk_dtrace_list(pid: int = 0) -> List[str]:
    """
    Create the list of traceable functions
    """

    if pid is None:
        pid = 0

    if int(pid) == 0:
        try:
            dtl_op = subprocess.run(
                            ["dtrace", "-l"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)

        except subprocess.SubprocessError:
            msg = "dtrace -l Error.."
            exit_with_msg(msg, 1)

    if int(pid) > 0:
        param = "pid"+str(pid)+":::entry"
        try:
            dtl_op = subprocess.run(
                            ["dtrace", "-ln", param],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
            if dtl_op.returncode != 0:
                msg = "dtrace -l Error : " + dtl_op.stdout.decode()
                dbg(msg)
                exit_with_msg("Error executing dtrace -l.")

        except subprocess.SubprocessError:
            msg = "dtrace -ln " + param + " Error."
            exit_with_msg(msg, 1)

    dtl_out = dtl_op.stdout.decode().strip().splitlines()
    return dtl_out


DT_HDR = "#!/usr/sbin/dtrace -s \n"


DT_PRAGMA = """

#pragma D option destructive

#pragma D option quiet

"""

DT_BEGIN = """

BEGIN
{
"""


DT_TXT_END = "}"


DT_TXT_ENT = """

pid__PID__:__LIB__:__FUNC__:entry
{
"""


DT_TXT_RET = """

pid__PID__::__FUNC__:return
"""

DT_TXT_START = """
{
"""


KERN_DT_PRINT_ENT = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Entry.\",
        walltimestamp, timestamp, pid, execname, curthread->cpu, probefunc);
"""


KERN_DT_PRINT_ENT_GT_UEK8 = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Entry.\",
        walltimestamp, timestamp, pid, execname, curthread->thread_info.cpu,
        probefunc);
"""


KERN_DT_PRINT_RET = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Return.\",
        walltimestamp, timestamp, pid, execname, curthread->cpu, probefunc);
"""


KERN_DT_PRINT_RET_GT_UEK8 = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Return.\",
        walltimestamp, timestamp, pid, execname, curthread->thread_info.cpu,
        probefunc);
"""


PROC_DT_PRINT_ENT = """
    printf("\\n[%Y] %s Entry.", walltimestamp, probefunc);
"""


PROC_DT_PRINT = """
    printf("\\n[%Y] %s Return TimeToComplete %llu ns.",
        walltimestamp, probefunc, delta);
"""

PROC_DT_PRINT_VIRDOMAINSETVCPU = """
    printf("\\nHPDBG_TRACE:%s  cpu:%s, cpu_hp_op:%d",
        probefunc, stringof(arg1), arg2);
"""


PROC_DT_PRINT_VIRDOMAINSETVCPUS = """
    printf("\\nHPDBG_TRACE:%s  cpus:%d", probefunc, arg1);
"""


def check_kern_version_gt(uek: int) -> bool:
    """
    Check if the kernel is equal to or higher than the uek version provided.
    """
    uek_to_kern = {5: [4, 14], 6: [5, 4], 7: [5, 15], 8: [6, 12]}

    if MAJOR >= uek_to_kern[uek][0] and MINOR >= uek_to_kern[uek][1]:
        return True
    return False


def generate_param_list(param_list: List) -> str:
    """
    This accepts a list of [type, var] values and returns in
    dtrace printf format
    """
    type_to_format = {
        'unsigned int': '%u',
        'int': '%d',
        'long int': '%ld',
        'float': '%f',
        'str': '%s'
    }

    args = []
    for idx, param in enumerate(param_list):
        if param:
            param_type = param[0]
            param_name = param[1]

            # Get format specifier based on the dictionary above,
            # the default is string
            format_specifier = type_to_format.get(param_type, '%s')
            args.append(f"{param_name} = {format_specifier}")

    printf_statement = "    printf(\"\\nParameter list: " +\
                       ", ".join(args) + "\""

    for idx in range(len(param_list)):
        if not param_list[idx]:
            continue
        if param_list[idx][0] == "str":
            arg = f"stringof(arg{idx + 0})"
        else:
            arg = f"arg{idx + 0}"
        printf_statement += ", " + arg

    printf_statement += ");\n"

    return printf_statement


def mk_kern_trace_entry(dtfile: TextIO, this_fn: str,
                        timeout: int, param_list: List,
                        provider: str) -> None:
    """
    Write kernel trace entry.
    """
    dt_kern_pid = DT_TXT_ENT.replace("pid__PID__", provider)
    dt_kern_lib = dt_kern_pid.replace("__LIB__", "")
    dt_kern = dt_kern_lib.replace("__FUNC__", this_fn)
    dtfile.write(dt_kern)

    if timeout:
        msg = "Creating kernel entry :" + this_fn + ", timeout " + str(timeout)
        dbg(msg)

    if timeout:
        timevar = "    gvar_"+this_fn+"_ent = timestamp;\n"
        dtfile.write(timevar)

    if check_kern_version_gt(8):
        dtfile.write(KERN_DT_PRINT_ENT_GT_UEK8)
    else:
        dtfile.write(KERN_DT_PRINT_ENT)
    if param_list:
        dtfile.write(generate_param_list(param_list))
    dtfile.write(DT_TXT_END)


def generate_ret_print(ret: List) -> str:
    """
    This accepts a [type, var] values and returns in
    dtrace return value printf format
    """
    type_to_format = {
        'unsigned int': '%u',
        'int': '%d',
        'long int': '%ld',
        'float': '%f',
        'str': '%s'
    }

    printf_statement = "    printf(\"\\nReturn value for %s: "
    param_type = ret[0]
    param_name = ret[1]

    if param_type == "str":
        arg1 = "stringof(arg1)"
    else:
        arg1 = "arg1"

    # Get format specifier based on the dictionary above,
    # the default is string
    format_specifier = type_to_format.get(param_type, '%s')
    printf_statement += f"{param_name} = {format_specifier}\", "\
                        f"probefunc, {arg1});\n"

    return printf_statement


def mk_kern_trace_exit(dtfile: TextIO, this_fn: str,
                       timeout, ret, provider) -> None:
    """
    Write kernel trace exit.
    """
    dt_kern_pid = DT_TXT_RET.replace("pid__PID__", provider)
    dt_kern_lib = dt_kern_pid.replace("__LIB__", "")
    dt_kern = dt_kern_lib.replace("__FUNC__", this_fn)
    dtfile.write(dt_kern)

    if timeout:
        msg = "Creating kernel exit :" + this_fn + ", timeout " + str(timeout)
        dbg(msg)

    if timeout:
        timevar = f"/ (timestamp - gvar_{this_fn}_ent)/1000000 > " \
                  f"gvar_{this_fn}_to /"
        dtfile.write(timevar)

    dtfile.write(DT_TXT_START)
    if check_kern_version_gt(8):
        dtfile.write(KERN_DT_PRINT_RET_GT_UEK8)
    else:
        dtfile.write(KERN_DT_PRINT_RET)

    if ret:
        dtfile.write(generate_ret_print(ret))

    if timeout:

        exit_txt = f"    printf(\"\\n{this_fn}: " \
                   "Exit on timeout  %llu ms. \\n \", "
        dtfile.write(exit_txt)
        exit_txt = "\n            gvar_"+this_fn+"_to);"
        dtfile.write(exit_txt)

        timevar = "\n    exit(1);\n"
        dtfile.write(timevar)

    dtfile.write(DT_TXT_END)


def parse_function(input_str: str) -> Optional[Tuple[Any, ...]]:
    """
    Regex pattern to match the function components (return type,
    function name, parameters)
    This function returns a tuple of the above components after
    processing them.
    """
    pattern = r"^(?P<return_type>\([^\)]+\)\s+)?(?P<function_name>\w+)" \
              r"(\s*\((?P<params>.*?)\))?$"
    match = re.match(pattern, input_str.strip())

    if not match:
        if input_str.strip() == input_str.split()[0]:
            return [], input_str.strip(), []
        return None

    return_type = match.group('return_type')
    function_name = match.group('function_name')
    params_str = match.group('params')

    if return_type:
        return_type = return_type.strip("()").split()
        if len(return_type) == 2 and return_type[1].endswith(')'):
            return_type[1] = return_type[1][:-1]
    else:
        return_type = []

    params = []
    if params_str:
        params = [param.strip() for param in params_str.split(',')]

    parsed_params = []
    for param in params:
        if param:
            var = param.split()[-1]
            parsed_params.append([param[:-len(var)].strip(), var])
        else:
            parsed_params.append([])

    return return_type, function_name, parsed_params


def mk_kern_dt_fn(dtfile: TextIO, fnlist: list, dtl_out) -> None:
    """
    Process the function names obtained and create entry and
    return dtrace entries for those functions
    """

    mk_kern_gvars(dtfile, fnlist)

    dbg("Processing function names:\n")
    for fnnames in fnlist:
        fn_name = fnnames.strip()
        if not fn_name:
            continue
        if "::" in fn_name:
            this_fn = fn_name.split("::")[0]
            timeout = fn_name.split("::")[1]
        else:
            this_fn = fn_name.strip()
            timeout = None

        trace_entry = False
        trace_return = False

        result = parse_function(this_fn)
        if not result:
            continue
        ret, func_name, param_list = result
        dbg(f"Function = {func_name}, Return = {ret}, "
            f"Parameters = {param_list}")

        provider = ""
        p_idx = dtl_out[0].split().index("PROVIDER")
        for dtl in dtl_out:
            fnentry = " "+func_name+" "
            if fnentry in dtl and " entry" in dtl:
                trace_entry = True
                provider = dtl.split()[p_idx]
                dbg(dtl)

            if fnentry in dtl and " return" in dtl:
                trace_return = True
                dbg(dtl)

        if not validate_function_name(func_name):
            dbg(f"Invalid function name: {func_name}, skipping it")
            continue

        if provider == "rawfbt":
            provider = "fbt"
        if trace_entry:
            mk_kern_trace_entry(dtfile, func_name, timeout,
                                param_list, provider)

        if trace_return:
            mk_kern_trace_exit(dtfile, func_name, timeout, ret, provider)


def parse_function_name(input_str: str) -> Optional[str]:
    """
    Regex pattern to match the function name.
    This function returns only the function name.
    """
    pattern = r"(?:\([^\)]+\)\s+)?(?P<function_name>\w+)"
    match = re.match(pattern, input_str.strip())

    if not match:
        return None

    function_name = match.group('function_name')

    return function_name


def mk_kern_gvars(dtfile: TextIO, fnlist: list) -> None:
    """
    Create global variables in the dtrace file
    """
    exit_fn_list = []
    exit_fn_vars = []

    for fnnames in fnlist:
        fn_name = fnnames.strip()
        if fn_name:
            if "::" in fn_name:
                this_fn = fn_name.split("::")[0]
                fn_time = fn_name.split("::")[1]
                if fn_time:
                    func_name = parse_function_name(this_fn)
                    if not func_name:
                        continue
                    gvar = "uint64_t gvar_"+func_name+"_ent;\n"
                    dtfile.write(gvar)
                    gvarto = "uint64_t gvar_"+func_name+"_to;\n"
                    dtfile.write(gvarto)

                    gvar_int = "    gvar_"+func_name+"_ent = 0;\n"
                    exit_fn_vars.append(gvar_int)
                    gvarto_int = "    gvar_"+func_name+"_to = "+fn_time+";\n"
                    exit_fn_vars.append(gvarto_int)

                    exit_fn_list.append(func_name)

    if exit_fn_list:
        dtfile.write("uint64_t delta;\n")
        dtfile.write(DT_BEGIN)

        for init_fn in exit_fn_vars:
            dtfile.write(init_fn)

        dtfile.write("    delta = 0;\n")
        dtfile.write(DT_TXT_END)


def mk_kern_fn_and_exit(dtfile: TextIO, fnlist: list) -> None:
    """
    Create dtrace list and call mk_kern_st_fn to
    create the dtrace script
    """
    dtl_out = mk_dtrace_list()
    mk_kern_dt_fn(dtfile, fnlist, dtl_out)


def kern_create_dt(fnlist: list, wl_name: str) -> str:
    """
    Create the dtrace script for kernel.
    """
    dbg("Start creating dt file.")

    if fnlist:
        dtfile_name = TIME+"_"+wl_name+".d"
        dtfile_path = DTPATH+dtfile_name

        try:
            with open(dtfile_path, "a", encoding="utf-8") as dtfile:
                dbg("File open : " + dtfile_path)

                dtfile.truncate(0)
                dtfile.write(DT_HDR)
                dtfile.write(DT_PRAGMA)

                mk_kern_fn_and_exit(dtfile, fnlist)

                dtfile.close()
                dbg("File close : " + dtfile_path)
                os.chmod(dtfile_path, 0o777)

        except OSError:
            msg = "File open error : " + str(dtfile_path)
            exit_with_msg(msg, 2)

    return dtfile_name


def write_proc_dt_entry(dtfile: TextIO, pid: int, this_fn: str,
                        param_list: List) -> None:
    """
    write process entry dtrace.
    """

    dt_lib = DT_TXT_ENT.replace("__LIB__", "")
    dt_pid = dt_lib.replace("__PID__", str(pid))
    dt_buff = dt_pid.replace("__FUNC__", this_fn)
    dtfile.write(dt_buff)

    timevar = "    gvar_"+this_fn+"_ent = timestamp;\n"
    dtfile.write(timevar)

    if this_fn == "virDomainSetVcpu":
        dtfile.write(PROC_DT_PRINT_VIRDOMAINSETVCPU)

    if this_fn == "virDomainSetVcpus":
        dtfile.write(PROC_DT_PRINT_VIRDOMAINSETVCPUS)

    dtfile.write(PROC_DT_PRINT_ENT)
    if param_list:
        dtfile.write(generate_param_list(param_list))
    dtfile.write(DT_TXT_END)


def write_proc_dt_return(dtfile: TextIO, pid: int, this_fn: str,
                         ret: List) -> None:
    """
    write process return dtrace.
    """

    dt_lib = DT_TXT_RET.replace("__LIB__", "")
    dt_pid = dt_lib.replace("__PID__", str(pid))
    dt_buff = dt_pid.replace("__FUNC__", this_fn)
    dtfile.write(dt_buff)
    dtfile.write(DT_TXT_START)

    timevar = "    delta = timestamp - gvar_"+this_fn+"_ent;\n"
    dtfile.write(timevar)
    dtfile.write(PROC_DT_PRINT)
    if ret:
        dtfile.write(generate_ret_print(ret))
    timevar = "    delta = 0;\n"
    dtfile.write(timevar)

    dtfile.write(DT_TXT_END)


def write_proc_dt_exit(dtfile: TextIO, pid: int, this_fn: str,
                       timeout: int) -> None:
    """
    Write process exit dtrace.
    """

    dt_lib = DT_TXT_RET.replace("__LIB__", "")
    dt_pid = dt_lib.replace("__PID__", str(pid))
    dt_buff = dt_pid.replace("__FUNC__", this_fn)
    dtfile.write(dt_buff)

    if timeout:
        msg = "Creating exit function " + this_fn + ", timeout " + str(timeout)
        dbg(msg)

    dt_exit_cond = "/ (timestamp - gvar_"+this_fn+"_ent)/1000000 > gvar_" \
                   + this_fn + "_to /"
    dtfile.write(dt_exit_cond)

    dtfile.write(DT_TXT_START)

    exit_txt = f"    printf(\"\\n{this_fn}: " \
               "Exit on timeout  %llu ms. \\n \", "
    dtfile.write(exit_txt)
    exit_txt = "\n            gvar_"+this_fn+"_to);"
    dtfile.write(exit_txt)

    timevar = "\n    exit(1);\n"
    dtfile.write(timevar)

    dtfile.write(DT_TXT_END)


def write_proc_dt(dtfile: TextIO, pid: int, this_fn: str,
                  param_list: List, ret: List, timeout: int) -> None:
    """
    write process dtrace file.
    """

    write_proc_dt_entry(dtfile, pid, this_fn, param_list)
    write_proc_dt_return(dtfile, pid, this_fn, ret)
    if timeout:
        write_proc_dt_exit(dtfile, pid, this_fn, timeout)


def mk_proc_gvars(dtfile: TextIO, processed_fnnames: list) -> None:
    """
    Create global variables in dtrace file for proc gvars
    """
    for fn_name, fn_time in processed_fnnames:
        fn_name = parse_function_name(fn_name)
        if fn_name:
            gvar = "uint64_t gvar_"+fn_name+"_ent;\n"
            dtfile.write(gvar)
            if fn_time:
                gvar = "uint64_t gvar_"+fn_name+"_to;\n"
                dtfile.write(gvar)

    dtfile.write("uint64_t delta;\n")
    dtfile.write(DT_BEGIN)

    for fn_name, fn_time in processed_fnnames:
        fn_name = parse_function_name(fn_name)
        if fn_name:
            gvar = "    gvar_"+fn_name+"_ent = 0;\n"
            dtfile.write(gvar)
            if fn_time:
                gvar = "    gvar_"+fn_name+"_to = "+fn_time+";\n"
                dtfile.write(gvar)

    dtfile.write("    delta = 0;\n")
    dtfile.write(DT_TXT_END)


def proc_create_dt(pid: int, fnlist: list, function_list: str) -> str:
    """
    Create the dtrace script for the process.
    """
    if pid == 0:
        return ""

    dtl_out = mk_dtrace_list(pid)
    msg = "Creating dt file for : "+function_list+"pid : " + str(pid)
    dbg(msg)

    if fnlist:
        proc_dtfile_name = TIME+"_profile_"+function_list+"_"+str(pid)+".d"
        dtfile_path = DTPATH+proc_dtfile_name
        dbg("Tracing script :", dtfile_path)

        try:
            with open(dtfile_path, "a", encoding="utf-8") as dtfile:
                dbg("File open " + dtfile_path)

                dtfile.truncate(0)
                dtfile.write(DT_HDR)
                dtfile.write(DT_PRAGMA)

                processed_fnnames = []
                for fnnames in fnlist:
                    fn_name = fn_time = None
                    fn_name = function = fnnames.strip()
                    if function and "::" in function:
                        fn_name = function.split("::")[0]
                        fn_time = function.split("::")[1]
                    processed_fnnames.append([fn_name, fn_time])

                mk_proc_gvars(dtfile, processed_fnnames)

                for this_fn, timeout in processed_fnnames:
                    result = parse_function(this_fn)
                    if not result:
                        continue
                    ret, func_name, param_list = result
                    dbg(f"Function = {func_name}, Return = {ret}, "
                        f"Parameters = {param_list}")

                    trace_fn = False

                    for dtl in dtl_out:
                        fnentry = " "+func_name+" "
                        if fnentry in dtl:
                            trace_fn = True
                            dbg(dtl)

                    if not validate_function_name(func_name):
                        dbg(f"Invalid function name: {func_name}, skipping it")
                        continue

                    if func_name and trace_fn:
                        write_proc_dt(dtfile, pid, func_name,
                                      param_list, ret, timeout)

                dtfile.close()
                dbg("File close : " + dtfile_path)
                os.chmod(dtfile_path, 0o777)

        except OSError:
            msg = "File open error : " + str(dtfile_path)
            exit_with_msg(msg, 2)

    return proc_dtfile_name


def validate_function_name(function_name: str) -> bool:
    """
    Function name must start with a letter or underscore,
    followed by letters, numbers, or underscores.
    """
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, function_name))


def clear_workload_list() -> None:
    """
    Clear workload list if user workload is specified
    """
    workload.clear()


def mk_workload_list(wlfile_path: str) -> None:
    """
    Access and process the workload file.
    """
    try:
        with open(wlfile_path, 'r', encoding='utf-8') as wlfile:
            lines = wlfile.readlines()
            for line in lines:
                function_name = line.strip()
                workload.append(function_name)
    except FileNotFoundError:
        print(f"Error: The file {wlfile_path} was not found.")
    except IOError as e:
        print(f"Error: An I/O error occurred. {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def mk_workload(function_list: str) -> None:
    """
    Prepare existing workload file to read.
    """
    wl_file_path = INSTPATH+function_list+".fnlist"
    mk_workload_list(wl_file_path)


def mk_user_workload(wl_file_path: str, pid: int) -> None:
    """
    Load the user workload file.
    """
    if pid:
        proc_workload_list.append("user_workload")
    else:
        kern_workload_list.append("user_workload")

    mk_workload_list(wl_file_path)


def get_cmdiline() -> str:
    """
    Get the command line args and return the command
    passed by the user.
    """

    cmdline = ''

    for arg in sys.argv[1:]:
        if ' ' in arg:
            cmdline += f'"{arg}"  '
        else:
            cmdline += f"{arg}  "

    return "oled profile " + cmdline


def runlist() -> None:
    """
    Display current running traces.
    """
    lcount = 0
    try:
        with open(OLPROF_RUNS, 'r+', encoding='utf-8') as runfile:
            fcntl.flock(runfile, fcntl.LOCK_SH)
            lines = runfile.readlines()
            lcount = len(lines)
            if lcount:
                msg = "Running profile trace are: "
                print(msg)
                for line in lines:
                    print(line)

            fcntl.flock(runfile, fcntl.LOCK_UN)
            runfile.close()

    except Exception:
        msg = "No runnig profile traces."
        print(msg)
        dbg(msg)
        return

    if lcount == 0:
        msg = "No runnig profile traces."
        print(msg)
        dbg(msg)

    return


def runlist_clean(_id: int) -> None:
    """
    Clear the trace from runlist OLPROF_RUNS file.
    """
    if _id is None:
        return

    idstr = "PID: "+str(_id)+","

    run_list: List[str] = []
    lcount = 0

    try:
        with open(OLPROF_RUNS, 'r+', encoding='utf-8') as runfile:
            fcntl.flock(runfile, fcntl.LOCK_SH)

            lines = runfile.readlines()
            lcount = len(lines)
            del_line = False

            if lcount:
                for line in lines:
                    run_list.append(line)

                for line in run_list[:]:
                    if idstr in line:
                        run_list.remove(line)
                        del_line = True
                        break

            if del_line:
                runfile.truncate(0)
                nlcount = len(run_list)
                if nlcount:
                    for line in run_list:
                        runfile.write(line)
            fcntl.flock(runfile, fcntl.LOCK_UN)
            runfile.close()

    except Exception:
        msg = "No runnig profile traces."
        print(msg)
        dbg(msg)
        return

    if lcount == 0:
        msg = "No runnig profile traces."
        print(msg)
        dbg(msg)

    return


def terminate_id(_id: str) -> None:
    """
    Terminate the specified profile.
    """
    if _id is None:
        return

    idstr = "PID: "+_id+","
    dokill = False

    try:
        with open(OLPROF_RUNS, 'r+', encoding='utf-8') as runfile:
            fcntl.flock(runfile, fcntl.LOCK_SH)
            lines = runfile.readlines()
            lcount = len(lines)
            if lcount:
                for line in lines:
                    if idstr in line:
                        dokill = True
            fcntl.flock(runfile, fcntl.LOCK_UN)
            runfile.close()

    except Exception:
        msg = "No runnig profile traces."
        print(msg)
        dbg(msg)
        return

    try:
        if dokill is True:
            os.kill(int(_id), 9)
            print("Workload PID: "+_id+" terminated")
        else:
            print("PID: "+_id+" is not a workload.")
    except Exception:
        print("Workload PID: "+_id+" Not running")


def run_dt(dtfile_name: str) -> None:
    """
    Execute the created dtrace script.
    """

    global DTPID
    args = parse_args()

    dtfile_path = DTPATH + dtfile_name
    msg = "Starting dtrace : " + dtfile_path
    dbg(msg)

    log_path = DTLOGPATH + dtfile_name + ".log"
    if args.outfile:
        log_path = args.outfile

    dbg(log_path)
    cmdline = get_cmdiline()

    uek_version = platform.uname().release
    time = DATE.strftime('%A, %B %d, %Y %H:%M:%S')

    try:
        with open(log_path, 'a', encoding='utf-8') as logfile:
            logfile.truncate(0)
            logfile.write(f"Kernel version: {uek_version}\n")
            logfile.write(f"Command: {cmdline}\n")
            logfile.write(f"Version: {VERSION}\n")
            logfile.write(f"oled profile start time: {time}\n")
            logfile.write(f"dtrace file: {dtfile_path}\n")

            logfile.close()
    except Exception:
        print("File open error : ", log_path)

    if args.print:
        param = dtfile_path
    else:
        param = dtfile_path + " -o " + log_path

    dbg(param)
    print("\nStarted tracing, output logs are being continuously "
          f"redirected to {log_path}\n"
          "Please monitor the file for real-time updates. "
          "Press Ctrl + C to stop the tool")

    pid = str(os.getpid())
    pid_entry = f"PID: {pid}, Time {TIME}, Command: {cmdline}"
    dbg(pid_entry)

    param_list = param.split(" ")

    try:
        dt_subproc = subprocess.Popen(param_list)
        DTPID = dt_subproc.pid
        msg = f"PID: {dt_subproc.pid}, Time {TIME}, Command: {cmdline} \n"

        try:
            with open(OLPROF_RUNS, 'a+', encoding='utf-8') as runfile:
                fcntl.flock(runfile, fcntl.LOCK_EX)
                runfile.write(msg)
                fcntl.flock(runfile, fcntl.LOCK_UN)
                runfile.close()

        except Exception:
            print("File open error pss : ", OLPROF_RUNS)
            with open(OLPROF_RUNS, 'a+', encoding='utf-8') as runfile:
                fcntl.flock(runfile, fcntl.LOCK_EX)
                runfile.write(msg)
                fcntl.flock(runfile, fcntl.LOCK_UN)
                runfile.close()
        try:
            with open(log_path, 'a', encoding='utf-8') as logfile:
                logfile.write(f"Waiting on dtrace pid: {DTPID}\n")
                logfile.write("Trace Logs: \n")
                logfile.close()
        except Exception:
            print("File open error : ", log_path)

        dt_subproc_ret = dt_subproc.wait()
        msg = f"PID: {dt_subproc.pid}, Time {TIME}, " \
              f"Command: {cmdline} Exit with code {dt_subproc_ret}"
        runlist_clean(DTPID)
        dbg("msg")

    except OSError:
        msg = "System Error : " + param
        exit_with_msg(msg)

    msg = "Stopping dtrace : " + dtfile_path
    dbg(msg)


def dbg(msg: str = "") -> None:
    """
    Print debug log.
    """
    args = parse_args()

    if args.debug:
        try:
            with open(DBGFILE, "a", encoding="utf-8") as dbgfile:
                dbgfile.write(f"{msg}\n")
                dbgfile.close()
        except Exception:
            print("File open error : ", DBGFILE)
            exit_with_msg("", 2)


def signal_handler(sig: int, _frame) -> None:
    """
    Handle sigint and execute necessary cleanup.
    """
    print("pid :" + str(DTPID) + " Exit on signal", str(sig))

    if DTPID:
        terminate_id(str(DTPID))
        runlist_clean(DTPID)

    cleanup_trace()
    sys.exit(sig)


def trace_proc(function_list: str, tpid: int) -> str:
    """
    Trace user process.
    """
    kwl_rc = chk_kern_workload(function_list)
    if kwl_rc:
        msg = "Kernel workload doesnot require pid."
        exit_with_msg(msg, 2)

    if tpid is None or tpid == 0:
        msg = "Creating dtrace for : " + function_list + " needs pid"
        exit_with_msg(msg, 2)

    msg = "Creating dtrace for pid : " + str(tpid)
    msg = msg + " and workload : "+function_list

    dbg(msg)
    mk_dtrace_list(tpid)

    wlname = get_workload(function_list)
    if not wlname:
        msg = "Invalid workload : " + function_list
        exit_with_msg(msg, 2)

    dtfile_name = proc_create_dt(tpid, wlname, function_list)
    msg = "Running dtrace for pid : "+str(tpid)
    msg = msg+" and workload : "+function_list
    dbg(msg)

    run_dt(dtfile_name)
    return dtfile_name


def trace_kern(function_list: str) -> str:
    """
    Trace kernel.
    """
    pwl_rc = chk_proc_workload(function_list)
    if pwl_rc:
        msg = function_list + " Workload requires pid."
        exit_with_msg(msg, 2)

    msg = "Creating dtrace for kernel, workload : "+function_list
    dbg(msg)
    mk_dtrace_list()

    wlname = get_workload(function_list)
    if not wlname:
        msg = "Invalid workload : " + function_list
        exit_with_msg(msg, 2)

    dtfile_name = kern_create_dt(wlname, function_list)
    msg = "Running dtrace for kernel, workload : "+function_list
    dbg(msg)

    run_dt(dtfile_name)
    return dtfile_name


def trace_dt(function_list: str, tpid: int = 0) -> str:
    """
    Process function_list
    """
    dtfile_name = ""
    kwl_rc = chk_kern_workload(function_list)
    pwl_rc = chk_proc_workload(function_list)
    if kwl_rc:
        dtfile_name = trace_kern(function_list)
    elif pwl_rc:
        dtfile_name = trace_proc(function_list, tpid)
    else:
        print("Error..........")

    return dtfile_name


# pylint: disable=too-many-branches, too-many-statements
def main() -> None:
    """
    oled profile genartes profiling scripts dynamically for a list of
    functions representing a workload and excutes the profiling script.
    The profiled data contains outputs of  entry and return traces of each
    function listed in workload list. If a function is not traceable,
    profile will skip it and continue to trace other functions.

    The oled profile command  mandates use of the `-l` option ponits to
    workload function list. The default workloads are available in the
    workload directory.

    The command oled profile with a pid as an argument, will trace the
    specified process, otherwise will trace the kernel.

    The command oled profile with -d option, excutes in debug mode.
    """
    global MAJOR, MINOR

    if os.geteuid() != 0:
        msg = "You need to have root privileges to run this script."
        exit_with_msg(msg)

    dtfile_path = ""
    function_list = ""

    args = parse_args()

    if args.version:
        print(f"\n{VERSION}\n")
        exit_with_msg("", 0)

    if args.debug:
        print("Debug mode enabled. "
              f"Check {DBGFILE} for debug logs.\n")

    kernel = platform.uname().release
    dbg(f"Kernel version: {kernel}")
    match = re.match(r"(\d+)\.(\d+)", kernel)
    if not match:
        raise ValueError(f"Could not parse kernel version: {kernel}")
    MAJOR = int(match.group(1))
    MINOR = int(match.group(2))

    if args.list:
        print("Available workloads are: ")
        print_workload()
        exit_with_msg("", 0)

    if args.runs:
        runlist()
        sys.exit(0)

    if args.terminate:
        _id = args.terminate
        if _id is None:
            print("We need a ID to terminate the profile")
            print("Please run oled profile -R to list running profiles")
        else:
            terminate_id(_id)

        sys.exit(0)

    init_dtpath(DTPATH)
    init_dtpath(DTLOGPATH)

    if args.workload:
        function_list = args.workload
        wl_rc = None
        wl_rc = chk_workload(function_list)
        if wl_rc:
            mk_workload(function_list)
            if args.expand:
                expand_workload(function_list)
                exit_with_msg("", 0)

        else:
            msg = "Workload "+function_list+" does not exist."
            print(msg)
            print("Available workloads are: ")
            print_workload()

            exit_with_msg("", 2)

    elif args.expand:
        msg = "Workload name is required to expand"
        print(msg)
        print("Available workloads are: ")
        print_workload()

        exit_with_msg("", 0)

    if args.workloadfile:
        function_list = "user_workload"
        clear_workload_list()

        if args.pid:
            mk_user_workload(args.workloadfile, args.pid)

        else:
            mk_user_workload(args.workloadfile, 0)

    msg = "Starting workload: "+function_list
    print(msg)
    trace_dt(function_list, args.pid)

    if args.debug and dtfile_path:
        cmd = "cat "+dtfile_path+" >> " + DBGFILE + "2>&1"
        os.system(cmd)
    cleanup_trace()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)
signal.signal(signal.SIGQUIT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    main()
