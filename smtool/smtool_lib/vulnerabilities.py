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
Module scans for various vulnerabilities
the server is vulnerable to, contains methods
to enable and disable mitigations for different
vulnerabilities both in boot and runtime.

"""
import os
import parser

from base import Base
from distro import Distro
from server import Server
from sysfile import Sysfile
from variant import Variant


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


class Vulnerabilities(Base):
    """
    Vulnerabilities class. Lists various vulnerabilities and
    contains methods to enable, disable and reset mitigations
    for various vulnerabilities.

    """
    # Variants
    v_1 = v_2 = v_3 = v_4 = v_5 = v_6 = v_7 = v_8 = None
    host = None
    vtype = None
    sysfile = None
    distro = server = boot = None
    xen_machine_type = ""

    mitigation_options = []
    mitigation_supported = mitigation_not_supported = 0

    SPECTRE_V1 = 1
    SPECTRE_V2 = 2
    MELTDOWN = 3
    SSBD = 4
    L1TF = 5
    MDS = 6
    ITLB_MULTIHIT = 7
    TSX_ASYNC_ABORT = 8

    def get_vtype(self, var):
        """
        Returns vulnerability type for a given variant.

        Parameters:
        var(int): variant type.

        Returns:
        int: Vulnerability type.

        """
        if var == self.v_1:
            return self.SPECTRE_V1
        if var == self.v_2:
            return self.SPECTRE_V2
        if var == self.v_3:
            return self.MELTDOWN
        if var == self.v_4:
            return self.SSBD
        if var == self.v_5:
            return self.L1TF
        if var == self.v_6:
            return self.MDS
        if var == self.v_7:
            return self.ITLB_MULTIHIT
        if var == self.v_8:
            return self.TSX_ASYNC_ABORT

    def display(self):
        """
        Displays the name of various vulnerabilities.

        """
        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            if var is None:
                continue

            var.display()

    def is_xen(self):
        """
        Checks if the server is a Xen Hypervisor or PV guest.

        Returns:
        str: Type of Xen server.
        """
        self.distro = Distro(False)                  # Oracle distro object
        self.server = Server(self.distro, False)       # Baremetal, hypervisor, VM
        if self.server.stype == 2:
            self.xen_machine_type = "Xen Hypervisor"
            return True
        elif self.server.stype == 3:
            self.xen_machine_type = "Xen PV Guest"
            return True
        return False


    def disable_vulnerabilities(self, dry_run, yes):
        """
        Function to enable mitigation for various vulnerabilities.
        Checks sysfile to see if mitigation is enabled and if
        mitigation is supported, enables them at boot time if
        variable yes is set.

        Parameters:
        dry_run(bool): Option to request dry_run - entered by user.
        yes(bool): User provided option to enable mitigations.
        If set along with enable-full-mitigation, full mitigation
        for all vulnerabilities are enabled.

        """
        kernel = self.host.kernel
        variants = unsupported_variants = supported_variants = ""

        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            self.sysfile = Sysfile(self.get_vtype(var))
            if var is None:
                continue

            if self.is_xen():
                if (var == self.v_3) or (var == self.v_4) or (var == self.v_6):
                    unsupported_variants = unsupported_variants + var.vname + \
                        ", "
                    self.mitigation_not_supported = 1
                elif os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    supported_variants = supported_variants + var.vname + ", "
            else:
                if os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    supported_variants = supported_variants + var.vname + ", "
                else:
                    variants = variants + var.vname + ", "
                    self.mitigation_not_supported = 1

        if self.mitigation_not_supported:
            if self.is_xen():
                print self.xen_machine_type + \
                    " does not support mitigation for " + \
                    unsupported_variants[:-2]
            if variants and variants.strip():
                print "Kernel does not support mitigation for "
                print variants[:-2]
                if ((kernel.get_kernel_desc() == "UEK3") or (
                        kernel.get_kernel_desc() == "UEK2")):
                    print "Kernels older than UEK4 do not support mitigation "\
                            "for SSBD"
                    print "Please upgrade the kernel to UEK4 version "\
                            "4.1.12-124.33.2 to enable support for all mitigations"
                else:
                    print "Please upgrade the kernel to the following "\
                            "version: " + \
                        kernel.recommended_ver(kernel.get_kernel_desc())

        if self.mitigation_supported:
            if dry_run:
                print "Full mitigation for the following variants will be "\
                        "enabled: " + supported_variants[:-2]

                print "Please re-run this command with -y to enable these "\
                        "mitigations and then reboot for the changes to "\
                        "take effect."
            else:
                if not yes:
                    print "Full mitigation for the following variants "\
                        "will be enabled: " + supported_variants[:-2]
                    print "Would you like to enable them?"
                    option = raw_input(
                        "Please enter y to enable or n if you do not wish "\
                        "to enable them: ")
                    if option == "y":
                        yes = True
                    else:
                        yes = False
                if yes:
                    print "Enabling full mitigation for supported variants.."\
                        "Please reboot for the changes to take effect"
                    for var in (
                            self.v_1,
                            self.v_2,
                            self.v_3,
                            self.v_4,
                            self.v_5,
                            self.v_6,
                            self.v_8):
                        self.sysfile = Sysfile(self.get_vtype(var))
                        if var is None:
                            continue

                        if self.is_xen():
                            if ((var == self.v_3) or (var == self.v_4)
                                    or (var == self.v_6)):
                                continue

                        if os.path.exists(self.sysfile.get_sysfile()):
                            var.enable_variant_boot()
                return

    def enable_vulnerabilities(self, dry_run, yes):
        """
        Function to disable mitigation for various vulnerabilities.
        Checks sysfile to see if mitigation is disabled and if
        mitigation is supported, disables them at boot time if
        variable yes is set.

        Parameters:
        dry_run(bool): Option to request dry_run - entered by user.
        yes(bool): User provided option to disable mitigations.
        If set along with disable-mitigations, full mitigation for
        all vulnerabilities are enabled.

        """
        kernel = self.host.kernel
        variants = unsupported_variants = supported_variants = ""
        v_5 = False

        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            self.sysfile = Sysfile(self.get_vtype(var))
            if var is None:
                continue

            if self.is_xen():
                if (var == self.v_3) or (var == self.v_4) or (var == self.v_6):
                    unsupported_variants = unsupported_variants + \
                                           var.vname + ", "
                    self.mitigation_not_supported = 1
                elif os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    if var == self.v_5:
                        v_5 = True
                    if var != self.v_5:
                        supported_variants = supported_variants + \
                                             var.vname + ", "
            else:
                if os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    if var == self.v_5:
                        v_5 = True
                    if var != self.v_5:
                        supported_variants = supported_variants + \
                                             var.vname + ", "
                else:
                    variants = variants + var.vname + ", "
                    self.mitigation_not_supported = 1

        if self.mitigation_not_supported:
            if self.is_xen():
                print self.xen_machine_type + \
                    " does not support mitigation for " + \
                    unsupported_variants[:-2]
            if variants and variants.strip():
                print "Kernel does not support mitigation for " + \
                    variants[:-2]
                if ((kernel.get_kernel_desc() == "UEK3") or (
                        kernel.get_kernel_desc() == "UEK2")):
                    print "Kernels older than UEK4 do not support mitigation "\
                          "for SSBD"
                    print "Please upgrade the kernel to UEK4 version "\
                          "4.1.12-124.33.2 to enable support for all mitigations"
                else:
                    print "Please upgrade the kernel to the "\
                          "following version: " + \
                        kernel.recommended_ver(kernel.get_kernel_desc())

        if self.mitigation_supported:
            if dry_run:
                print "The mitigations for the following variants will be "\
                      "disabled: " + supported_variants[:-2]
                print "Please re-run this command with  -y to disable "\
                      "these mitigations and then reboot for the "\
                      "changes to take effect."
                if v_5:
                    print "Please note that PTE inversion mitigation is "\
                          "unconditionally enabled for L1TF"
                    print "l1tf=off only disables hypervisor mitigations "\
                          "if any"
            else:
                if not yes:
                    print "The mitigations for the following variants will be "\
                          "disabled: " + supported_variants[:-2]
                    print "Would you like to disable them?"
                    option = raw_input(
                        "Please enter y to disable or n if you do not wish "\
                        "to disable them: ")
                    if option == "y":
                        yes = True
                    else:
                        yes = False
                if yes:
                    print "Disabling mitigations for supported variants.." \
                          "Please reboot for the changes to take effect"
                    for var in (
                            self.v_1,
                            self.v_2,
                            self.v_3,
                            self.v_4,
                            self.v_5,
                            self.v_6,
                            self.v_8):
                        self.sysfile = Sysfile(self.get_vtype(var))
                        if var is None:
                            continue

                        if self.is_xen():
                            if ((var == self.v_3) or (var == self.v_4)
                                    or (var == self.v_6)):
                                continue

                        if var == self.v_5:
                            print "Please note that PTE inversion mitigation "\
                                  "is unconditionally enabled for L1TF"
                            print "l1tf=off only disables hypervisor "\
                                  "mitigations if any"

                        if os.path.exists(self.sysfile.get_sysfile()):
                            var.disable_variant_boot()

        return

    def enable_vulnerabilities_runtime(self, yes):
        """
        Function to disable mitigation for various vulnerabilities.
        at runtime. Invokes function to write to various sysfiles at
        runtime and provides the user with the options to be used.

        Parameters:
        yes(bool): User provided option to enable vulnerabilities.
        If set along with disable-mitigation, the default value
        will be written to the appropriate sysfile.

        """
        kernel = self.host.kernel
        variants = unsupported_variants = ""
        for var in (self.v_2, self.v_5, self.v_6, self.v_7):
            self.sysfile = Sysfile(self.get_vtype(var))
            if var is None:
                continue

            if self.is_xen():
                if (var == self.v_3) or (var == self.v_4) or (var == self.v_6):
                    unsupported_variants = unsupported_variants + var.vname +\
                        ", "
                    self.mitigation_not_supported = 1
                elif os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    var.disable_variant_runtime(yes)
            else:
                if os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    var.disable_variant_runtime(yes)
                else:
                    variants = variants + var.vname + ", "
                    self.mitigation_not_supported = 1

        if self.mitigation_not_supported:
            if self.is_xen():
                print self.xen_machine_type + \
                    " does not support runtime mitigations"
            if variants and variants.strip():
                print "Kernel does not support mitigation for " + variants[:-2]
                if ((kernel.get_kernel_desc() == "UEK3") or (
                        kernel.get_kernel_desc() == "UEK2")):
                    print "Kernels older than UEK4 do not support "\
                          "mitigation for SSBD"
                    print "Please upgrade the kernel to UEK4 version "\
                          "4.1.12-124.33.2 to enable support for all"\
                          "mitigations"
                else:
                    print "Please upgrade the kernel to the "\
                          "following version: " + \
                          kernel.recommended_ver(kernel.get_kernel_desc())
        return

    def disable_vulnerabilities_runtime(self, yes):
        """
        Function to enable mitigation for various vulnerabilities.
        at runtime. Invokes function to write to various sysfiles at
        runtime and provides the user with the options to be used.

        Parameters:
        yes(bool): User provided option to disable vulnerabilities.
        If set along with enable-mitigation, the default value
        will be written to the appropriate sysfile.

        """
        kernel = self.host.kernel
        variants = unsupported_variants = ""
        for var in (self.v_2, self.v_5, self.v_6, self.v_7):
            self.sysfile = Sysfile(self.get_vtype(var))
            if var is None:
                continue

            if self.is_xen():
                if (var == self.v_3) or (var == self.v_4) or (var == self.v_6):
                    unsupported_variants = unsupported_variants + \
                                           var.vname + ", "
                    self.mitigation_not_supported = 1
                elif os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    var.enable_variant_runtime(yes)
            else:
                if os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    var.enable_variant_runtime(yes)
                else:
                    variants = variants + var.vname + ", "
                    self.mitigation_not_supported = 1

        if self.mitigation_not_supported:
            if self.is_xen():
                print self.xen_machine_type + \
                    " does not support runtime mitigations"
            if variants and variants.strip():
                print "Kernel does not support mitigation for " + \
                    variants[:-2]
                if ((kernel.get_kernel_desc() == "UEK3") or (
                        kernel.get_kernel_desc() == "UEK2")):
                    print "Kernels older than UEK4 do not support "\
                          "mitigation for SSBD"
                    print "Please upgrade the kernel to UEK4 version "\
                          "4.1.12-124.33.2 to enable support for all "\
                          "mitigations"
                else:
                    print "Please upgrade the kernel to the "\
                          "following version: " + \
                          kernel.recommended_ver(kernel.get_kernel_desc())

    def reset_vulnerabilities(self, dry_run, yes):
        """
        Function to enable default mitigation for vulnerabilities.
        Checks sysfile to see if mitigation is enabled and if
        mitigation is supported, enables default mitigation
        at boot time if variable yes is set.

        Parameters:
        dry_run(bool): Option to request dry_run - entered by user.
        yes(bool): User provided option to enable mitigations.
        If set along with enable-default-mitigation, default
        mitigation for all vulnerabilities are enabled.

        """
        kernel = self.host.kernel
        variants = unsupported_variants = supported_variants = ""
        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            self.sysfile = Sysfile(self.get_vtype(var))
            if var is None:
                continue

            if self.is_xen():
                if (var == self.v_3) or (var == self.v_4) or (var == self.v_6):
                    unsupported_variants = unsupported_variants + var.vname + \
                        ", "
                    self.mitigation_not_supported = 1
                elif os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    supported_variants = supported_variants + var.vname + ", "
                    var.reset_variant_boot()
            else:
                if os.path.exists(self.sysfile.get_sysfile()):
                    self.mitigation_supported = 1
                    supported_variants = supported_variants + var.vname + ", "
                    var.reset_variant_boot()
                else:
                    variants = variants + var.vname + ", "
                    self.mitigation_not_supported = 1

        if self.mitigation_not_supported:
            if self.is_xen():
                print self.xen_machine_type + \
                    " does not support mitigation for " + \
                    unsupported_variants[:-2]
            if variants and variants.strip():
                print "Kernel does not support mitigation for " + \
                    variants[:-2]
                if ((kernel.get_kernel_desc() == "UEK3") or (
                        kernel.get_kernel_desc() == "UEK2")):
                    print "Kernels older than UEK4 do not support "\
                          "mitigation for SSBD"
                    print "Please upgrade the kernel to UEK4 version "\
                          "4.1.12-124.33.2 to enable support for all "\
                          "mitigations"
                else:
                    print "Please upgrade the kernel to the "\
                          "following version: " + \
                          kernel.recommended_ver(kernel.get_kernel_desc())

        if self.mitigation_supported:
            if dry_run:
                print "The default mitigations for the following variants "\
                      "will be enabled: " + \
                      supported_variants[:-2]
                print "Please re-run this command with  -y to enable default "\
                      "mitigations and then reboot for the changes to "\
                      "take effect"
            else:
                if not yes:
                    print "The default mitigations for the following "\
                          "variants will be enabled: " + \
                          supported_variants[:-2]
                    print "Would you like to enable them?"
                    option = raw_input(
                        "Please enter y to enable or n if you do not "\
                        "wish to enable them: ")
                    if option == "y":
                        yes = True
                    else:
                        yes = False
                if yes:
                    print "Enabling default mitigations for supported "\
                          "variants..Please reboot for the changes to take "\
                          "effect"
                    for var in (
                            self.v_1,
                            self.v_2,
                            self.v_3,
                            self.v_4,
                            self.v_5,
                            self.v_6,
                            self.v_8):
                        self.sysfile = Sysfile(self.get_vtype(var))
                        if var is None:
                            continue

                        if self.is_xen():
                            if ((var == self.v_3) or (var == self.v_4)
                                    or (var == self.v_6)):
                                continue

                        elif os.path.exists(self.sysfile.get_sysfile()):
                            var.reset_variant_boot()
        return

    def get_vulnerabilities(self):
        """
        Check which vulnerabilities the system is susceptible to.

        Returns:
        str: out: String containing vulnerabilities that the
        system is currently vulnerable to.

        """
        out = ""
        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            if var is None:
                continue
            if not var.is_mitigated():
                out = out + var.vname + ", "
        return out

    def is_mitigated(self):
        """
        Checks if all vulnerabilities are mitigated.

        Returns:
        bool: True if all mitigations are present,
        else returns False.

        """
        for var in (
                self.v_1,
                self.v_2,
                self.v_3,
                self.v_4,
                self.v_5,
                self.v_6,
                self.v_7,
                self.v_8):
            if var is None:
                continue
            if not var.is_mitigated():
                return False
        return True

    def scan_vulnerabilities(self):
        """
        Scans for various vulnerabilities and checks
        if mitigation is possible (based on kernel version,
        server type, microcode version) and updates
        vuln_list accordingly.

        """
        cpu = self.host.cpu
        cpu.scan_vulnerabilities()
        vuln_list = []
        if not cpu.is_cpu_vulnerable():
            return None

        logn("  scanning for vulnerabilities......")
        self.v_1 = Variant(self.SPECTRE_V1, self.host)
        is_mitigation_possible = self.v_1.scan_variant()
        self.mitigation_options.append(self.v_1.vname + " ")
        self.mitigation_options.append(self.v_1.mitigation_str)
        if (cpu.is_vulnerable_v_1()) and (not is_mitigation_possible):
            vuln_list.append(self.v_1.vname + ",")

        self.v_2 = Variant(self.SPECTRE_V2, self.host)
        is_mitigation_possible = self.v_2.scan_variant()
        self.mitigation_options.append(self.v_2.vname + " ")
        self.mitigation_options.append(self.v_2.mitigation_str)
        if (cpu.is_vulnerable_v_2()) and (not is_mitigation_possible):
            vuln_list.append(self.v_2.vname + ",")

        self.v_3 = Variant(self.MELTDOWN, self.host)
        is_mitigation_possible = self.v_3.scan_variant()
        self.mitigation_options.append(self.v_3.vname + " ")
        self.mitigation_options.append(self.v_3.mitigation_str)
        if (cpu.is_vulnerable_v_3()) and (not is_mitigation_possible):
            vuln_list.append(self.v_3.vname + ",")

        self.v_4 = Variant(self.SSBD, self.host)
        is_mitigation_possible = self.v_4.scan_variant()
        self.mitigation_options.append(self.v_4.vname + " ")
        self.mitigation_options.append(self.v_4.mitigation_str)
        if (cpu.is_vulnerable_v_4()) and (not is_mitigation_possible):
            vuln_list.append(self.v_4.vname + ",")

        self.v_5 = Variant(self.L1TF, self.host)
        is_mitigation_possible = self.v_5.scan_variant()
        self.mitigation_options.append(self.v_5.vname + " ")
        self.mitigation_options.append(self.v_5.mitigation_str)
        if (cpu.is_vulnerable_v_5()) and (not is_mitigation_possible):
            vuln_list.append(self.v_5.vname + ",")

        self.v_6 = Variant(self.MDS, self.host)
        is_mitigation_possible = self.v_6.scan_variant()
        self.mitigation_options.append(self.v_6.vname + " ")
        self.mitigation_options.append(self.v_6.mitigation_str)
        if (cpu.is_vulnerable_v_6()) and (not is_mitigation_possible):
            vuln_list.append(self.v_6.vname + ",")

        self.v_7 = Variant(self.ITLB_MULTIHIT, self.host)
        is_mitigation_possible = self.v_7.scan_variant()
        self.mitigation_options.append(self.v_7.vname + " ")
        self.mitigation_options.append(self.v_7.mitigation_str)
        if (cpu.is_vulnerable_v_7()) and (not is_mitigation_possible):
            vuln_list.append(self.v_7.vname + ",")

        self.v_8 = Variant(self.TSX_ASYNC_ABORT, self.host)
        is_mitigation_possible = self.v_8.scan_variant()
        self.mitigation_options.append(self.v_8.vname + " ")
        self.mitigation_options.append(self.v_8.mitigation_str)
        if (cpu.is_vulnerable_v_8()) and (not is_mitigation_possible):
            vuln_list.append(self.v_8.vname + ",")

        logn("")
        return vuln_list

    def __init__(self, host):
        """
        Init function for vulnerabilities class

        Initializes host variable

        """
        self.host = host
