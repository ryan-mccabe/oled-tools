signal_snooper.service(8)
# NAME
signal_snooper.service - A systemd service to monitor process termination signals

# SYNOPSIS
signal_snooper.service

General systemd service can be used to start or restart the service for more info see systemd(1) man page

# DESCRIPTION

signal_snooper.service is a systemd service to monitor process termination signals, providing insights into potential issues and improve system maintenance.++
By default, the service monitors processes for the SIGKILL (9) signal.

# SERVICE
To enable the service, run the following command:

\   *systemctl enable signal_snooper.service*

To start the service, run the following command:

\   *systemctl start signal_snooper.service*

It will start tracking the kill signal and logs can be observed in journalctl logs.

# DIAGNOSTIC INFORMATION
/var/log/messages Diagnostic information will be written to this file from signal_snooper service

journalctl -u signal_snooper.service

Journalctl can also be used with the service to filter out the logs related to signal_snooper.

The diagnostic information can be accessed using journalctl command. The diagnostic information are logged under the SYSLOG_IDENTIFIER "signal_snooper".++
The signal_snooper service is a wrapper for the kill_trace.sh shell script.

The systemd service file can be updated to include the -s (signal number) parameter, allowing you to configure which signal to monitor.

To enable the debug logging in the signal_snooper service, set the KILL_WATCHER_DEBUG environment variable to -v.++
It is also possible to enable the debug logging in the kill_trace.sh shell script by setting the DEBUG_FLAG environment variable in the signal_snooper service or invoke the kill_trace.sh script using the bash command with the -v flag.

# SEE ALSO
systemd(1)
OLED(8)
journalctl(1)
kill_trace(8)
dtrace(1)
# COLOPHON
This page is part of the OLED (Oracle Linux Enhanced Diagnostic) tools project. If you have a bug report for this manual page, send it to https://www.oracle.com/support/