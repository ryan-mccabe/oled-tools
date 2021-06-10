#!/usr/bin/python
# Copyright (c) 2020, Oracle and/or its affiliates.
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

"""
Module contains Base class for
Smtool. The Base class contains definitions
for various vulnerabilities, server types and
runtime settings along with some
helper functions.

"""
import os
import subprocess
import sys

if(sys.version[0] == "3"):
    from .command import Cmd
else:
    from command import Cmd

class Base(object):
    """
    Base class for the script.
    Contains definitions for various vulnerabilities,
    server types, runtime settings.
    Also contains methods run commands and
    to read and write files.

    """
    # spectre/meltdown variants

    def __init__(self):
        """
        Init method for Base class.

        """
        pass

    SPECTRE_V1 = 1
    SPECTRE_V2 = 2
    MELTDOWN = 3
    SSBD = 4
    L1TF = 5
    MDS = 6
    ITLB_MULTIHIT = 7
    TSX_ASYNC_ABORT = 8
    vdesc = [
        "Unknown",
        "Spectre V1",
        "Spectre V2",
        "Meltdown",
        "SSBD",
        "L1TF",
        "MDS",
        "ITLB_Multihit",
        "TSX_Async_Abort"]

    # runtime settings
    IBRS_ENABLED = 1
    IBPB_ENABLED = 2
    RETPOLINE_ENABLED = 3
    RETPOLINE_FALLBACK = 4
    VMENTRY_L1D_FLUSH = 5
    SMT_CONTROL = 6

    # Server types
    UNKNOWN = 0
    BARE_METAL = 1
    XEN_HYPERVISOR = 2
    XEN_PV = 3
    XEN_HVM = 4
    KVM_HOST = 5
    KVM_GUEST = 6
    sdesc = ["Unknown", "Bare Metal", "Xen Hypervisor", "Xen PV", "Xen HVM",
             "KVM_HOST", "KVM_GUEST"]

    def run_command(self, cmd):
        """
        Execute command and return the result
        Parameters:
        cmd (int): Command to run
        shell (bool): If True, run command through
        the shell

        Returns string: result of the specific command
        executed.

        """
        command = Cmd()
        command.run(cmd)
        return command.out


    def read_file(self, file_path):
        """
        Read file contents.

        Parameters:
        file_path (str): File path.

        Returns:
        str: Contents of the file.

        """
        if not os.path.exists(file_path):
            raise ValueError("ERROR: path " + file_path + " doesn't exist")

        if os.path.isdir(file_path):
            raise ValueError("ERROR: reading from directory " + file_path)

        try:
            f_p = open(file_path)
            ret = f_p.read()
            return ret.strip()
        except BaseException:
            raise ValueError("ERROR reading file " + file_path)

    def write_file(self, file_path, val):
        """
        Write file contents.

        Parameters:
        file_path(str): File path.
        val(str): Content to be written to file.

        Returns:
        None if the operation is successful.

        """
        if not os.path.exists(file_path):
            raise ValueError("ERROR: path " + file_path + " doesn't exist")

        if os.path.isdir(file_path):
            raise ValueError("ERROR: writing to directory " + file_path)

        try:
            f_p = open(file_path, "w")
            return f_p.write(str(val))
        except BaseException:
            raise ValueError("ERROR writing to file " + file_path)
