#!/usr/sbin/dtrace -Zqs

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
 */

/*
 * Author: Imran Khan.
 * Purpose: This script detects and prints the details of tasks stuck in D
 *          (UNINTERRUPTIBLE sleep) state for longer than a specified threshold.
 * Prerequisites: Refer to the file hungtask_detector_example.txt
 * Sample output: Refer to the file hungtask_detector_example.txt
 */

/*
 * min_kernel 5.4.17,5.15.0-200.103.1,6.12.0-0.0.1
 */

#pragma D option defaultargs

dtrace:::BEGIN
{
    TASK_UNINTERRUPTIBLE = 0x2;
    HUNG_DURATION_THRESH_US = $1 ? $1 : 100; 
}

/* Trace only D states */
sdt:sched:*:sched_switch
/arg3 == TASK_UNINTERRUPTIBLE/
{
    self->ts = timestamp;
}

fbt::finish_task_switch:entry
/((self->ts) &&
 ((timestamp - self->ts) >= HUNG_DURATION_THRESH_US * 1000))/
{

    this->delta = timestamp - self->ts;
    self->ts = 0;
    this->delta_us = this->delta / 1000;
    this->current_pid = ((struct task_struct*)curthread)->pid;
    this->current_comm = stringof(((struct task_struct*)curthread)->comm);
    printf(" %Y pid: %d comm: %s was blocked for %lu us in D state. \n", walltimestamp, this->current_pid, this->current_comm, this->delta_us);
    stack();
}


fbt::finish_task_switch:entry
/((self->ts) &&
 ((timestamp - self->ts) < HUNG_DURATION_THRESH_US * 1000))/
{

    self->ts = 0;
}

rawfbt::finish_task_switch*:entry
/((self->ts) &&
 ((timestamp - self->ts) >= HUNG_DURATION_THRESH_US * 1000))/
{

    this->delta = timestamp - self->ts;
    self->ts = 0;
    this->delta_us = this->delta / 1000;
    this->current_pid = ((struct task_struct*)curthread)->pid;
    this->current_comm = stringof(((struct task_struct*)curthread)->comm);
    printf(" %Y pid: %d comm: %s was blocked for %lu us in D state. \n", walltimestamp, this->current_pid, this->current_comm, this->delta_us);
    stack();
}


rawfbt::finish_task_switch*:entry
/((self->ts) &&
 ((timestamp - self->ts) < HUNG_DURATION_THRESH_US * 1000))/
{

    self->ts = 0;
}
