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
Module contains Sysfile class which lists various sysfiles
used to report the status of the mitigations. Also lists
various sysfiles that can be tuned at runtime to enable/disable
specific mitigations.

Contains routines to read and write sysfiles.

"""
import os
import parser

from base import Base
from distro import Distro
from kernel import Kernel
from server import Server


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


class Sysfile(Base):
    """
    Sysfile class contains paths to various status and runtime files.
    Lists valid options for each sysfile.
    Also contains methods to scan various sysfiles and read their
    contents.

    """

    # Variant mitigation status files
    SYS_SPECTRE_V1_FILE = "/sys/devices/system/cpu/vulnerabilities/spectre_v1"
    SYS_SPECTRE_V2_FILE = "/sys/devices/system/cpu/vulnerabilities/spectre_v2"
    SYS_L1TF_FILE = "/sys/devices/system/cpu/vulnerabilities/l1tf"
    SYS_MELTDOWN_FILE = "/sys/devices/system/cpu/vulnerabilities/meltdown"
    SYS_SSBD_FILE = "/sys/devices/system/cpu/vulnerabilities/spec_store_bypass"
    SYS_MDS_FILE = "/sys/devices/system/cpu/vulnerabilities/mds"
    SYS_ITLB_MULTIHIT_FILE = \
        "/sys/devices/system/cpu/vulnerabilities/itlb_multihit"
    SYS_TSX_ASYNC_ABORT_FILE = \
        "/sys/devices/system/cpu/vulnerabilities/tsx_async_abort"

    # SMT Status file
    SYS_SMT_ACTIVE_FILE = "/sys/devices/system/cpu/smt/active"

    # Mitigation runtime files
    SYS_IBRS_ENABLED_FILE = "/sys/kernel/debug/x86/ibrs_enabled"
    SYS_IBPB_ENABLED_FILE = "/sys/kernel/debug/x86/ibpb_enabled"
    SYS_RETPOLINE_FILE = "/sys/kernel/debug/x86/retp_enabled"
    SYS_RETPOLINE_ENABLED_FILE = "/sys/kernel/debug/x86/retpoline_enabled"
    SYS_RETPOLINE_FALLBACK_FILE = "/sys/kernel/debug/x86/retpoline_fallback"
    SYS_SSBD_ENABLED_FILE = "/sys/kernel/debug/x86/ssbd_enabled"
    SYS_SMT_CONTROL_FILE = "/sys/devices/system/cpu/smt/control"
    SYS_VMENTRY_L1D_FLUSH_FILE = \
        "/sys/module/kvm_intel/parameters/vmentry_l1d_flush"
    SYS_MDS_IDLE_CLEAR_FILE = "/sys/kernel/debug/x86/mds_idle_clear"
    SYS_MDS_USER_CLEAR_FILE = "/sys/kernel/debug/x86/mds_user_clear"
    SYS_ITLB_MULTIHIT_CTRL_FILE = "/sys/module/kvm/parameters/nx_huge_pages"

    runtime_files_array = [
        SYS_IBRS_ENABLED_FILE,
        SYS_IBPB_ENABLED_FILE,
        SYS_RETPOLINE_ENABLED_FILE,
        SYS_RETPOLINE_FALLBACK_FILE,
        SYS_SMT_CONTROL_FILE,
        SYS_VMENTRY_L1D_FLUSH_FILE,
        SYS_MDS_IDLE_CLEAR_FILE,
        SYS_MDS_USER_CLEAR_FILE,
        SYS_ITLB_MULTIHIT_CTRL_FILE]

    runtime_files_array_RHCK = [
        SYS_IBRS_ENABLED_FILE,
        SYS_RETPOLINE_FILE,
        SYS_IBPB_ENABLED_FILE,
        SYS_SSBD_ENABLED_FILE,
        SYS_SMT_CONTROL_FILE,
        SYS_VMENTRY_L1D_FLUSH_FILE]

    runtime_files_options = [
        [
            "0", "1"], [
                "0", "1", "2"], [
                    "0", "1"], [
                        "0", "1"], [
                            "on", "off", "forceoff"], [
                                "always", "cond", "never"], [
                                    "0", "1"], [
                                        "0", "1"], [
                                            "auto", "off", "force"]]

    runtime_files_options_RHCK6 = [["0", "1", "2", "3"], ["0", "1"],
                                   ["0", "1"], ["0", "1", "2"],
                                   ["on", "off", "forceoff"],
                                   ["always", "cond", "never"]]

    runtime_files_options_RHCK7 = [
        [
            "0", "1", "2", "3", "4"], [
                "0", "1"], [
                    "0", "1"], [
                        "0", "1", "2", "3"], [
                            "on", "off", "forceoff"], [
                                "always", "cond", "never"]]

    vtype = None   # Variant type
    svalue = None  # static sysfile value
    sfile = None
    rvalue = None
    rfile = None
    kernel = distro = server = None

    def read_kernel_ver(self):
        """
        Method to get information about the running kernel.

        """
        self.distro = Distro(False)                  # Oracle distro object
        self.server = Server(self.distro, False)       # Baremetal, hypervisor, VM
        self.kernel = Kernel(self.server)       # Running kernel
        return self.kernel.get_kernel_desc()

    def is_kvm(self):
        """
        Checks if the server is KVM.

        Returns:
        bool: True if server is KVM Host or Guest,
        else returns False.

        """
        self.distro = Distro(False)                  # Oracle distro object
        self.server = Server(self.distro, False)       # Baremetal, hypervisor, VM
        if (self.server.stype == 5) or (self.server.stype == 6):
            return True
        return False

    def get_sysfile(self):
        """
        Returns specific sysfile path
        based on the variant type.

        Returns:
        str: Sysfile path for the specific variant.

        """
        if self.vtype == self.SPECTRE_V1:
            self.sfile = self.SYS_SPECTRE_V1_FILE
        if self.vtype == self.SPECTRE_V2:
            self.sfile = self.SYS_SPECTRE_V2_FILE
        if self.vtype == self.MELTDOWN:
            self.sfile = self.SYS_MELTDOWN_FILE
        if self.vtype == self.SSBD:
            self.sfile = self.SYS_SSBD_FILE
        if self.vtype == self.L1TF:
            self.sfile = self.SYS_L1TF_FILE
        if self.vtype == self.MDS:
            self.sfile = self.SYS_MDS_FILE
        if self.vtype == self.ITLB_MULTIHIT:
            self.sfile = self.SYS_ITLB_MULTIHIT_FILE
        if self.vtype == self.TSX_ASYNC_ABORT:
            self.sfile = self.SYS_TSX_ASYNC_ABORT_FILE
        return self.sfile

    def is_option_valid(self, index, option, kernel_ver):
        """
        Function to check for valid options
        for the specific sysfile.

        Returns:
        bool: True if the option is valid,
        else returns False.

        """
        if kernel_ver == "RHCK6":
            if option in self.runtime_files_options_RHCK6[index]:
                return True
        elif kernel_ver == "RHCK7":
            if option in self.runtime_files_options_RHCK7[index]:
                return True
        else:
            if option in self.runtime_files_options[index]:
                return True
        return False

    def read_sysfiles(self):
        """
        Function to read the content of the specific sysfile.

        Returns:
        str: Contents of the sysfile.

        """
        self.svalue = self.read_file(self.sfile)
        return self.svalue

    def read_runtime_files(self, vtype):
        """
        Function to read and report contents of various
        runtime files.

        Parameters:
        vtype(int): Variant type.

        Returns:
        array: arr: Containing contents of various
        runtime files for the specific variant type.

        """

        arr = []
        self.read_kernel_ver()
        if vtype == self.SPECTRE_V2:
            if self.read_kernel_ver().find("RHCK") != -1:
                if os.path.isfile(self.runtime_files_array_RHCK[0]):
                    self.rvalue = self.read_file(
                        self.runtime_files_array_RHCK[0])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array_RHCK[1]):
                    self.rvalue = self.read_file(
                        self.runtime_files_array_RHCK[1])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array_RHCK[2]):
                    self.rvalue = self.read_file(
                        self.runtime_files_array_RHCK[2])
                    arr.append(str(self.rvalue))
            else:
                if os.path.isfile(self.runtime_files_array[0]):
                    self.rvalue = self.read_file(self.runtime_files_array[0])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array[1]):
                    self.rvalue = self.read_file(self.runtime_files_array[1])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array[2]):
                    self.rvalue = self.read_file(self.runtime_files_array[2])
                    arr.append(str(self.rvalue))
                if self.read_kernel_ver() == "UEK4":
                    if os.path.isfile(self.runtime_files_array[3]):
                        self.rvalue = self.read_file(
                            self.runtime_files_array[3])
                        arr.append(str(self.rvalue))

        if ((vtype == self.SSBD) and
                (self.read_kernel_ver().find("RHCK") != 0)):
            if os.path.isfile(self.runtime_files_array_RHCK[3]):
                self.rvalue = self.read_file(self.runtime_files_array[3])
                arr.append(str(self.rvalue))

        if vtype == self.L1TF:
            if self.read_kernel_ver().find("RHCK") != -1:
                if os.path.isfile(self.runtime_files_array_RHCK[4]):
                    self.rvalue = self.read_file(self.runtime_files_array[4])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array_RHCK[5]):
                    self.rvalue = self.read_file(self.runtime_files_array[5])
                    arr.append(str(self.rvalue))
            else:
                if os.path.isfile(self.runtime_files_array[4]):
                    self.rvalue = self.read_file(self.runtime_files_array[4])
                    arr.append(str(self.rvalue))
                if os.path.isfile(self.runtime_files_array[5]):
                    self.rvalue = self.read_file(self.runtime_files_array[5])
                    arr.append(str(self.rvalue))

        if (vtype == self.MDS) and (self.read_kernel_ver().find("UEK") != 1):
            if os.path.isfile(self.runtime_files_array[6]):
                self.rvalue = self.read_file(self.runtime_files_array[6])
                arr.append(str(self.rvalue))
            if os.path.isfile(self.runtime_files_array[7]):
                self.rvalue = self.read_file(self.runtime_files_array[7])
                arr.append(str(self.rvalue))

        if (vtype == self.ITLB_MULTIHIT) and (self.is_kvm()):
            if os.path.isfile(self.runtime_files_array[8]):
                self.rvalue = self.read_file(self.runtime_files_array[8])
                arr.append(str(self.rvalue))

        return arr

    def is_ibrs_tunable(self):
        """
        Checks if ibrs/ibpb variables can be tuned.

        Returns:
        bool: True if parameters can be tuned,
        else returns False.

        """
        cmd = ["dmesg | grep SPEC_CTRL"]
        is_spec_ctrl = self.run_command(cmd, True)

        cmd = ["dmesg | grep IBPB | grep FEATURE"]
        is_ibpb = self.run_command(cmd, True)

        if (is_spec_ctrl.find("Not") != -1) and (is_ibpb.find("Not") != -1):
            return False
        return True

    def is_mitigated(self):
        """
        Checks mitigation status of specific variant
        as reported in the sysfile.

        Returns:
        bool: True if string "Vulnerable" is not present
        in the sysfile for the specific variant, else
        returns False.
        """
        if (self.svalue.startswith("Vulnerable")
                or self.svalue.startswith("Unknown")):
            return False

        # return true if mitigated or not affected
        return True

    def scan_sysfile(self):
        """
        Scans various sysfiles to check for mitigation status
        and reports the mitigation status.

        """
        self.read_sysfiles()
        if self.is_mitigated():
            logn("        Boot status................: Mitigated (" +
                 self.svalue + ")")
        else:
            logn("        Boot status................: Vulnerable")

    def __init__(self, vtype):
        """
        Init function for Sysfile class.
        Initializes variant type.

        Parameters:
        vtype(int): Variant type.

        """
        if (vtype not in [self.SPECTRE_V1,
                          self.SPECTRE_V2,
                          self.MELTDOWN,
                          self.SSBD,
                          self.L1TF,
                          self.MDS,
                          self.ITLB_MULTIHIT,
                          self.TSX_ASYNC_ABORT]):
            raise ValueError("ERROR: Unrecognized variant")

        self.vtype = vtype
