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
Module contains various methods to
identify and validate the server type.

"""
import parser
from base import Base


def log(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if parser.VERBOSE:
        print msg,
    return


def logn(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if parser.VERBOSE:
        print msg
    return


def error(msg):
    """
    Logs error messages.

    """
    print "ERROR: " + msg
    return


# Server
class Server(Base):
    """
    Identifies server type.
    Contains methods to scan and validate the type of server.

    """
    stype = None

    def get_server(self):
        """
        Method to get server type.

        Returns:
        str: server type.

        """
        return self.sdesc[self.stype]

    def scan_server(self, distro):
        """
        Identifies the type of server.
        Uses virt-what command to do so.

        Parameters:
        distro (int): distro type.

        Returns:
        int: server type.

        """
        if distro.is_ovm():
            return self.XEN_HYPERVISOR

        cmd = ["virt-what"]
        out = self.run_command(cmd, True)
        server_type = out.splitlines()

        if not server_type:
            cmd = ["egrep vmx /proc/cpuinfo"]
            out = self.run_command(cmd, True)
            if not out is None:
                cmd = ["lsmod | grep kvm"]
                run = self.run_command(cmd, True)
                if run != "":
                    return self.KVM_HOST
                else:
                    return self.BARE_METAL
        elif server_type[0] == "xen":
            if server_type[1] == "xen-hvm":
                return self.XEN_HVM
            if server_type[1] == "xen-domU":
                return self.XEN_PV
        elif server_type[0] == "kvm":
            return self.KVM_GUEST

        return self.UNKNOWN

    def is_valid(self):
        """
        Validates server type.

        Returns:
        bool: True if server type is valid,
        else returns False.

        """
        if (self.stype in [self.BARE_METAL, self.XEN_HYPERVISOR, self.XEN_PV,
                           self.XEN_HVM, self.KVM_HOST, self.KVM_GUEST]):
            return True

        return False

    def get_server_type(self):
        """
        Function to get server type.

        Returns:
        str: server type.

        """
        if not self.is_valid():
            return ""

        return self.sdesc[self.stype]

    def __init__(self, distro, is_log):
        """
        Init function for server class.
        Validates distribution type and identifies
        server type.

        Parameters:
        distro(int): Type of distribution.

        """
	if (is_log is True):
        	log("           server type.............:")
        if not distro.is_valid():
            raise ValueError("ERROR: Unsupported Linux Distribution")

        self.stype = self.scan_server(distro)
        if not self.is_valid():
            raise ValueError("ERROR: Invalid server type")
	if (is_log is True):
        	logn(str(self.get_server()))
        return
