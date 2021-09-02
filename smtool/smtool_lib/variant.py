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
Module contains class Variant which
contains various methods to check for
mitigations and enable/disable mitigations
for different variants at boot and runtime.

It also scans the system for various
vulnerabilities and thier status and
recommends upgrades if any.

"""
import os
import sys

if (sys.version_info[0] == 3):
    from . import parser

    from .base import Base
    from .boot import Boot
    from .cpu import Cpu
    from .distro import Distro
    from .server import Server
    from .sysfile import Sysfile
else:
    import parser

    from base import Base
    from boot import Boot
    from cpu import Cpu
    from distro import Distro
    from server import Server
    from sysfile import Sysfile


def log(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if parser.VERBOSE:
        print(msg)
    return


def error(msg):
    """
    Logs error messages.

    """
    print("ERROR: " + msg)
    return


class Variant(Base):
    """
    Class contains various methods to check for
    mitigations and enable/disable mitigations
    for different variants at boot and runtime.

    """
    host = None
    boot = None
    server = None
    distro = None
    vtype = None
    vname = None
    sysfile = None
    cpu = None
    variant_type = None

    vulnerable = None
    mitigated_kernel = None
    mitigated_boot = None
    mitigated_sys = None
    mitigation_possible = None
    mitigation_str = []
    variant_list = []

    def check_mitigations(self):
        """
        Checks if kernel supports mitigation and if
        the mitigation is enabled/disabled at boot time.

        """
        self.mitigated_kernel = True

        if (os.path.exists(self.sysfile.get_sysfile()) and self.sysfile.is_mitigated()):
            self.mitigated_sys = True

        vuln_string = self.boot.scan_cmdline()
        if (self.vname == "TSX_Async_Abort"):
            if (vuln_string.find("tsx_async_abort=off") != -1):
                self.mitigated_boot = None
            else:
                self.mitigated_boot = True
        else:
            if (vuln_string.find("no") != -1) or (vuln_string.find("off") != -1):
                self.mitigated_boot = None
            else:
                self.mitigated_boot = True
        return

    def disable_variant_boot(self):
        """
        Invokes function to disable mitigation
        for the specific variant at boot time.

        """
        self.boot.disable_mitigation(self)
        return

    def enable_variant_boot(self):
        """
        Invokes function to enable full mitigation
        for the specific variant at boot time.

        """
        self.boot.enable_mitigation(self)
        return

    def disable_variant_runtime(self, yes):
        """
        Allows the user to disable mitigation
        for different variants at run time.

        Parameters:
        yes(bool): If set to True, use the
        default runtime option to disable
        mitigation at runtime.

        """
        self.sysfile = Sysfile(self.vtype)
        self.cpu = Cpu()
        kernel_version = self.sysfile.read_kernel_ver()
        is_kvm = self.sysfile.is_kvm()

        if self.vtype == 2:
            spectre_v2_arr = self.sysfile.read_runtime_files(self.vtype)
            if not spectre_v2_arr:
                return

            len_arr = len(spectre_v2_arr)
            if kernel_version == "RHCK6":
                len_arr = 1
            if kernel_version == "RHCK7":
                len_arr = 2

            for i in range(len_arr):
                if kernel_version.find("UEK") != -1:
                    if self.cpu.is_skylake():
                        if (i == 2) or (i == 3):
                            continue
                    else:
                        if i == 0:
                            continue

                if (i == 0) or (i == 1):
                    if self.sysfile.is_ibrs_tunable() is False:
                        continue

                if not yes:
                    if kernel_version.find("RHCK") != -1:
                        print("Enter 0 to disable mitigation")
                        option = raw_input(
                            self.sysfile.runtime_files_array_RHCK[int(i)] +
                            ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    int(i), option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array_RHCK[int(i)]
                                + ": ")
                    else:
                        print("Please enter 0 to disable mitigation")
                        option = raw_input(
                            self.sysfile.runtime_files_array[int(i)] + ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    int(i), option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array[int(i)] +
                                ": ")
                        if kernel_version.find("RHCK") != -1:
                            self.write_file(
                                self.sysfile.runtime_files_array_RHCK[int(i)],
                                str(option))
                        else:
                            self.write_file(
                                self.sysfile.runtime_files_array[int(i)],
                                str(option))
                else:
                    if kernel_version.find("RHCK") != -1:
                        self.write_file(
                            self.sysfile.runtime_files_array_RHCK[int(i)], '0')
                    else:
                        self.write_file(
                            self.sysfile.runtime_files_array[int(i)], '0')

        if (self.vtype == 4) and (kernel_version.find("RHCK") != -1):
            if os.path.isfile(self.sysfile.runtime_files_array[3]):
                if not yes:
                    print("Enter 0 to disable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array_RHCK[3] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                3, option, kernel_version)):
                        print("Please enter a valid option")
                    option = raw_input(
                        self.sysfile.runtime_files_array_RHCK[3] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array_RHCK[3], str(option))
                else:
                    self.write_file(
                        self.sysfile.runtime_files_array_RHCK[3], '0')

        # For l1tf, the array elements/indices for RHCK and UEK are the same,
        # the options are also the same
        # So will not alter the below code for RHCK kernels
        if self.vtype == 5:
            smt_list = ["forceoff", "notsupported"]
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[4]):
                    if (self.read_file(
                            self.sysfile.runtime_files_array[4])
                            not in smt_list):
                        print("Enter on to enable SMT")
                        option = raw_input(
                            self.sysfile.runtime_files_array[4] + ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    4, option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array[4] + ": ")
                        self.write_file(
                            self.sysfile.runtime_files_array[4], str(option))
                if os.path.isfile(self.sysfile.runtime_files_array[5]):
                    print("Enter never to disable L1D flush mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[5] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                5, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[5] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[5], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[4]):
                    if (self.read_file(
                            self.sysfile.runtime_files_array[4])
                            not in smt_list):
                        self.write_file(
                            self.sysfile.runtime_files_array[4], 'on')
                if os.path.isfile(self.sysfile.runtime_files_array[5]):
                    self.write_file(
                        self.sysfile.runtime_files_array[5], 'never')

        # mds control files don't exists for RHCK kernels
        if (self.vtype == 6) and (kernel_version.find("UEK") != -1):
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[6]):
                    print("Enter 0 to disable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[6] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                6, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[6] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[6], str(option))
                if os.path.isfile(self.sysfile.runtime_files_array[7]):
                    print("Enter 0 to disable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[7] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                7, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[7] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[7], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[6]):
                    self.write_file(
                        self.sysfile.runtime_files_array[6], '0')
                if os.path.isfile(self.sysfile.runtime_files_array[7]):
                    self.write_file(
                        self.sysfile.runtime_files_array[7], '0')

        # itlb_multihit control files
        if (self.vtype == 7) and is_kvm:
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[8]):
                    print("Enter off to disable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[8] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                8, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[8] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[8], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[8]):
                    self.write_file(
                        self.sysfile.runtime_files_array[8], 'off')
        return

    def enable_variant_runtime(self, yes):
        """
        Allows the user to enable mitigation
        for the different variants at run time.

        Parameters:
        yes(bool): If set to True, use the
        default runtime option to enable
        mitigation at runtime.

        """
        self.sysfile = Sysfile(self.vtype)
        self.cpu = Cpu()
        kernel_version = self.sysfile.read_kernel_ver()
        is_kvm = self.sysfile.is_kvm()

        if self.vtype == 2:
            spectre_v2_arr = self.sysfile.read_runtime_files(self.vtype)
            if not spectre_v2_arr:
                return
            len_arr = len(spectre_v2_arr)
            if kernel_version == "RHCK6":
                len_arr = 1
            if kernel_version == "RHCK7":
                len_arr = 2

            for i in range(len_arr):
                if (i == 0) or (i == 1):
                    if self.sysfile.is_ibrs_tunable() is False:
                        continue
                if self.sysfile.read_kernel_ver().find("UEK") != -1:
                    if self.cpu.is_skylake():
                        if (i == 2) or (i == 3):
                            continue
                    else:
                        if i == 0:
                            continue
                if not yes:
                    if kernel_version.find("RHCK") != -1:
                        if (i == 0):
                            if (kernel_version == "RHCK6"):
                                print("Please enter 1,2 or 3 to "
                                      "enable mitigation")
                            elif (kernel_version == "RHCK7"):
                                print("Please enter 1,2,3 or 4 to "
                                      "enable mitigation")
                        else:
                            print("Please enter 1 to enable mitigation")
                        option = raw_input(
                            self.sysfile.runtime_files_array_RHCK[int(i)] +
                            ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    int(i), option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array_RHCK[int(i)] +
                                ": ")
                        self.write_file(
                            self.sysfile.runtime_files_array_RHCK[int(i)],
                            str(option))
                    else:
                        print("Please enter 1 to enable mitigation")
                        option = raw_input(
                            self.sysfile.runtime_files_array[int(i)] +
                            ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    int(i), option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array[int(i)] +
                                ": ")
                        self.write_file(
                            self.sysfile.runtime_files_array[int(i)],
                            str(option))
                else:
                    if kernel_version.find("RHCK") != -1:
                        self.write_file(
                            self.sysfile.runtime_files_array_RHCK[int(i)], '1')
                    else:
                        self.write_file(
                            self.sysfile.runtime_files_array[int(i)], '1')

        if (self.vtype == 4) and (kernel_version.find("RHCK") != -1):
            if os.path.isfile(self.sysfile.runtime_files_array[3]):
                if not yes:
                    print("Please enter 1 to enable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array_RHCK[3] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                3, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array_RHCK[3] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array_RHCK[3], str(option))
                else:
                    if kernel_version == "RHCK6":
                        self.write_file(
                            self.sysfile.runtime_files_array_RHCK[3], '3')
                    elif kernel_version == "RHCK7":
                        self.write_file(
                            self.sysfile.runtime_files_array_RHCK[3], '4')

        # For l1tf, the array elements/indices for RHCK and UEK are the same,
        # the options are also the same
        # So will not alter the below code for RHCK kernels
        if self.vtype == 5:
            smt_list = ["forceoff", "notsupported"]
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[4]):
                    if (self.read_file(
                            self.sysfile.runtime_files_array[4])
                            not in smt_list):
                        print("Enter off or forceoff to disable SMT")
                        option = raw_input(
                            self.sysfile.runtime_files_array[4] + ": ")
                        while (
                                not self.sysfile.is_option_valid(
                                    4, option, kernel_version)):
                            print("Please enter a valid option")
                            option = raw_input(
                                self.sysfile.runtime_files_array[4] + ": ")
                        self.write_file(
                            self.sysfile.runtime_files_array[4], str(option))
                if os.path.isfile(self.sysfile.runtime_files_array[5]):
                    print("Enter cond or always to enable L1D flush mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[5] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                5, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[5] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[5], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[4]):
                    if (self.read_file(
                            self.sysfile.runtime_files_array[4])
                            not in smt_list):
                        self.write_file(
                            self.sysfile.runtime_files_array[4], 'off')
                if os.path.isfile(self.sysfile.runtime_files_array[5]):
                    self.write_file(
                        self.sysfile.runtime_files_array[5], 'cond')

        if (self.vtype == 6) and (kernel_version.find("UEK") != -1):
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[6]):
                    print("Enter 1 to enable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[6] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                6, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[6] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[6], str(option))
                if os.path.isfile(self.sysfile.runtime_files_array[7]):
                    print("Enter 1 to enable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[7] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                7, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[7] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[7], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[6]):
                    self.write_file(
                        self.sysfile.runtime_files_array[6], '1')
                if os.path.isfile(self.sysfile.runtime_files_array[7]):
                    self.write_file(
                        self.sysfile.runtime_files_array[7], '1')

        # itlb_multihit control files
        if (self.vtype == 7) and is_kvm:
            if not yes:
                if os.path.isfile(self.sysfile.runtime_files_array[8]):
                    print("Enter force or auto to enable mitigation")
                    option = raw_input(
                        self.sysfile.runtime_files_array[8] + ": ")
                    while (
                            not self.sysfile.is_option_valid(
                                8, option, kernel_version)):
                        print("Please enter a valid option")
                        option = raw_input(
                            self.sysfile.runtime_files_array[8] + ": ")
                    self.write_file(
                        self.sysfile.runtime_files_array[8], str(option))
            else:
                if os.path.isfile(self.sysfile.runtime_files_array[8]):
                    self.write_file(
                        self.sysfile.runtime_files_array[8], 'force')
        return

    def reset_variant_boot(self):
        """
        Invokes function to enable default mitigation
        for the specific variant at boot time.

        """
        self.boot.reset_mitigation(self)
        return

    def display(self):
        """
        Displays the mitigation status of each variant.

        """
        print("     Variant      : " + self.vname)
        if self.sysfile is None:
            return
        print("       File       : " + self.sysfile.get_sysfile())
        print("       Mitigated  : kernel=" + str(self.mitigated_kernel))
        print(", Boot=")
        print(str(self.mitigated_boot) + ", sys=" + str(self.mitigated_sys))
        if self.boot.boot_on:
            print("       boot on    : True")
        if self.boot.boot_off:
            print("       boot off   : True")
        if self.boot.grub_on:
            print("       grub on    : True")
        if self.boot.grub_off:
            print("       grub off   : True")

    def is_mitigated(self):
        """
        Checks if mitigation is in place for specific variant.

        Returns:
        bool: True if mitigation is in place, else returns False.

        """
        cpu = self.host.cpu
        server = self.host.server
        if (cpu.is_vulnerable(self.vtype)) and (not self.mitigated_kernel):
            return False
        if ((server.stype == self.XEN_PV) or (
                server.stype == self.XEN_HVM) or
                (server.stype == self.KVM_GUEST)):
           if (os.path.exists(self.sysfile.get_sysfile()) and not self.sysfile.is_mitigated()):
               return False
        else:
            if ((cpu.is_vulnerable(self.vtype)) and (os.path.exists(self.sysfile.get_sysfile())
                and not self.sysfile.is_mitigated())):
                return False
        return True

    def is_mitigation_possible(self):
        """
        Checks if mitigation can be enabled for a specific variant based
        on server type.

        Returns:
        bool: True if mitigation can be enabled, else returns False.

        """
        cpu = self.host.cpu
        server = self.host.server
        self.sysfile = Sysfile(self.vtype)
        if not cpu.is_vulnerable(self.vtype):
            return True

        if ((server.stype == self.XEN_PV) or (
                server.stype == self.XEN_HYPERVISOR)):
            if (self.vtype == self.MELTDOWN or self.vtype == self.SSBD or
                    self.vtype == self.MDS):
                return False

            if self.vtype == self.L1TF:
                if not os.path.exists(self.sysfile.get_sysfile()):
                    return False

        return True

    def scan_variant(self):
        """
        Scans sysfiles, grub and commandline to check mitigation
        status for various variants and reports status.
        Also recommends upgrades if any.

        """
        log("     scanning variant..............: '" + str(self.vname) + "'")
        cpu = self.host.cpu
        kernel = self.host.kernel
        self.distro = Distro(False)                  # Oracle distro object
        # Baremetal, hypervisor, VM
        self.server = Server(self.distro, False)

        mitigation_possible = self.is_mitigation_possible()
        if cpu.is_vulnerable(self.vtype):
            self.vulnerable = True
            log("        CPU........................: Vulnerable")
        else:
            self.vulnerable = False
            log("        CPU........................: Not Vulnerable")

        self.sysfile = Sysfile(self.vtype)
        if os.path.exists(self.sysfile.get_sysfile()):
            log("        Running kernel.............: Supports Mitigation")
            self.sysfile.scan_sysfile()
            self.boot = Boot(self.vtype, kernel.kver)
            # Does grub really needs to be scanned?
            self.boot.scan_grub()
            self.check_mitigations()
            self.mitigation_str = [self.mitigated_sys, self.mitigated_boot]
        else:
            if mitigation_possible is False:
                server_type = ""
                if self.server.stype == 2:
                    server_type = "Xen Hypervisor"
                elif self.server.stype == 3:
                    server_type = "Xen PV Guest"
                log(server_type + " doesn't support mitigation" +
                     " for MDS, SSBD and Meltdown")
            else:
                log("        Running kernel.............: Doesn't support" +
                     " mitigation")
            return False
        return True

    def __init__(self, vtype, host):
        """
        Init function for variant class.

        Initializes vulnerability type, host
        and variant name.

        Parameters:
        vtype(int): Vulnerability type.
        host(class): instance of host class.

        """
        self.vtype = vtype
        self.host = host
        self.vname = self.vdesc[vtype]
