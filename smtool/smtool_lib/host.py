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
Contains Host class which initializes and validates
various host parameters.

Contains methods to check if the host is vulnerable to
various variants and also contains methods to scan, enable
and disable vulnerabilities.

"""
import parser

from distro import Distro
from cpu import Cpu
from kernel import Kernel
from server import Server
from vulnerabilities import Vulnerabilities


VERBOSE = False  # type: bool


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


class Host:
    """
    Contains methods to initialize various host parameters
    including distribution type, kernel, cpu and microcode
    versions.

    Contains methods to check if the host is vulnerable to
    various variants and also contains methods to scan, enable
    and disable vulnerabilities.

    """
    distro = server = kernel = cpu = vuln = None
    scan = True

    def is_vulnerable(self):
        """
        Checks if host is vulnerable to any variants.

        Returns:
        bool: True if host is vulnerable, else
        return False.

        """
        if self.vuln is None:
            return False
        return True

    def is_mitigated(self):
        """
        Checks if all known vulnerabilities are mitigated
        on the server.

        Returns:
        bool: True if host is protected from all vulnerabilities,
        else returns False.

        """
        if self.vuln is None:
            return True

        vuln = self.vuln
        if vuln.is_mitigated():
            return True

        return False

    def get_vulnerabilities(self):
        """
        Function to get a string that contains
        variants that the system is vulnerable to.

        Returns:
        str: list of vulnerabilities.

        """
        return self.vuln.get_vulnerabilities()

    def disable_mitigations(self, dry_run, runtime, yes):
        """
        Invokes methods to disable mitigations at boot
        and runtime.

        Parameters:
        dry_run(bool): True if user specifies "-d" option,
        else False.
        runtime(bool): True if user specifies "-r" option,
        else False.
        yes(bool): True if user specifies "-y" option, else
        False.

        """
        logn("disabling mitigations")
        if runtime:
            self.vuln.enable_vulnerabilities_runtime(yes)
        else:
            self.vuln.enable_vulnerabilities(dry_run, yes)
        return

    def enable_mitigations(self, dry_run, runtime, yes):
        """
        Invokes methods to enable mitigations at boot
        and runtime.

        Parameters:
        dry_run(bool): True if user specifies "-d" option,
        else False.
        runtime(bool): True if user specifies "-r" option,
        else False.
        yes(bool): True if user specifies "-y" option, else
        False.

        """
        logn("enabling mitigation")
        if runtime:
            self.vuln.disable_vulnerabilities_runtime(yes)
        else:
            self.vuln.disable_vulnerabilities(dry_run, yes)
        return

    def reset_mitigations(self, dry_run, yes):
        """
        Invokes methods to enable default mitigations at boot
        time.

        Parameters:
        dry_run(bool): True if user specifies "-d" option,
        else False.
        yes(bool): True if user specifies "-y" option, else
        False.

        """
        logn("reset mitigation")
        self.vuln.reset_vulnerabilities(dry_run, yes)
        return

    def scan_host(self):
        """
        Invokes method to scan the host for various
        vulnerabilities.

        """
        logn("Scanning Host.......................")

        self.vuln = Vulnerabilities(self)

        self.vuln.scan_vulnerabilities()

        return

    def __init__(self):
        """
        Init method for host class.
        Invokes init methods to identify and validate
        the type of distribution, server, cpu family and
        kernel version.

        """
        logn("Initializing host")
        self.distro = Distro(True) 			# Oracle distro object
        if not self.distro.is_valid():
            raise ValueError("Invalid Distribution")

        self.server = Server(self.distro, True)  # Baremetal, hypervisor, VM
        if not self.server.is_valid():
            raise ValueError("Unsupported System")

        self.kernel = Kernel(self.server)  # Running kernel
        if not self.kernel.is_valid():
            raise ValueError("Unsupported Kernel")

        self.cpu = Cpu()  # Running cpu info
        if not self.cpu.is_valid():
            raise ValueError("Unsupported CPU")
