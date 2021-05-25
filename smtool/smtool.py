#!/usr/bin/python
#
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
This module contains the core class for the tool.
User runs smtool.py with specific options
and the Smtool class contains various
methods to parse, validate user provided options
and invoke specific actions based on them.

The class also contains method to scan and report
the status of vulnerabilities to the user.
"""
import signal
import sys

from smtool_lib import Boothole
from smtool_lib import Parser
from smtool_lib import Host
from smtool_lib import Microcode
from smtool_lib import Distro
from smtool_lib import Server
from smtool_lib import Vulnerabilities


def cleanup(signum, frame):
    print("Received interrupt, exiting!")
    exit(0)


def setup_signal_handlers():
    """
    Catch ctrl-c and other signals that can cause this script to terminate,
    and exit after any cleanup.
    """
    signal.signal(signal.SIGHUP, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    return


def error(msg):
    """
    Logs error messages.

    """
    print("ERROR: " + msg)
    return


class Smtool(Parser):
    """
    Core class of the tool.
    Contains various methods to parse various
    user provided options and invoke specific
    actions based on them.

    Contains routine to scan the system, report
    the status of various mitigations and recommend
    any upgrades if required. Also contains helper
    routines to get variant type and highest microcode
    version required by scan routine.

    """

    boothole = None

    def get_variant_type(self, vname):
        """
        Returns specific variant type based
        on variant name.

        Parameters:
        vname(str): Variant name

        Returns: int: Variant type.

        """
        if vname == "Spectre V1":
            return self.SPECTRE_V1
        if vname == "Spectre V2":
            return self.SPECTRE_V2
        if vname == "Meltdown":
            return self.MELTDOWN
        if vname == "SSBD":
            return self.SSBD
        if vname == "L1TF":
            return self.L1TF
        if vname == "MDS":
            return self.MDS
        if vname == "ITLB_MULTIHIT":
            return self.ITLB_MULTIHIT
        if vname == "TSX_ASYNC_ABORT":
            return self.TSX_ASYNC_ABORT

    # Get the microcode version that supports mitigation for all
    # vulnerabilities
    def get_highest_microcode_ver(self, arr, n):
        """
        Get highest microcode version that
        supports fixes for all vulnerabilities.

        Parameters:
        arr(list): microcode versions.
        n(int): length of the list.

        Returns:
        str: Highest microcode version.

        """
        highest_ver = arr[0]

        for i in range(1, n):
            if arr[i] > highest_ver:
                highest_ver = arr[i]

        return highest_ver

    def scan_status(self):
        """
        Scans the current status of the server.
        Checks the current kernel, microcode versions and
        the status of vulnerabilities.

        Recommends any upgrade if needed.
        """
        h = self.host
        kernel = h.kernel
        vname = ""
        xen = False
        check_mitigation = True

        server_type = self.server.scan_server(self.distro)
        is_mitigated_sys = []
        is_mitigated_cmdline = []
        is_mitigated_kernel = []
        is_mitigated_cmdline_xen = []
        is_mitigated_kernel_xen = []
        is_enabled_runtime = False
        is_microcode_vulnerable = ""
        enabled_mitigation_list = ""
        enabled_mitigation_list_new = ""

        min_microcode_ver_arr = []
        variant_list = []
        variants = []
        require_microcode_update = False
        require_kernel_upgrade = False
        require_cmdline_update = False

        disabled_variants_cmdline = ""
        disabled_variants_kernel = ""
        recommended_ver = kernel.recommended_ver(kernel.get_kernel_desc())

        self.boothole = Boothole()

        if not h.is_vulnerable():
            print("System is not vulnerable")
            return

        if h.is_mitigated():
            print("Mitigations are in place for all cpu vulnerabilities")
            return

        list_vuln = h.get_vulnerabilities()

        h.vuln = Vulnerabilities(h)
        h.vuln.mitigation_options = []
        h.vuln.scan_vulnerabilities()

        if h.vuln.mitigation_options:
            for i in range(len(h.vuln.mitigation_options)):
                if (i % 2) == 0:
                    variant_type = self.get_variant_type(
                        h.vuln.mitigation_options[i].strip())
                    vname = h.vuln.mitigation_options[i].strip()
                    min_microcode_ver = self.microcode.\
                        get_min_microcode_version(variant_type)
                    if min_microcode_ver:
                        if (self.microcode.cur_microcode_ver <
                                min_microcode_ver):
                            variant_list.append(h.vuln.mitigation_options[i])
                            min_microcode_ver_arr.append(min_microcode_ver)
                else:
                    mitigation_opt = h.vuln.mitigation_options[i]
                    if mitigation_opt:
                        is_mitigated_kernel.append(vname + "," + "True")
                        if mitigation_opt[1]:
                            is_mitigated_cmdline.append(vname + "," + "True")
                            if mitigation_opt[0]:
                                is_mitigated_sys.append(vname + "," + "True")
                            else:
                                is_mitigated_sys.append(vname + "," + "False")
                                is_microcode_vulnerable += vname + ", "
                                require_microcode_update = True
                        else:
                            is_mitigated_cmdline.append(vname + "," + "False")
                            if mitigation_opt[0]:
                                enabled_mitigation_list += vname + ", "
                    else:
                        is_mitigated_kernel.append(vname + "," + "False")

        if enabled_mitigation_list:
            if enabled_mitigation_list.find("Spectre V2") != -1:
                is_enabled_runtime = True

        print("System is vulnerable to " + list_vuln[:-2])
        vuln_list = list_vuln[:-2].split(",")

        if ((self.server.stype == self.XEN_PV) or (
                self.server.stype == self.XEN_HYPERVISOR)):
            xen = True
            print("Mitigation is not available for Meltdown, "
                  "SSBD and MDS on this system")
            for vuln in vuln_list:
                if (vuln.strip() == "Spectre V2" or vuln.strip()
                        == "Spectre V1" or vuln.strip() == "L1TF"):
                    check_mitigation = True
                    break
                else:
                    check_mitigation = False

            if is_mitigated_cmdline:
                for i in range(0, len(is_mitigated_cmdline)):
                    if ((is_mitigated_cmdline[i].find("Spectre V2") != -1) or
                            (is_mitigated_cmdline[i].find("Spectre V2") !=
                             -1) or
                            (is_mitigated_cmdline[i].find("L1TF") != -1)):
                        is_mitigated_cmdline_xen.append(
                            is_mitigated_cmdline[i])

            if is_mitigated_kernel:
                for i in range(0, len(is_mitigated_kernel)):
                    if ((is_mitigated_kernel[i].find("Spectre V1") != -1) or
                            (is_mitigated_kernel[i].find("Spectre V2") != -1)
                            or (is_mitigated_kernel[i].find("L1TF") != -1)):
                        is_mitigated_kernel_xen.append(is_mitigated_kernel[i])

        if check_mitigation:
            if is_mitigated_cmdline:
                if xen:
                    if len(is_mitigated_cmdline_xen) != 0:
                        for i in range(0, len(is_mitigated_cmdline_xen)):
                            if is_mitigated_cmdline[i].find("False") != -1:
                                disabled_variants_cmdline += \
                                    is_mitigated_cmdline_xen[i]\
                                    .split(",")[0] + ","
                                require_cmdline_update = True
                else:
                    for i in range(0, len(is_mitigated_cmdline)):
                        if is_mitigated_cmdline[i].find("False") != -1:
                            disabled_variants_cmdline += \
                                is_mitigated_cmdline[i].split(",")[0] + ","
                            require_cmdline_update = True

        if check_mitigation:
            if is_mitigated_kernel:
                if xen:
                    if is_mitigated_kernel_xen:
                        for i in range(0, len(is_mitigated_kernel_xen)):
                            if (is_mitigated_kernel_xen[i].find(
                                    "False") != -1):
                                disabled_variants_kernel += \
                                    is_mitigated_kernel_xen[i].\
                                    split(",")[0] + ","
                                require_kernel_upgrade = True
                else:
                    for i in range(0, len(is_mitigated_kernel)):
                        if is_mitigated_kernel[i].find("False") != -1:
                            disabled_variants_kernel += \
                                is_mitigated_kernel[i].split(",")[0] + ","
                            require_kernel_upgrade = True

        if require_cmdline_update:
            print("Mitigation for the following variants disabled on "
                  "the cmdline: " + disabled_variants_cmdline[:-1])
            print("Please enable the mitigations for the above mentioned "
                  "variants using the tool.")
        if enabled_mitigation_list:
            if is_enabled_runtime:
                print("Runtime mitigation may be enabled for Spectre V2.")
                enabled_mitigation_list_new = enabled_mitigation_list.\
                    replace('Spectre V2', '')
            else:
                enabled_mitigation_list_new = enabled_mitigation_list
        if enabled_mitigation_list_new:
            print("Please note that the default mitigation will "
                  "always be enabled for the following: "
                  "" + enabled_mitigation_list_new[:-2].strip())

        if require_kernel_upgrade:
            print("Kernel is too old to support mitigations for "
                  "" + disabled_variants_kernel[:-1])
            if (kernel.ktype == 1) or (kernel.ktype == 2):
                print("Kernels older than UEK4 do not support mitigation "
                      "for SSBD.")
                print("Please upgrade the kernel to UEK4 version "
                      "4.1.12-124.33.2 to enable support for all "
                      "mitigations")
            else:
                print(
                    "Please upgrade the kernel to version " +
                    recommended_ver)

        if require_microcode_update:
            if (server_type == self.BARE_METAL or server_type ==
                    self.KVM_HOST or server_type == self.XEN_HYPERVISOR):
                if (min_microcode_ver_arr):
                    highest_ver = self.get_highest_microcode_ver(
                        min_microcode_ver_arr, len(min_microcode_ver_arr))
                if "Spectre V2 " in variant_list:
                    i = variant_list.index("Spectre V2 ")
                    variant_list[i] = "Spectre V2 (IBRS-based) "
                if xen:
                    for i in variant_list:
                        if ((i.find("Meltdown") != -1) or
                                (i.find("SSBD") != -1) or
                                (i.find("MDS") != -1)):
                            continue
                        else:
                            variants.append(i)
                        if variants:
                            print("Microcode is too old to support "
                                  "mitigation for " + ''.join(variants))
                            if (min_microcode_ver_arr):
                                print("Please upgrade the microcode to "
                                      "version " + str(hex(highest_ver)))
                            else:
                                print("Please upgrade the microcode to "
                                      "the latest version")
                print("Microcode is too old to support "
                      "mitigation for " + ''.join(variant_list))
                if (min_microcode_ver_arr):
                    print("Please upgrade the microcode to "
                          "version " + str(hex(highest_ver)))
                else:
                    print("Please upgrade the microcode to "
                          "the latest version.")
            elif (server_type == self.KVM_GUEST or server_type ==
                  self.XEN_PV or server_type == self.XEN_HVM):
                print("Please check if the host microcode "
                      "is uptodate for " + is_microcode_vulnerable[:-2])
                if (server_type == self.KVM_GUEST):
                    print("Also please verify if the host is running "
                          "QEMU version 2.9 and above")
                else:
                    print("Also please verify if Dom0 is running "
                          "the latest xen version")

    def __init__(self, argv):
        """
        Init function for the Smtool class.

        Invokes specific routines to scan, enable and disable
        various vulnerabilities based on various user
        provided options on running the tool.

        Parameters:
        argv(str): User provided option.

        """
        setup_signal_handlers()

        if self.parse_options(argv) is False:
            raise ValueError("ERROR: parsing objects")

        if self.validate_options() is False:
            raise ValueError("ERROR: validating options")

        try:
            self.host = Host()
            self.distro = Distro(False)                  # Oracle distro object
            # Baremetal, hypervisor, VM
            self.server = Server(self.distro, False)

            self.microcode = Microcode()
            self.host.scan_host()
            if not self.host.is_vulnerable():
                print("This system is not vulnerable. Nothing to be done")
            if self.scan_only:
                self.scan_status()
                return
            if self.disable_all:
                self.host.disable_mitigations(
                    self.dry_run, self.runtime, self.yes)
            if self.enable_full:
                self.host.enable_mitigations(
                    self.dry_run, self.runtime, self.yes)
            if self.enable_default:
                self.host.reset_mitigations(self.dry_run, self.yes)
        except ValueError as err:
            print(err)
            sys.exit(2)


# main
try:
    SMT = Smtool(sys.argv)
except ValueError as err:
    sys.exit(2)
