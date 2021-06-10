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
from smtool_lib import Sysfile
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
        vname = vname.strip()
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
        if vname == "ITLB_Multihit":
            return self.ITLB_MULTIHIT
        if vname == "TSX_Async_Abort":
            return self.TSX_ASYNC_ABORT


    def is_enabled_runtime(self, vtype, vals):
        if (vtype == self.SPECTRE_V2):
            if ((vals[0] == "0") and (vals[2] == "0")):
                return False
            else:
                return True
        elif (vtype == self.MDS):
            if(self.server.get_server_type() == "KVM_GUEST"):
                if ((vals[0] == "0") or (vals[1] == "0")):
                    return False
                else:
                    return True
            else:
                if ((vals[0] == "1") or (vals[1] == "1")):
                    return True
                else:
                    return False
        elif (vtype == self.ITLB_MULTIHIT):
            if (vals[0] == "N"):
                return False
            else:
                return True


    def is_variant_xen(self, vname):
        if (vname == "Spectre V1" or vname == "Spectre V2"
                or vname == "TSX_Async_Abort"):
            return True
        else:
            return False


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
        check_mitigation_xen = True

        server_type = self.server.scan_server(self.distro)
        is_mitigated_sys = []
        is_mitigated_cmdline = []
        is_mitigated_kernel = []
        is_mitigated_cmdline_xen = []
        is_mitigated_kernel_xen = []
        is_enabled_runtime = False
        is_microcode_vulnerable = ""
        enabled_mitigations_str = ""

        variant_list = []
        variants = []
        variant_list_rt_enabled = []
        variant_list_rt_disabled = []
        variant_list_mc = []
        require_microcode_update = False
        require_kernel_upgrade = False
        require_cmdline_update = False
        require_runtime_update = False
        is_l1tf = 0

        disabled_variants_cmdline = ""
        disabled_variants_cmdline_xen = ""
        disabled_variants_kernel = ""
        disabled_variants_kernel_xen = ""
        recommended_ver = kernel.recommended_ver(kernel.get_kernel_desc())
        kernel_ver = kernel.get_kernel()

        self.boothole = Boothole()

        if not h.is_vulnerable():
            print("System is not vulnerable")
            return

        if h.is_mitigated():
            print("Mitigations are in place for all cpu vulnerabilities")
            return

        list_vuln = h.get_vulnerabilities()

        h.vuln = Vulnerabilities(h)

        len_mitigation_opt = len(h.vuln.mitigation_options)
        if h.vuln.mitigation_options:
            for i in range(0, len_mitigation_opt):
                if (i % 2) == 0:
                    vname = h.vuln.mitigation_options[i].strip()
                else:
                    """
                    Check if kernel supports mitigation for
                    different variants, whether they are mitigated
                    at boot and runtime and create lists for variants
                    that require kernel, microcode, runtime or boot-time
                    upgrades.

                    """ 
                    mitigation_opt = h.vuln.mitigation_options[i]
                    if (len(mitigation_opt) != 0):
                        is_mitigated_kernel.append(vname + "," + "True")
                        if (mitigation_opt[1]):
                            is_mitigated_cmdline.append(vname + "," + "True")
                            if (mitigation_opt[0]):
                                is_mitigated_sys.append(vname + "," + "True")
                            else:
                                if mitigation_opt[0] is None:
                                    is_mitigated_sys.append(
                                        vname + "," + "False")
                                    is_microcode_vulnerable += vname + ","
                                    variant_list_mc.append(vname)
                                    vtype = self.get_variant_type(vname)
                                    sysfile = Sysfile(vtype)
                                    vals = sysfile.read_runtime_files(vtype)
                                    if vals:
                                        if (not self.is_enabled_runtime(vtype, vals)):
                                            require_runtime_update = True
                                            variant_list_mc.remove(vname)
                                            variant_list_rt_disabled.append(vname)
                                    if len(variant_list_mc) != 0:
                                        require_microcode_update = True
                        else:
                            if mitigation_opt[1] is None:
                                is_mitigated_cmdline.append(
                                    vname + "," + "False")
                            if mitigation_opt[0]:
                                is_mitigated_sys.append(
                                    vname + "," + "True")
                                vtype = self.get_variant_type(vname)
                                sysfile = Sysfile(vtype)
                                vals = sysfile.read_runtime_files(vtype)
                                if vals:
                                    if self.is_enabled_runtime(vtype, vals):
                                        variant_list_rt_enabled.append(vname)
                                        require_runtime_update = False 
                            require_cmdline_update = True
                    else:
                        is_mitigated_kernel.append(vname + "," + "False")
                        require_kernel_upgrade = True

        if (list_vuln):
            print("System is vulnerable to " + list_vuln[:-1])
            vuln_list = list_vuln[:-1].split(",")

        if is_mitigated_cmdline:
            """ 
            List variants that would
            require cmdline update
           
            """ 
            for i in range(0, len(is_mitigated_cmdline)):
                var = is_mitigated_cmdline[i].split(",")[0]
                if (is_mitigated_cmdline[i].find(
                        "False") != -1):
                    disabled_variants_cmdline += \
                        is_mitigated_cmdline[i].\
                        split(",")[0] + ", "
                    require_cmdline_update = True
                    if (self.is_variant_xen(var)):
                        is_mitigated_cmdline_xen.append(
                            is_mitigated_cmdline[i])

        if is_mitigated_kernel:
            """ 
            List variants that would
            require kernel update.
           
            """ 
            for i in range(0, len(is_mitigated_kernel)):
                var = is_mitigated_kernel[i].split(",")[0]
                if (is_mitigated_kernel[i].find(
                        "False") != -1):
                    disabled_variants_kernel += \
                        is_mitigated_kernel[i].\
                        split(",")[0] + ", "
                    require_kernel_upgrade = True
                    if (self.is_variant_xen(var)):
                        is_mitigated_kernel_xen.append(
                            is_mitigated_kernel[i])

        """ 
        List variants that require commandline/kernel
        updates on xen machine.
       
        """ 
        if ((self.server.stype == self.XEN_PV) or (
                self.server.stype == self.XEN_HYPERVISOR)):
            xen = True
            print("Mitigation is not available for Meltdown, "
                  "SSBD, MDS and ITLB_Multihit on Xen systems")

            require_cmdline_update = False
            require_kernel_upgrade = False
            if len(is_mitigated_cmdline_xen) != 0:
                for i in range(0, len(is_mitigated_cmdline_xen)):
                    var = is_mitigated_cmdline_xen[i].\
                        split(",")[0]
                    disabled_variants_cmdline_xen += var + ", "
                if (disabled_variants_cmdline_xen):
                    require_cmdline_update = True

            if len(is_mitigated_kernel_xen) != 0:
                for i in range(0, len(is_mitigated_kernel_xen)):
                    disabled_variants_kernel_xen += \
                        is_mitigated_kernel_xen[i].\
                        split(",")[0] + ", "
                if (disabled_variants_kernel_xen):
                    require_kernel_upgrade = True

        """ 
        List variants that are disabled in runtime
        and would require runtime upgrades.
       
        """ 
        if require_runtime_update:
            if variant_list_rt_disabled:
                variants = ""
                for i in range(0, len(variant_list_rt_disabled)):
                    vtype = self.get_variant_type(variant_list_rt_disabled[i])
                    if (variant_list_rt_disabled[i] == "SSBD"):
                        if (kernel_ver.find("UEK") != -1):
                            continue
                    variants += variant_list_rt_disabled[i] + ","
                if variants:
                    print("Mitigation for the following "
                          "variants have been disabled at runtime: " +
                          variants[:-1].strip())
                    print("They can be enabled at runtime "
                          "using the tool")

        """ 
        List variants which require kernel upgrade
        and recommend appropriate kernel version upgrade.
       
        """ 
        if require_kernel_upgrade:
            print("Kernel is too old to support mitigations for "
                  "" + disabled_variants_kernel[:-2])
            if (kernel.ktype == 1) or (kernel.ktype == 2):
                print("Kernels older than UEK4 do not support mitigation "
                      "for SSBD and ITLB_Multihit")
                print("Please upgrade the kernel to UEK4 version "
                      "4.1.12-124.33.2 to enable support for all "
                      "mitigations")
            else:
                print("Please upgrade the kernel to version " +
                    recommended_ver)

        """ 
        List variants which require microcode update
        and add appropriate recommendations based on
        server type.
        
        """ 
        if require_microcode_update:
            if (server_type == self.BARE_METAL or server_type ==
                    self.KVM_HOST or server_type == self.XEN_HYPERVISOR):
                if "Spectre V2 " in variant_list_mc:
                    i = variant_list_mc.index("Spectre V2 ")
                    variant_list[i] = "Spectre V2 (IBRS-based) "
                if xen:
                    for i in variant_list_mc:
                        if (self.is_variant_xen(i)):
                            variants_mc.append(i)
                    variant_list_mc = list(variants)
                if (variant_list_mc):
                    print("Microcode is too old to support "
                      "mitigation for " + ' '.join(variant_list_mc))
                    print("Please upgrade the microcode to "
                      "the latest version using "
                      "yum upgrade microcode_ctl")
            elif (server_type == self.KVM_GUEST or server_type ==
                  self.XEN_PV or server_type == self.XEN_HVM):
                print("Please check if the host microcode "
                      "is updated to address the following vulnerabilities: "
                      + is_microcode_vulnerable[:-1])
                if (server_type == self.KVM_GUEST):
                    print("Also please verify if the host is running "
                          "QEMU version 2.9 and above")
                else:
                    print("Also please verify if Dom0 is running "
                          "the latest xen version")

        #List variants that would require boot-time update
        
        if require_cmdline_update:
            if (xen):
                disabled_variants_cmdline = disabled_variants_cmdline_xen
            if (disabled_variants_cmdline):
                if variant_list_rt_enabled:
                    if ('L1TF' in variant_list_rt_enabled):
                        variant_list_rt_enabled.remove('L1TF')
                        is_l1tf = 1
                    enabled_mitigations_str = ','.join(
                        str(val) for val in variant_list_rt_enabled)
                    if (enabled_mitigations_str and not xen):
                        print(
                            "Mitigation for the following variants has been enabled "
                            "at runtime: " + enabled_mitigations_str)
                print("Mitigation for the following variants disabled on "
                    "the cmdline: " + disabled_variants_cmdline[:-2])
                if (list_vuln[:-2].find('ITLB_Multihit') != -1):
                    vuln_list.remove('ITLB_Multihit')
                    if (not vuln_list):
                        if (server_type == self.KVM_HOST):
                            if (not variant_list_rt_enabled):
                                print("Please enable mitigation for itlb_multihit "
                                    "explicitly either at runtime or at boot using "
                                    "either enable-default-mitigation "
                                    "enable-full-mitigation options provided by the tool")
                if (is_l1tf):
                    print("Please note that the default mitigation will "
                        "always be enabled for L1TF")
                if (vuln_list):
                    print("Please enable the mitigations for all variants using the tool")


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
            self.server.get_server_type()

            self.microcode = Microcode()
            self.host.scan_host()
            if not self.host.is_vulnerable():
                print("This system is not vulnerable. Nothing to be done")
            if self.scan:
                if (not self.verbose):
                    print("Scanning system for the following vulnerabilities: ")
                    print(", ".join(self.vdesc[1:]))
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
