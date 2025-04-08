#!/usr/libexec/platform-python
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
# 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.

# Author: Partha Satapathy <partha.satapathy@oracle.com>

"""
Module providing a function to profile workload.
"""

from typing import Optional

import argparse
import os
import subprocess
import signal
import sys
import typing

KERN_DTFILE_NAME = "dt_trace_kern.d"
DTPATH = "/tmp/dtscripts/"

kern_workload_list = [
    'kern_cpuhp'
]

proc_workload_list = [
    'libvirt_cpuhp',
    'qemu_cpuhp'
]

wl_kern_cpuhp = [
    'acpi_device_hotplug',
    'acpi_evaluate_ej0',
    'acpi_evaluate_ost',
    'acpi_hotplug_work_fn',
    'acpi_irq',
    'acpi_os_execute_defereed',
    'acpi_scan_is_offline',
    'acpi_soft_cpu_dead',
    'acpi_soft_cpu_online',
    'alloc_swap_slot_cache',
    'bio_cpu_dead',
    'blk_mq_hctx_notify_dead',
    'blk_mq_hctx_notify_offline',
    'blk_softirq_cpu_dead',
    'buffer_exit_cpu_dead',
    'cacheinfo_cpu_pre_down',
    'common_cpu_die',
    'console_cpu_notify',
    '_cpu_down',
    'cpu_down',
    'cpuhp_invoke_callback',
    '__cpuhp_kick_ap',
    'cpuhp_kick_ap',
    'cpuhp_kick_ap_work',
    'cpuhp_should_run',
    'cpuhp_thread_fun',
    'cpuid_device_destroy',
    'cpuset_hotplug_workfn',
    'cpuset_wait_for_hotplug',
    'cpuset_wait_for_hotplug',
    'crash_cpuhp_offline',
    'css_rightmost_descendant',
    'dev_cpu_dead',
    'finish_cpu',
    'fixed_percpu_data',
    'free_slot_cache',
    'free_vm_stack_cache',
    'haltpoll_cpu_offline',
    'haltpoll_cpu_online',
    'hrtimers_dead_cpu',
    'hwlat_cpu_die',
    'hwlat_cpu_init',
    'intel_iommu_cpu_dead',
    'iova_cpuhp_dead',
    'io_wq_cpu_offline',
    'irq_poll_cpu_dead',
    'itmt_legacy_cpu_online',
    'ixed_percpu_data',
    'KsCPUHPOffline',
    'KsCPUHPOnline',
    'kvmclock_cpu_down_prep',
    'kvmclock_cpu_online',
    'kvm_cpu_down_prepare',
    'kvm_dying_cpu',
    'lockup_detector_cleanup',
    'lockup_detector_cleanup',
    'lockup_detector_offline_cpu',
    'mce_cpu_dead',
    'mce_cpu_online',
    'mce_cpu_pre_down',
    'memcg_hotplug_cpu_dead',
    'migration_offline_cpu',
    'migration_online_cpu',
    'msr_device_destroy',
    'native_cpu_die',
    'osnoise_cpu_die',
    'osnoise_cpu_init',
    'padata_cpu_dead',
    'page_alloc_cpu_dead',
    'page_writeback_cpu_online',
    'percpu_counter_cpu_dead',
    'perf_event_exit_cpu',
    'radix_tree_cpu_dead',
    'rapl_cpu_offline',
    'rcutree_dead_cpu',
    'rcutree_dying_cpu',
    'rcutree_offline_cpu',
    'rebuild_sched_domains',
    'rebuild_sched_domains_locked',
    'sched_cpu_activate',
    'sched_cpu_deactivate',
    'sched_cpu_dying',
    'sched_cpu_wait_empty',
    'slub_cpu_dead',
    'smpboot_park_threads',
    'smpcfd_dead_cpu',
    'smpcfd_dying_cpu',
    'takedown_cpu',
    'takeover_tasklets',
    'timers_dead_cpu',
    'topology_remove_dev',
    'virtnet_cpu_dead',
    'virtnet_cpu_down_prep',
    'virtnet_cpu_online',
    'vmstat_cpu_dead',
    'vmstat_cpu_down_prep',
    'workqueue_offline_cpu',
    'x86_pmu_dead_cpu',
    'x86_pmu_dying_cpu',
    'xfs_cpu_dead',
    'zs_cpu_dead',
    'zswap_cpu_comp_dead',
    'zswap_dstmem_dead'
]

wl_libvirt_cpuhp = [
    'qemuDomainSetVcpuInternal',
    'qemuDomainSetVcpusInternal',
    'virDomainSetVcpu',
    'virDomainSetVcpus',
    'virDomainCgroupEmulatorAllNodesAllow',
    'virNumaGetHostMemoryNodeset',
    'qemuMonitorDelDevice',
    'qemuDomainVcpuPersistOrder',
    'virDomainObjWaitUntil',
    'qemuDomainRemoveVcpuAlias',
    'qemuDomainRemoveDevice',
    'qemuDomainRefreshVcpuInfo',
    'qemuMonitorJSONIOProcessLine',
    'qemuMonitorIOWriteWithFD'
]

wl_qemu_cpuhp = [
    'acpi_update_sci',
    'qdev_unplug',
    'legacy_acpi_cpu_plug_cb',
    'acpi_cpu_plug_cb',
    'acpi_cpu_unplug_request_cb',
    'x86_cpu_unplug_request_cb',
    'x86_cpu_pre_plug',
    'x86_cpu_plug',
    'x86_cpu_unplug_cb',
    'hotplug_handler_unplug_request',
    'hotplug_handler_unplug',
    'qmp_device_del',
    'hmp_device_del',
    'qapi_event_send_acpi_device_ost',
    'qapi_event_send_device_deleted'
]


def get_workload(wlname: str) -> list:
    """
    Get the workload name
    """

    if wlname == "kern_cpuhp":
        return wl_kern_cpuhp

    if wlname == "libvirt_cpuhp":
        return wl_libvirt_cpuhp

    if wlname == "qemu_cpuhp":
        return wl_qemu_cpuhp

    return []


def chk_kern_workload(wlname: str) -> Optional[str]:
    """
    Check the worklaod is a kernel workload.
    """
    if wlname in kern_workload_list:
        return wlname
    return None


def chk_proc_workload(wlname: str) -> Optional[str]:
    """
    Check the workalod is a user peorcess worklaod.
    """
    if wlname in proc_workload_list:
        return wlname
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


def parse_args() -> argparse.Namespace:
    """
    Parse the CLI arguments
    """

    parser = argparse.ArgumentParser(
        prog='olprof',
        description='Trace and profile workload events.')

    parser.add_argument(
        "-l",
        "--workload",
        help="name of workload",
        required=True)

    parser.add_argument(
        "-p",
        "--pid",
        help="pid to trace")

    parser.add_argument(
        "-d",
        "--debug",
        action='store_true',
        help="Debug logging")

    args = parser.parse_args()
    return args


def init_dtpath(dpath: str) -> None:
    """
    Create the directory require to store the trace scripts.
    """

    msg = "Check and create dtrace path : " + dpath
    dbg(msg)
    try:
        os.mkdir(dpath)
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

    try:
        os.rmdir(dpath)
        msg = "Removing : " + dpath
        dbg(msg)
    except OSError:
        print("Error deleting directory :", dpath)


def exit_with_msg(msg: str = "", error: int = 1) -> None:
    """"
    Error out when something undesired happens
    """
    print(msg)
    sys.exit(error)


def mk_dtrace_list(pid: int = 0) -> typing.List[str]:
    """
    Create the list of traceable functions
    """

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

        except subprocess.SubprocessError:
            msg = "dtrace -ln " + param + " Error."
            exit_with_msg(msg, 1)

    if dtl_op.returncode != 0:
        msg = "dtrace -l Error : " + dtl_op.stdout.decode()
        dbg(msg)
        exit_with_msg("Error executing dtrace -l.")

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
{
"""


KERN_DT_PRINT_ENT = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Entry.\",
        walltimestamp, timestamp, pid, execname, curthread->cpu, probefunc);
"""


KERN_DT_PRINT_RET = """
    printf(\"\\n[%Y] [Time: %d] [pid: %d] [comm: %s] [cpu: %d] %s Return.\",
        walltimestamp, timestamp, pid, execname, curthread->cpu, probefunc);
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


def mk_kern_trace_entry(dtfile, this_fn: str) -> None:
    """
        Write kernel trace entry.
    """

    dt_kern_pid = DT_TXT_ENT.replace("pid__PID__", "fbt")
    dt_kern_lib = dt_kern_pid.replace("__LIB__", "")
    dt_kern = dt_kern_lib.replace("__FUNC__", this_fn)
    dtfile.write(dt_kern)
    dtfile.write(KERN_DT_PRINT_ENT)
    dtfile.write(DT_TXT_END)


def mk_kern_trace_exit(dtfile, this_fn: str) -> None:
    """
        Write kernel trace exit.
    """

    dt_kern_pid = DT_TXT_RET.replace("pid__PID__", "fbt")
    dt_kern_lib = dt_kern_pid.replace("__LIB__", "")
    dt_kern = dt_kern_lib.replace("__FUNC__", this_fn)
    dtfile.write(dt_kern)
    dtfile.write(KERN_DT_PRINT_RET)
    dtfile.write(DT_TXT_END)


def kern_create_dt(fnlist: list) -> str:
    """
    Create the dtrace script for kernel.
    """

    dbg("Start creating dt file.")
    dtl_out = mk_dtrace_list()

    if fnlist:
        dtfile_path = DTPATH+KERN_DTFILE_NAME

        try:
            with open(dtfile_path, "a", encoding="utf-8") as dtfile:
                dbg("File open : " + dtfile_path)

                dtfile.truncate(0)
                dtfile.write(DT_HDR)
                dtfile.write(DT_PRAGMA)

                for fnnames in fnlist:
                    this_fn = fnnames.strip()
                    trace_entry = False
                    trace_return = False

                    for dtl in dtl_out:
                        fnentry = " "+this_fn+" "
                        if fnentry in dtl and " entry" in dtl:
                            trace_entry = True
                            dbg(dtl)

                        if fnentry in dtl and " return" in dtl:
                            trace_return = True
                            dbg(dtl)

                    if trace_entry:
                        mk_kern_trace_entry(dtfile, this_fn)

                    if trace_return:
                        mk_kern_trace_exit(dtfile, this_fn)

                dtfile.close()
                dbg("File close : " + dtfile_path)
                os.chmod(dtfile_path, 0o777)

        except OSError:
            msg = "File open error : " + str(dtfile_path)
            exit_with_msg(msg, 2)

    return dtfile_path


def write_proc_dt(dtfile, pid: int, this_fn: str) -> None:
    """
        write process dytrace file.
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
    dtfile.write(DT_TXT_END)

    dt_lib = DT_TXT_RET.replace("__LIB__", "")
    dt_pid = dt_lib.replace("__PID__", str(pid))
    dt_buff = dt_pid.replace("__FUNC__", this_fn)
    dtfile.write(dt_buff)

    timevar = "    delta = timestamp - gvar_"+this_fn+"_ent;\n"
    dtfile.write(timevar)
    dtfile.write(PROC_DT_PRINT)
    timevar = "    delta = 0;\n"
    dtfile.write(timevar)
    timevar = "    gvar_"+this_fn+"_ent = 0;\n"
    dtfile.write(timevar)

    dtfile.write(DT_TXT_END)


def proc_create_dt(pid: int, fnlist: list) -> str:
    """
    Create the detrace script for the process.
    """

    if pid == 0:
        return ""

    dtl_out = mk_dtrace_list(pid)
    msg = "Creating dt file pid : " + str(pid)
    dbg(msg)

    if fnlist:
        proc_dtfile_name = "olprof_"+str(pid)+".d"
        dtfile_path = DTPATH+proc_dtfile_name

        try:
            with open(dtfile_path, "a", encoding="utf-8") as dtfile:
                dbg("File open " + dtfile_path)

                dtfile.truncate(0)
                dtfile.write(DT_HDR)
                dtfile.write(DT_PRAGMA)

                for fnnames in fnlist:
                    this_fn = fnnames.strip()
                    if this_fn:
                        gvar = "uint64_t gvar_"+this_fn+"_ent;\n"
                        dtfile.write(gvar)

                dtfile.write("uint64_t delta;\n")
                dtfile.write(DT_BEGIN)

                for fnnames in fnlist:
                    this_fn = fnnames.strip()
                    if this_fn:
                        gvar = "    gvar_"+this_fn+"_ent = 0;\n"
                        dtfile.write(gvar)

                dtfile.write("    delta = 0;\n")
                dtfile.write(DT_TXT_END)

                for fnnames in fnlist:
                    this_fn = fnnames.strip()
                    dbg(this_fn)
                    trace_fn = False

                    for dtl in dtl_out:
                        fnentry = " "+this_fn+" "
                        if fnentry in dtl:
                            trace_fn = True
                            dbg(dtl)

                    if this_fn and trace_fn:
                        write_proc_dt(dtfile, pid, this_fn)

                dtfile.close()
                dbg("File close : " + dtfile_path)
                os.chmod(dtfile_path, 0o777)

        except OSError:
            msg = "File open error : " + str(dtfile_path)
            exit_with_msg(msg, 2)

    return dtfile_path


def run_dt(dtfile_path: str) -> None:
    """
    Execute the created dtrace script.
    """

    msg = "Starting dtrace : " + dtfile_path
    dbg(msg)
    param = dtfile_path
    try:
        os.system(param)

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
        print(msg)


def signal_handler(sig: int, frame) -> None:
    """
    Handle sigint and execute necessary cleanup.
    """

    print("Exit on signal", str(sig))
    cleanup_trace()


def trace_proc(function_list: str, tpid: int) -> str:
    """
    Trace user process.
    """

    kwl_rc = chk_kern_workload(function_list)
    if kwl_rc:
        msg = "Kernel workload doesnot require pid."
        exit_with_msg(msg, 2)

    msg = "Creating dtrace for pid : " + str(tpid)
    msg = msg + " and workload : "+function_list

    print(msg)
    mk_dtrace_list(tpid)

    wlname = get_workload(function_list)
    if not wlname:
        msg = "Invalid workload : " + function_list
        exit_with_msg(msg, 2)

    dtfile_path = proc_create_dt(tpid, wlname)
    msg = "Running dtrace for pid : "+str(tpid)
    msg = msg+" and workload : "+function_list
    print(msg)

    run_dt(dtfile_path)

    return dtfile_path


def trace_kern(function_list: str) -> str:
    """
    Trace kernel.
    """

    pwl_rc = chk_proc_workload(function_list)
    if pwl_rc:
        msg = function_list + " Workload requires pid."
        exit_with_msg(msg, 2)

    msg = "Creating dtrace for kernel, workload : "+function_list
    print(msg)
    mk_dtrace_list()

    wlname = get_workload(function_list)
    if not wlname:
        msg = "Invalid workload : " + function_list
        exit_with_msg(msg, 2)

    dtfile_path = kern_create_dt(wlname)
    msg = "Running dtrace for kernel, workload : "+function_list
    print(msg)

    run_dt(dtfile_path)

    return dtfile_path


def main() -> None:
    """
    olprof genartes profiling scripts dynamically for a list of
    functions representing a workload and excutes the profiling script.
    The profiled data contains outputs of  entry and return traces of each
    function listed in workload list. If a function is not traceable,
    olprof will skip it and continue to trace other functions.

    The oled olprof command  mandates use of the `-l` option ponits to
    workload function list. The default workloads are available in the
    workload directory.

    The command oled olprof with a pid as an argument, will trace the
    specified process, otherwise will trace the kernel.

    The command oled olprof with -d option, excutes in debug mode.
    """

    if os.geteuid() != 0:
        msg = "You need to have root privileges to run this script."
        exit_with_msg(msg)

    init_dtpath(DTPATH)
    args = parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    if args.debug:
        dbg("Debug mode enabled")

    if args.workload:
        function_list = args.workload
        wl_rc = None
        wl_rc = chk_workload(function_list)
        if wl_rc:
            msg = "Tracing workload: "+function_list
            print(msg)
        else:
            msg = "Workload "+function_list+" does not exist."
            print(msg)
            print("Available workloads are: ")
            print_workload()

            exit_with_msg("", 2)

    if args.pid:
        dtfile_path = trace_proc(function_list, args.pid)
    else:
        dtfile_path = trace_kern(function_list)

    if args.debug:
        cmd = "cat "+dtfile_path+" 2>/dev/null"
        os.system(cmd)

    cleanup_trace()


main()
