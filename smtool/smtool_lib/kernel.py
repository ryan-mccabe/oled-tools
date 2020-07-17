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
Module contains methods to identify
and validate various kernel versions.

"""
import re
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


class Kernel(Base):
    """
    Contains various methods to identify, set,
    validate the kernel type and recommend the kernel
    version that supports all mitigations.

    """
    kern_ver_cmd = ["uname -r"]
    ktype = None
    kver = None

    UNKNOWN = 0
    UEK2 = 1
    UEK3 = 2
    UEK4 = 3
    UEK5 = 4
    RHCK6 = 5
    RHCK7 = 6
    RHCK8 = 7
    desc = ['UNKNOWN', 'UEK2', 'UEK3', 'UEK4', 'UEK5', 'RHCK6', 'RHCK7',
            'RHCK8']

    def recommended_ver(self, kernel_ver):
        """
        Identifies recommended kernel version based
        on the kernel type.

        Parameters:
        kernel_ver(str): Kernel type.

        Returns:
        str: Latest kernel version based on the
        specific kernel type.

        """
        if kernel_ver == "UEK2":
            return "2.6.39-400.316.1"
        elif kernel_ver == "UEK3":
            return "3.8.13-118.40.1"
        elif kernel_ver == "UEK4":
            return "4.1.12-124.33.2"
        elif kernel_ver == "UEK5":
            return "4.14.35-1902.6.7"
        elif kernel_ver == "RHCK6":
            return "2.6.32-754.25.1"
        elif kernel_ver == "RHCK7":
            return "3.10.0-1062.4.2"
        elif kernel_ver == "RHCK8":
            return "4.18.0-147"

    def get_kernel_desc(self):
        """
        Gets kernel description based on the type.

        Returns:
        str: String based on specific kernel type.

        """
        return self.desc[self.ktype]

    def get_kernel(self):
        """
        Gets kernel version.

        Returns:
        str: Specific kernel version"

        """
        return self.kver

    def is_valid(self):
        """
        Validates kernel version.

        Returns:
        bool: True if version is supported by the tool, else
        returns False.

        """
        if (self.ktype in [self.UEK4, self.UEK5, self.UEK2,
                           self.UEK3, self.RHCK6, self.RHCK7, self.RHCK8]):
            return True
        logn("Tool currently doesn't support kernel " + self.desc[self.ktype])

        return False

    def set_kernel_version(self):
        """
        Updates the kver variable to the running kernel version.

        """
        self.ktype = self.UNKNOWN
        self.kver = self.run_command(self.kern_ver_cmd, True)

    def set_kernel_type(self, ver):
        """
        Gets kernel version.

        Returns:
        str: Specific kernel version"

        """
        self.kver = ver.split()[0]
        if re.search("^2.6.39", self.kver) is not None:
            self.ktype = self.UEK2

        if re.search("^3.8.13", self.kver) is not None:
            self.ktype = self.UEK3

        if re.search("^4.1.12", self.kver) is not None:
            self.ktype = self.UEK4

        if re.search("^4.14.35", self.kver) is not None:
            self.ktype = self.UEK5

        if re.search("^2.6.32", self.kver) is not None:
            self.ktype = self.RHCK6

        if re.search("^3.10.0", self.kver) is not None:
            self.ktype = self.RHCK7

        if re.search("^4.18.0", self.kver) is not None:
            self.ktype = self.RHCK8

        return


    def __init__(self, server):
        """
        Init function for kernel class.
        Identifies/validates specific kernel type.

        Parameters:
        server(int): Server type.

        """
        log("           running kernel..........:")
        if not server.is_valid():
            raise ValueError("Invalid server")

        self.set_kernel_version()
        self.set_kernel_type(self.get_kernel())
        if not self.is_valid():
            raise ValueError("Invalid kernel " + self.get_kernel())
        logn(self.get_kernel_desc() + " (" + self.get_kernel() + ")")
        return
