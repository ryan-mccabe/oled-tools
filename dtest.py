import argparse
import os
import time
import signal
import re
import shutil
import subprocess as sp
import platform
from datetime import datetime

SCRIPTS_DIRECTORY = "./scripts"   #path to dtrace scripts directory
RESULTS_DIRECTORY = "./results"
current_kernel_version = platform.uname().release

script_specific_args = {
    "rds_check_tx_stall.d" : ["1000"],
    "spinlock_time.d" : ["2"],
    "nvme_io_comp.d" : ["2", "2"],
    "scsi_latency.d" : ["5"],
}

def version_tuple(version):
    """
    Converts a kernel version string into a tuple of integers.
    """
    return tuple(int(x) for x in re.split(r'[.-]', version) if x.isnumeric())


def is_kernel_version_compatible(current_kernel_version, min_version, max_version):
    """
    Checks if the current kernel version is compatible with the specified
    minimum and maximum kernel versions.
    """
    if not min_version and not max_version:
        return False
    current_version = '.'.join(current_kernel_version.split('.')[:-2])
    current_version_tuple = version_tuple(current_version)
    min_version_tuple = version_tuple(min_version) if min_version else None
    max_version_tuple = version_tuple(max_version) if max_version else None

    if min_version_tuple and current_version_tuple < min_version_tuple:
        return False
    if max_version_tuple and current_version_tuple > max_version_tuple:
        return False

    return True


def get_compat_kernel_versions(file_path: str) -> tuple:
    min_kernel_version = None
    max_kernel_version = None
    curr_ver = platform.uname().release.split('-')[0]

    if not os.path.isfile(file_path):
        return min_kernel_version, max_kernel_version

    try:
        with open(file_path, 'r') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line.startswith('* min_kernel'):
                    min_versions = line.split()[2]
                    for version in min_versions.split(','):
                        if version.startswith(curr_ver):
                            min_kernel_version = version
                elif stripped_line.startswith('* max_kernel'):
                    max_versions = line.split()[2]
                    for version in max_versions.split(','):
                        if version.startswith(curr_ver):
                            max_kernel_version = version
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")

    return min_kernel_version, max_kernel_version


def check_and_load_modules(modules, dtest_log):
    for module in modules:
        try:
            sp.run(["modprobe", module])
            dtest_log.write(f"Loaded {module} module\n")
        except sp.CalledProcessError as e:
            dtest_log.write(f"Error loading module {module}: {e}\n")


def setup_logging():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dtest_log = open("dtest.log", "w")
    dtest_log.write(f"Start Time: {start_time}\n")
    dtest_log.write(f"Running {dtrace_version} from {dtrace_path}\n")
    dtest_log.write("Dtest Version: Dtest-automation 1.0.0\n\n")
    return dtest_log

def matched_probe_count(error_message):
    match = re.search(r'matched (\d+) probe', error_message)
    if match:
        return int(match.group(1))
    return None

def execute_script(script_name, verbose, quiet, flags_and_params, script_args, dtest_log):
    global skipped_count
    script_file_path = script_name
    script_base_path = os.path.splitext(script_name)[0]
    script_base_name = os.path.basename(script_base_path)
    min_kernel_version, max_kernel_version = get_compat_kernel_versions(script_file_path)
    if not is_kernel_version_compatible(current_kernel_version, min_kernel_version, max_kernel_version):
        print(f"{script_base_name:<20}: Skipping: Error: file not compatible for current kernel version {current_kernel_version}\n")
        dtest_log.write(f"{script_base_name:<20}: Skipping: Error: file not compatible for current kernel version {current_kernel_version}\n")
        skipped_count += 1
        return
    
    cmd = ["dtrace", "-Cs"]
    if verbose:
        cmd.insert(1, "-v")
    if quiet:
        cmd.insert(1, "-q")
    cmd.extend(flags_and_params)
    cmd.append(script_file_path)

    if script_name in script_args:
        cmd.extend(script_args[script_name])

    print(f"============={script_base_name}=============")
    dtest_log.write(f"{script_base_name:<20}: ")
    out_file_path = os.path.join(RESULTS_DIRECTORY, f"{script_base_name}.out")
    err_file_path = os.path.join(RESULTS_DIRECTORY, f"{script_base_name}.err")
    with open(out_file_path, 'w') as out, open(err_file_path, 'w') as err:
        process = sp.Popen(cmd, stdout=out, stderr=err)
        time.sleep(5)
        os.kill(process.pid, signal.SIGINT)
        process.wait()

    if os.path.exists(err_file_path):
        with open(err_file_path, 'r') as err_file:
            error_message = err_file.read().strip()
            matched_probes = matched_probe_count(error_message)
            if matched_probes is not None and matched_probes > 0:
                successful.append(script_name)
                dtest_log.write(f"Successful\n")
                print("Successful!")
                os.remove(err_file_path)
            else:
                failed.append(script_name)
                dtest_log.write(f"Failed\n")
                print("Failed!")
    else:
        failed.append(script_name)
        print(f"Error : No .err file found for {script_name}")
        dtest_log.write(f"Error: No .err file found for {script_name}\n")



def execute_all_scripts(verbose, quiet, flags_and_params, dtest_log):
    global skipped_count
    uek_acronyms = {
    "5.15.0": "UEK7",
    "5.4.17": "UEK6",
    "4.14.35": "UEK5"
    }

    uek_ver = None
    for version, uek in uek_acronyms.items():
        if uek_ver is None and current_kernel_version.startswith(version):
            uek_ver = uek
            break
    modules = ["fbt", "sdt"]
    if uek_ver == "UEK5":
        check_and_load_modules(modules,dtest_log)

    script_files = [
        os.path.join(root, f)
        for root, dirs, files in os.walk(SCRIPTS_DIRECTORY)
        for f in files
        if f.endswith('.d')
    ]

    if script_files:
        dtest_log.write(f"Executing scripts for {uek_ver} kernel version {current_kernel_version}\n\n")
        print(f"Executing scripts for {uek_ver} kernel version {current_kernel_version}")
        
        for script_name in script_files:
            if not os.path.exists(script_name):
                dtest_log.write(f"Error: Skipping--->{script_name} file not found\n")
                print(f"Error: Skipping--->{script_name} file not found\n")
                skipped_count += 1
                continue
            execute_script(script_name, verbose, quiet, flags_and_params, script_specific_args, dtest_log)
    
    else:
        print("No Dtrace scripts found in the specified directory.")
        dtest_log.write("No Dtrace scripts found in the specified directory.\n")

def main():
    dtest_log = setup_logging()
    dtest_log.write("Loading Modules\n")
    modules = ["ext4", "isofs", "nfs", "rds", "xfs", "btrfs"]
    check_and_load_modules(modules, dtest_log)
    try:
        os.system("ulimit -l unlimited")
    except Exception as e:
        print(f"Error setting ulimit: {e}")
        dtest_log.write(f"Error setting ulimit: {e}\n")

    parser = argparse.ArgumentParser(description=help_message,usage=Usage, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("script_name", nargs='?', help="Name of the DTrace script to execute")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-q", "--quiet", action="store_true", help="Decrease verbosity")
    parser.add_argument("additional_args", nargs=argparse.REMAINDER, help="Additional arguments for single script execution")
    args = parser.parse_args()
    if args.script_name:
        script_name = args.script_name
        if not os.path.exists(os.path.join(SCRIPTS_DIRECTORY, script_name)):
            dtest_log.write(f"Error: DTrace script '{script_name}' not found in the scripts directory.\n")
            print(f"Error: DTrace script '{script_name}' not found in the scripts directory.")
            exit(1)
        execute_script(script_name, args.verbose, args.quiet,args.additional_args, script_specific_args, dtest_log)
    else:
        execute_all_scripts(args.verbose, args.quiet, args.additional_args, dtest_log)

    dtest_log.write(f"\n\nSummary of Execution:\n")
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dtest_log.write(f"End time: {end_time}\n")
    total_executed_scripts = len(successful) + len(failed)
    dtest_log.write(f"Total Scripts: {total_executed_scripts+skipped_count}\nSuccessful: {len(successful)}\nFailed: {len(failed)}\nSkipped: {skipped_count}\n")
    dtest_log.close()

if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dtrace_path = sp.check_output(["which", "dtrace"]).decode().strip()
    dtrace_version = sp.check_output(["dtrace", "-V"]).decode().strip()

    Usage = """
    For Running all Scripts automated
    python3 dtest.py [-h] [-v] [-q]
    For Running single script
    python3 dtest.py script_name.d [-h] [-v] [-q] -s
    """
    help_message = """
    This script executes DTrace scripts listed in SCRIPTS_DIRECTORY based on flags passed and kernel version
    Generates the std output in ./results directory in file named script-name.out and std error in file named script-name.err

    Check the logs for execution in ./dtest.log file
    """

    # Remove the existing result directory and create new results directory
    if os.path.exists(RESULTS_DIRECTORY):
        shutil.rmtree(RESULTS_DIRECTORY)
    os.makedirs(RESULTS_DIRECTORY)

    skipped_count = 0

    successful = []
    failed = []

    main()

