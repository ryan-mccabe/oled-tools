kill_trace.sh(8)

# NAME
kill_trace.sh - Monitor a process for a specific kill signal and display details of the process that issued the kill signal.

# SYNOPSIS
kill_trace.sh [(-n NAME|--name NAME) | (-p PID|--pid PID) ] [(-s SIGNAL|--signal SIGNAL) ] [(-v|--verbose) ] [ (-h|--help) ]

# DESCRIPTION
kill_trace.sh is a shell script designed to monitor a process for a specific kill signal and display details of the process that issued the kill signal. It uses DTrace to monitor the process and display the details of the killer process, including its PID, parent's PID, and the signal used.

# OPTIONS
\
The following options are available:
** *-n NAME*, *--name NAME* Specify the process name (mutually exclusive with *-p*/*--pid*)
** *-p PID*, *--pid PID* Specify the process id (mutually exclusive with *-n*/*--name*)
** *-s SIGNAL*, *--signal SIGNAL* Specify the signal number (default: *100*, *monitors all signals*)
** *-v*, *--verbose* Enable verbose output (can be combined with *-n* , *-s* or *-p*)
** *-h*, *--help* Show this help message and exit

# USAGE
\
Default execution of kill_trace.sh will monitor system-wide for the default kill signal 100 (all type of kill signals) and display the details of the process that issued the kill signal.
\
To monitor a specific process, use the *-n (or --name)* option to specify the process name or the *-p (or --pid)* option to specify the process id.
\
To use kill_trace.sh, simply run the command with the process name or PID as an argument:
\
\  \    *kill_trace.sh -n <process_name>*
\
\  \    *kill_trace.sh -p <pid_of_the_process>*
\
*Monitor a Process for a Specific Kill Signal*
\
You can monitor a process and specify the signal number directly using the -s (or --signal) option.

# OUTPUT
The output of kill_trace.sh will display the details of the process that issued the kill signal, including its PID, parent's PID, and the signal used.

The output will be in the following format:

[[ killer(PID)
:- Killer_parent(PPID)
:- Signal
:- target_pid

##  EXAMPLES
## Monitor a process for the default kill signal:
\  \    *kill_trace.sh -n my_process*

## Monitor a process for a specific kill signal:
\  \    *kill_trace.sh -n my_process -s 9*
\

This will monitor the process *my_process* or with *PID 1234* for the default kill signal (100) and display the details of the process that issued the kill signal.
\
\  \    *kill_trace.sh -n my_process*
\
\  \    *kill_trace.sh -p 1234*

## Enable debug logging:
kill_trace.sh -v -n my_process
\
\  \    *kill_trace.sh -n my_process -s 9*
\
This will monitor the process my_process for signal 9 (SIGKILL).


# SERVICE
kill_trace.sh can also be run as a service using the signal_snooper.service file. To enable the service, run the following command:

\   \   *systemctl enable signal_snooper.service*

To start the service, run the following command:

\   \   *systemctl start signal_snooper.service*

It will start tracking the kill signal and logs can be observed in journalctl logs.

By default service will catch only *signal 9* (SIGKILL).

# DIAGNOSTIC INFORMATION
Diagnostic information will be written to /var/log/messages from the kill_watcher service.Journalctl can also be used with the service to filter out the logs related to kill_trace.

The diagnostic information can be accessed using the journalctl command.The diagnostic information are logged under the SYSLOG_IDENTIFIER "kill_watcher" and "kill_trace".
The kill_watcher service is a wrapper for the kill_trace.sh shell script.

To enable the debug logging in the kill_watcher service, set the KILL_WATCHER_DEBUG environment variable to -v.It is also possible to enable the debug logging in the kill_trace.

#  SEE ALSO
systemd(1)
OLED(8)
journalctl(1)
dtrace(1)
signal_snooper.service(8)
#   COLOPHON
This page is part of the OLED (Oracle Linux Enhanced Diagnostic) tools project. If you have a bug report for this manual page, send it to https://www.oracle.com/support/