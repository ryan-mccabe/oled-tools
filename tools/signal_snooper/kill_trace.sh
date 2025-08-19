#!/bin/bash

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
#

# kill_trace.sh
#
# Monitor a process for a specific kill signal and display details 
# of the process that issued the kill signal.
#
# This script reads the signal number from a file located at 
# /tmp/signal.txt. By default, the file contains signal number 100,
# which can be modified by the user to track a specific kill signal
# for a given process.
#
# It displays the details of the process that issued the kill signal
# including the killer's PID, parent's PID, and the signal used,
# in a tabular format.
#
# Usage: ./kill_trace.sh 
#        ./kill_trace.sh -p <pid_of_the_process>
#        ./kill_trace.sh -n <name_of_the_process>
#        ./kill_trace.sh -v enable debugging mode
#        ./kill_trace.sh -h show help
# Author: Sagar Sagar <sagar.sagar@oracle.com>

#!/bin/bash

NAME=""
PID=""
VERBOSE=0
SIGNAL=""   # New signal variable
PROGRAM_NAME=$(basename "$0")
D_Signal=100


show_help() {
cat << EOF
Usage: $PROGRAM_NAME [(-n NAME|--name NAME) | (-p PID|--pid PID) ] [(-s SIGNAL|--signal SIGNAL) ] [(-v|--verbose) ] [ (-h|--help) ]
Options:
  -n, --name     Specify the process name (mutually exclusive with -p/--pid)
  -p, --pid      Specify the process id (mutually exclusive with -n/--name)
  -s, --signal   Specify the signal number (default: $D_Signal, monitor all signals)
  -v, --verbose  Enable verbose output
  -h, --help     Show this help message and exit
EOF
}


get_pid_from_name() {
    local name="$1"
    local pid=$(pgrep -n "$name")
    if [[ -z "$pid" ]]; then
        echo "Error: No process found with name '$name'" >&2
        return 1
    fi
    echo "$pid"
}


debug_output() {
    echo "Debug: Debug mode enabled"
    if [[ -n "$NAME" && -n "$PID" ]]; then
        echo "Debug: Tracking process PID (from process name $NAME): $PID"
    elif [[ -n "$PID" ]]; then
        echo "Debug: Tracking process PID: $PID"
    fi
    echo "Debug: Using signal $SIGNAL"
}


get_pid_if_name_set() {
    if [[ -n "$NAME" ]]; then
        PID=$(get_pid_from_name "$NAME")
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to get PID for process name '$NAME'"
            exit 1
        fi
    fi
}


# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--name)
            if [[ -n "$PID" ]]; then
                echo "Error: --name and --pid cannot be used together."
                exit 1
            fi
            if [[ -n "$NAME" ]]; then
                echo "Error: --name specified more than once."
                exit 1
            fi
            NAME="$2"
            shift 2
            ;;
        -p|--pid)
            if [[ -n "$NAME" ]]; then
                echo "Error: --name and --pid cannot be used together."
                exit 1
            fi
            if [[ -n "$PID" ]]; then
                echo "Error: --pid specified more than once."
                exit 1
            fi
            if [[ $2 =~ ^[0-9]+$ && -n "$(ps -p "$2" -o pid=)" ]]; then
                PID="$2"
                shift 2
            else
                echo "Error: --pid requires a valid numerical value"
                show_help
                exit 1
            fi
            ;;
        -s|--signal)
            if [[ -n "$SIGNAL" ]]; then
                echo "Error: --signal specified more than once."
                exit 1
            fi
            if [[ $2 =~ ^[0-9]+$ && $2 -ge 0 && $2 -le 31 ]]; then
                SIGNAL="$2"
                shift 2
            else
                echo "Error: --signal requires a value between 0-31"
                exit 1
            fi
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done


# Enforce mutual exclusivity: Only one of NAME, PID allowed (besides verbose)
count=0
[[ -n "$NAME" ]] && ((count++))
[[ -n "$PID" ]] && ((count++))

if [[ $count -gt 1 ]]; then
    echo "Error: Only one of --name or --pid can be used."
    exit 1
fi


if [[ -n "$NAME" ]]; then
    get_pid_if_name_set "$NAME"
fi

# Default signal if none provided
if [[ -z "$SIGNAL" ]]; then
    SIGNAL=$D_Signal
fi

if [[ $VERBOSE -eq 1 ]]; then
    debug_output
fi

#################################
# --- Main Program, DTrace ---
#

### Define D Script
dtrace='
#pragma D option quiet
#pragma D option destructive

inline int SIGNAL = '$SIGNAL';
inline int D_SIG = '$D_Signal';
inline int debug = '$VERBOSE';
struct process_info{
    int64_t pid;
    string process_name;
    int64_t ppid;
    string parent_process_name;
    int64_t target_pid;
}killer_process;


dtrace:::BEGIN
{
    debug ? printf("----------------------------------------\n") : 0;
    debug && $target ? (SIGNAL == D_SIG ? printf("Debug: Monitoring process %d for all kill signals \n", $target) : printf("Debug: Monitoring process %d for kill signal %d \n", $target, SIGNAL)) : 0;
    debug && !$target ? printf("Started monitoring kill signal %d system wide\n", SIGNAL) : 0;

    /* Initialize variables */
    self->found = 0;
    self->pid = 0;
    self->signal = 0;
}

syscall::kill:entry
/
    SIGNAL == D_SIG ? 0 : 1 &&
    $target == (int64_t)arg0 &&
    arg1 != 0 && arg0 != 0
/
{
    debug ? printf("Debug: No signal match found\n") : 0;
    debug ? printf("Target process %d received signal %d which is not in the tracking list\n", arg0, arg1) : 0;
}

syscall::kill:entry
/ ($target == 0 || $target == (int64_t)arg0) &&
  arg1 != 0 && arg0 != 0  &&
  SIGNAL == D_SIG ? 1 : arg1 == SIGNAL ? 1 : 0
/
{
    debug  && $target ? printf("Debug: Found killer process %d\n", pid) : 0;
    debug ? printf("%-16s %-16s %-16s %-16s\n","killer(PID)","Killer_parent(PPID)","Signal","target pid"): 0;
    debug ? printf("%-15s %-20s %-15s %-15s\n","------------","-----------------","------","--------------") : 0;

    self->found = 1 ;
    self->pid = pid;
    self->signal = arg1;

    killer_process.pid = pid;
    killer_process.process_name = execname;
    killer_process.ppid = ppid;
    killer_process.parent_process_name = curthread->real_parent->real_parent->comm;
    killer_process.target_pid = arg0;

}

syscall::kill:return
/ self->found == 1 && self->pid == pid && arg0 == 0/
{
    printf("%s(%d)  %10s(%d) %6d %18d\n",
    killer_process.process_name, killer_process.pid, killer_process.parent_process_name, killer_process.ppid, self->signal,killer_process.target_pid);

    /* reset */
    self->found = 0;
    self->pid = 0;
    self->signal = 0;
}

::do_tkill:entry
/ $target == arg1 &&
  arg0 != 0 && self->found == 0/
{
    printf("Target pid = %d received signal %d with thread ID = %d\n", arg1, arg2, arg0);
    self->found = 1;
}

dtrace:::END
{
    debug ? printf("Debug: Process kill signal watcher %d - Exiting\n", $target) : 0;
    debug ? printf("----------------------------------------\n") : 0;
}
'

### Run Dtrace
if [ $VERBOSE -eq 1 ]; then
    echo "Debug: Running DTrace in DEBUG mode"
fi

if [ -n "$PID" ]; then
    [ $VERBOSE -eq 1 ] && echo "Debug: Running DTrace on PID $PID"
    /usr/sbin/dtrace -n "$dtrace" -p "$PID"
else
    [ $VERBOSE -eq 1 ] && echo "Debug: No pid given to run dtrace on"
    /usr/sbin/dtrace -n "$dtrace"
fi
