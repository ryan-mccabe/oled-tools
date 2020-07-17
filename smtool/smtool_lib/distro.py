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
Module contains class Distro which
lists various distributions supported by the tool,
identify the type of distribution that the
server is running and validate it.

"""
import os
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


class Distro(Base):
    """
    Contains methods to validate and find
    the type of distribution that the
    server is running.

    """
    UNKNOWN = 0
    OL6 = 1
    OL7 = 2
    OL8 = 3
    RHEL6 = 4
    RHEL7 = 5
    RHEL8 = 6
    OVM32 = 7
    OVM33 = 8
    OVM34 = 9
    OVM40 = 10
    desc = ["UNKNOWN", "Oracle Linux 6", "Oracle Linux 7", "Oracle Linux 8",
            "Red Hat 6", "Red Hat 7", "Red Hat 8",
            "Oracle VM 3.2", "Oracle VM 3.3", "Oracle VM 3.4", "Oracle VM 4.0"]
    oracle_release_file = "/etc/oracle-release"
    redhat_release_file = "/etc/redhat-release"
    ovs_release_file = "/etc/ovs-release"
    error = ""

    dtype = None

    def read_release_file(self):
        """
        Reads release file to identify
        the type of distribution -
        OVS, Redhat, UEK

        """
        cmd = ["uname -r"]
        out = self.run_command(cmd, True)

        if os.path.exists(self.ovs_release_file):
            return self.read_file(self.ovs_release_file)

        if out.find("uek") != -1:
            if os.path.exists(self.oracle_release_file):
                return self.read_file(self.oracle_release_file)
        else:
            if os.path.exists(self.redhat_release_file):
                return self.read_file(self.redhat_release_file)

        print "Unknown Release"

        return None

    def scan_distro(self):
        """
        Scans the release file and identifies
        that the tool can be run with.

        Returns: int: type of distribution.

        """
        out = self.read_release_file()
        if out is None:
            return self.UNKNOWN

        tmp = out.split()
        if tmp[0] == "Oracle":
            if tmp[1] not in ["Linux", "VM"]:
                return self.UNKNOWN

            if tmp[1] == "Linux":
                if tmp[4] < "6.0" or tmp[4] >= "9.0":
                    return self.UNKNOWN
                if tmp[4] > "8.0":
                    return self.OL8
                if tmp[4] > "7.0":
                    return self.OL7
                if tmp[4] > "6.0":
                    return self.OL6

            if tmp[1] == "VM":
                if tmp[4] < "3.2" or tmp[4] >= "5.0":
                    return self.UNKNOWN
                if tmp[4] >= "4.0":
                    return self.OVM40
                if tmp[4] >= "3.4":
                    return self.OVM34
                if tmp[4] >= "3.3":
                    return self.OVM33
                if tmp[4] >= "3.2":
                    return self.OVM32

        if tmp[0] == "Red" and tmp[1] == "Hat":
            if tmp[6] < "6.0" or tmp[6] >= "9.0":
                return self.UNKNOWN

            if tmp[6] >= "8.0":
                return self.RHEL8

            if tmp[6] >= "7.0":
                return self.RHEL7

            if tmp[6] >= "6.0":
                return self.RHEL6

        return self.UNKNOWN

    def is_valid(self):
        """
        Validates distribution type.

        Returns: bool: True if distro is valid,
        False if distro is invalid.

        """
        if (self.dtype in [self.OL6, self.OL7, self.OL8, self.OVM34,
                           self.OVM40, self.RHEL6, self.RHEL7, self.RHEL8]):
            return True

        return False

    def is_ovm(self):
        """
        Validates if the distro is OVM

        Returns: True if distro is OVM, else
        returns False.

        """
        if self.dtype in [self.OVM32, self.OVM33, self.OVM34, self.OVM40]:
            return True

        return False

    def get_distro(self):
        """
        Gets distribution type.

        Returns: str: Distro type.

        """
        return self.desc[self.dtype]

    def __init__(self, is_log):
        """
        Init function for distro class
        Scans, identifies and validates the type
        of distribution that the server is running.

        """
	if (is_log is True):
        	log(" Scanning distribution....................:")
        self.dtype = self.scan_distro()
        if not self.is_valid():
            raise ValueError("ERROR: Unsupported Linux Distribution")
	if (is_log is True):
        	logn(self.get_distro())
        return
