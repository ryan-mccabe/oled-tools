rpm_db_snooper(8)

# NAME

rpm_db_snooper - A systemd service to monitor process termination signals related to the RPM database

# SYNOPSIS

rpm_db_snooper.service

General systemd command can be used to start or restart the service for more info see *systemd(1)* man page

# DESCRIPTION

*rpm_db_snooper* is a systemd service to monitor on process termination signals related to the RPM database, providing insights into potential issues and improve system maintenance.

# FILES
The following files are relevant to the rpm_db_snooper command:

/var/lib/rpm
	The default location of the RPM database.

/usr/libexec/oled-tools/scripts.d/monitor_rpmdb.d
	DTrace program that monitors the RPM database for any changes made by the yum, dnf, or rpm commands.

/var/log/messages
	Diagnostic information will be written to this file from rpm_db_snooper service

journalctl -u rpm_db_snooper.service
	Journalctl can also be used with the service to filter out the logs related to rpm_db_snooper.

The diagnostic information can be accessed using *journalctl* command. The diagnostic information are logged under the *SYSLOG_IDENTIFIER* "rpm_db_snooper".
The *rpm_db_snooper* command is a wrapper for the *monitor_rpmdb.d* DTrace program.

To enable the debug logging in the *rpm_db_snooper* command, set the *RPM_DB_SNOOPER_DEBUG* environment variable to *-DDEBUG*.
It is also possible to enable the debug logging in the *monitor_rpmdb.d* DTrace program by setting the *DEBUG* environment variable in the *monitor_rpmdb.d* DTrace program
or invoke the *monitor_rpmdb.d* dtrace program using the *dtrace* command with the *-DDEBUG* flag.


# SEE ALSO
systemd(1), OLED(8), journalctl(1) and lkce(8)
# COLOPHON

This page is part of the OLED (Oracle Linux Enhanced Diagnostic) tools project. If you have a bug report for this manual page, send it to https://www.oracle.com/support/ 
