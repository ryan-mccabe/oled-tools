#!/usr/sbin/dtrace -Cs

#pragma D option quiet

/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 2 only, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * version 2 for more details (a copy is included in the LICENSE file that
 * accompanied this code).
 *
 * You should have received a copy of the GNU General Public License version
 * 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
 *
 * Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
 * or visit www.oracle.com if you need additional information or have any
 * questions.
 *
 * monitor_rpmdb.d
 *
 * This DTrace script monitors the RPM database for any changes made by
 * the yum, dnf, or rpm commands.
 * It captures the process ID (PID) and parent process ID (PPID)
 * of the killing process, as well as the signal
 * sent to the RPM database user process.
 *
 * Author : Sagar Sagar <sagar.sagar@oracle.com>
 */

/* File mode and group permission */
#define O_RDONLY	                     0x00
#define O_WRONLY	                     0x01
#define O_RDWR		                     0x02
#define NOT_A_WRITER                      ""

/* Helper pre processor */
#define IS_WRITE_MODE(m) \
                                        ((m) & (O_RDWR | O_WRONLY))
#define GET_FILE_NAME(name)             (basename(stringof(name)))
#define IS_PACKAGE_MANAGER(execname) \
                                        (execname == "yum" || execname == "dnf" || execname == "rpm")
#define IS_DATABASE_FILE(filename) \
                                        (strstr(GET_FILE_NAME(filename), "__db") != NULL || strstr(GET_FILE_NAME(filename), "history.sqlite") != NULL)


struct killer_info {
    int64_t pid;
    int64_t ppid;
    string process_name;
    string parent_process_name;
    int64_t target;
    string target_process_name;
    int64_t signal;
} killer;

string db_users[int64_t];

BEGIN
{
    printf("-------------------------\n");
    printf("Rpm db snooper - start \n");
    self->killer_found = 0 ;
    self->database_user_found = 0;
}

/* Point to find the database consumer */
fbt:vmlinux:do_sys_open*:entry
/ IS_PACKAGE_MANAGER(execname) && (IS_DATABASE_FILE(arg1))
  && db_users[pid] != execname  /
{
    self->filename = GET_FILE_NAME(arg1);
    self->flag =  (probefunc == "do_sys_openat2") ? (*(struct open_how *)arg2).flags : arg2;

    db_users[pid] = IS_WRITE_MODE(self->flag) ? execname  : NOT_A_WRITER;
    self->database_user_found = IS_WRITE_MODE(self->flag) ? 1 : 0;

#ifdef DEBUG
    printf ("Database consumer found flag = %s\n", self->database_user_found ? "true" : "false"); 
    printf("Process %s(%d) opened the database file %s\n", db_users[pid], pid, self->filename);
    printf("Database consumer %s opened the database in %s mode\n", db_users[pid],(self->flag & O_RDWR) ? "read-write": "write");
#endif
}

fbt:vmlinux:do_sys_open*:return
/ self->database_user_found == 1  && db_users[pid] == execname  && (int)arg0 < 0 /
{
    self->database_user_found = 0;
    self->filename = "";
}

/* Point to find the killer of database consumer */
syscall::kill:entry
/ db_users[(int64_t)arg0] != 0 && arg1 != 0 /
{
    self->killer_found = 1;
    killer.pid =  pid;
    killer.ppid = ppid;
    killer.process_name = execname;
    killer.target = (int64_t)arg0;
    killer.target_process_name = db_users[killer.target];
    killer.parent_process_name = curthread->real_parent->real_parent->comm;
    killer.signal = arg1;
#ifdef DEBUG
    printf ("killer found flag = %s\n", self->killer_found ? "true" : "false");
#endif
    printf("%-20s %-25s %-12s %-25s\n",
       "Process(PID)", "Parent Process(PID)", "Signal No", "Target Process(PID)");
}

syscall::kill:return
/ self->killer_found == 1 && arg0 == 0 && pid == killer.pid /
{
    printf("%s(%d) %13s(%d)  %16d  %10s(%d)\n",
            killer.process_name, killer.pid, killer.parent_process_name, killer.ppid, killer.signal, \
            killer.target_process_name, killer.target);

    /* cleanup */
    self->killer_found = 0;

    /* Reset 'killer' structure */
    killer.pid = 0;
    killer.ppid = 0;
    killer.process_name = "";
    killer.parent_process_name = "";
    killer.target = 0;
    killer.target_process_name = "";
    killer.signal = 0;

    /* Reset 'db_user' structure */
    db_users[pid] = "";
}

/* Point to reset the database consumer if it has exited */
syscall:vmlinux:exit_group:entry,
syscall:vmlinux:exit:entry
/ db_users[pid] == execname /
{

#ifdef DEBUG
    printf("Process %s(%d) exited with code %lld and closed the database \n", execname,pid,arg0); 
#endif
    db_users[pid] = "";
}

END
{
    /* cleanup */
    /* Reset 'killer' structure */
    killer.pid = 0;
    killer.ppid = 0;
    killer.process_name = "";
    killer.parent_process_name = "";
    killer.target = 0;
    killer.target_process_name = "";
    killer.signal = 0;

    /* Reset 'db_user' structure */
    db_users[pid] = "";

    printf("Rpm db snooper - end \n");
    printf("-------------------------\n");
}