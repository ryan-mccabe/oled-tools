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
Module contains Boot class which
contains various methods to
enable/disable/reset various mitigations
at boot time.

Also contains methods to identify
various boot options available for
different kernel/distribution types.

"""
import os
import re
import subprocess
import parser

from tempfile import mkstemp
from shutil import move
from os import fdopen, remove
from base import Base
from sysfile import Sysfile



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


class Boot(Base):
    """
    Class Boot contains various methods
    to scan and identify various boot
    parameters and available options for
    different variants.

    Also contains methods to enable/disable/
    reset mitigations for different
    vulnerabilities.

    """
    # states
    ON = 1
    OFF = 2

    # types
    CMDLINE = 1
    GRUB = 2

    vtype = None
    options = []

    grub_on = None
    grub_off = None
    boot_on = None
    boot_off = None
    kver = None
    bootp = None

    distro = server = None
    sysfile = None
    ktype = None

    def get_kernel_ver(self):
        """
        Method to identify the kernel version.

        Returns:
        str: ktype: Kernel type.

        """
        if re.search("^2.6.39", self.kver) is not None:
            self.ktype = "UEK2"

        if re.search("^3.8.13", self.kver) is not None:
            self.ktype = "UEK3"

        if re.search("^4.1.12", self.kver) is not None:
            self.ktype = "UEK4"

        if re.search("^4.14.35", self.kver) is not None:
            self.ktype = "UEK5"

        if re.search("^2.6.32", self.kver) is not None:
            self.ktype = "RHCK6"

        if re.search("^3.10.0", self.kver) is not None:
            self.ktype = "RHCK7"

        if re.search("^4.18.0", self.kver) is not None:
            self.ktype = "RHCK8"

        return self.ktype

    def is_mitigated(self):
        """
        Checks if mitigation is enabled at boot time.

        Returns:
        bool: True if mitigated on commandline, else
        returns False.

        """
        print "Boot off"
        print self.boot_off
        if self.boot_on:
            return True
        elif self.boot_off:
            return False

    def get_boot_options(self):
        """
        Returns array containing various boot options
        for different variants.

        Returns:
        list: list of various boot options per variant.

        """

        if self.vtype == self.SPECTRE_V1:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                if self.get_kernel_ver().find("UEK") != -1:
                    return ["nospectre_v1"]

        if self.vtype == self.SPECTRE_V2:
            self.get_kernel_ver()
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                if self.get_kernel_ver() == "UEK5":
                    return [
                        "spectre_v2",
                        "spectre_v2_user",
                        "spectre_v2_heuristics",
                        "nospectre_v2",
                        "noibrs",
                        "noibpb"]
                elif self.get_kernel_ver() == "UEK4":
                    return [
                        "spectre_v2",
                        "spectre_v2_heuristics",
                        "nospectre_v2",
                        "noibrs",
                        "noibpb"]
                elif self.get_kernel_ver() == "UEK3":
                    return["spectre_v2", "nospectre_v2", "noibrs", "noibpb"]
                elif self.get_kernel_ver() == "UEK2":
                    return["spectre_v2", "nospectre_v2", "noibrs", "noibpb"]
                elif (self.get_kernel_ver() == "RHCK6" or
                      self.get_kernel_ver() == "RHCK7" or
                      self.get_kernel_ver() == "RHCK8"):
                    return["spectre_v2", "nospectre_v2"]

        if self.vtype == self.MELTDOWN:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                return ["pti", "nopti"]

        if self.vtype == self.SSBD:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                return [
                    "spec_store_bypass_disable",
                    "nospec_store_bypass_disable"]

        if self.vtype == self.L1TF:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                return ["l1tf"]

        if self.vtype == self.MDS:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                return ["mds"]

        if self.vtype == self.TSX_ASYNC_ABORT:
            self.sysfile = Sysfile(self.vtype)
            if os.path.exists(self.sysfile.get_sysfile()):
                return ["tsx_async_abort"]

        return []

    def add_boot_option(self, btype, vtype, opt, val):
        """
        Verifies grub commandline and add the appropriate
        boot option.

        """

        for arr in self.options:
            if (arr[0] == btype and arr[1] == vtype and arr[2] == opt and
                    arr[3] == val):
                return
        self.options.append([btype, vtype, opt, val])

    def get_cmdline_options(self):
        """
        Checks commandline option for specific variant
        and returns the associated string.

        Returns:
        str: tstr: commandline_option and it's value.

        """
        tstr = ""
        for arr in self.options:
            if arr[0] != self.CMDLINE:
                continue
            if arr[3] is None:
                tstr = tstr + arr[2]
            else:
                if arr[3] == self.ON:
                    tstr = tstr + str(arr[2]) + "=on "
                else:
                    tstr = tstr + str(arr[2]) + "=off "
        return tstr

    def get_grub_options(self):
        """
        Checks grub file for specific commandline option
        pertaining to a variant and return the associated
        string.

        Returns:
        str: tstr: grub file option for the specific variant
        and it's value.

        """
        tstr = ""
        for arr in self.options:
            if arr[0] != self.GRUB:
                continue
            if arr[3] is None:
                tstr = tstr + arr[2]
            else:
                if arr[3] == self.ON:
                    tstr = tstr + str(arr[2]) + "=on "
                else:
                    tstr = tstr + str(arr[2]) + "=off "
        return tstr

    def adjust_param(self, arr, i, opt, n):
        arg = arr[i].replace(' ', '')
        if len(arg) == len(opt):
            tmp = arr[i].replace(' ', '')
            if len(tmp) == 1:
                if tmp == "=":
                    if i + 2 < n:
                        return None
                    return arg + "=" + arr[i + 2].replace(' ', '')
                return None
            if i + 1 < n:
                return arg + arr[i + 1].replace(' ', '')
            return None

        if len(arg) == len(opt + "="):
            if i < n - 1:
                return arg + arr[i + 1].replace(' ', '')
            return None
        return arg

    def scan_param(self, btype, arr, j, n):
        """
        Scans for various boot parameters and sets the
        appropriate boot option.

        """
        vtype = self.vtype
        arg = arr[j].replace(' ', '')
        optarr = self.get_boot_options()
        for i in range(len(optarr)):
            opt = optarr[i]
            if len(arg) < len(opt):
                continue
            if len(arg) == len(opt):
                if self.get_kernel_ver().find("UEK") != -1:
                    if vtype == self.SPECTRE_V1 and arg == "nospectre_v1":
                        self.boot_off = True
                        self.add_boot_option(btype, vtype, arg, None)

                if ((vtype == self.SPECTRE_V2 and arg == "nospectre_v2") or
                        (vtype == self.MELTDOWN and arg == "nopti") or
                        (vtype == self.SSBD and
                         arg == "nospec_store_bypass_disable")):
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, arg, None)
                return

            targ = self.adjust_param(arr, j, opt, n)
            if vtype == self.SPECTRE_V2:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)

                if ((targ == opt + "=on") or
                        (targ == opt + "=auto") or
                        (targ == opt + "=retpoline") or
                        (targ == opt + "=retpoline,generic") or
                        (targ == opt + "=retpoline,amd") or
                        (targ == opt + "=ibrs")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)

                if opt == "spectre_v2_user":
                    if ((targ == opt + "=on") or
                            (targ == opt + "=prctl") or
                            (targ == opt + "=prctl,ibpb") or
                            (targ == opt + "=seccomp") or
                            (targ == opt + "=seccomp,ibpb") or
                            (targ == opt + "=auto")):
                        self.boot_on = True
                        self.add_boot_option(btype, vtype, opt, self.ON)
                    elif targ == opt + "=off":
                        self.boot_off = True
                        self.add_boot_option(btype, vtype, opt, self.OFF)

                if opt == "spectre_v2_heuristics":
                    if ((targ == opt + "=skylake=off") or
                            (targ == opt + "=ssbd=off")):
                        self.boot_on = True
                        self.add_boot_option(btype, vtype, opt, self.ON)
                    elif targ == opt + "=off":
                        self.boot_off = True
                        self.add_boot_option(btype, vtype, opt, self.OFF)
                return

            if vtype == self.MELTDOWN:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)
                    return
                if ((targ == opt + "=on") or
                        (targ == opt + "=auto")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)
                    return

            if vtype == self.SSBD:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)
                    return
                if ((targ == opt + "=on") or
                        (targ == opt + "=auto") or
                        (targ == opt + "=prctl") or
                        (targ == opt + "=seccomp")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)
                    return

            if vtype == self.L1TF:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)
                    return
                if ((targ == opt + "=full,force") or
                        (targ == opt + "=flush,nosmt") or
                        (targ == opt + "=flush,nowarn") or
                        (targ == opt + "=full") or
                        (targ == opt + "=flush")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)
                    return

            if vtype == self.MDS:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)
                    return
                if ((targ == opt + "=full") or
                        (targ == opt + "=full,nosmt")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)
                    return

            if vtype == self.TSX_ASYNC_ABORT:
                if targ == opt + "=off":
                    self.boot_off = True
                    self.add_boot_option(btype, vtype, opt, self.OFF)
                if ((targ == opt + "=full") or
                        (targ == opt + "=full,nosmt")):
                    self.boot_on = True
                    self.add_boot_option(btype, vtype, opt, self.ON)
                if opt == "tsx":
                    if ((targ == opt + "=on") or
                            (targ == opt + "=auto")):
                        self.boot_on = True
                        self.add_boot_option(btype, vtype, opt, self.ON)
                    elif targ == opt + "=off":
                        self.boot_off = True
                        self.add_boot_option(btype, vtype, opt, self.OFF)
                return

        return

    def get_grub_info_xen(self):
        """
        Scan grub file in xen systems and obtain
        the various options and their values.

        Returns:
        str: tstr: commandline option and it's value
        for specific variant.

        """
        kernel_ver = self.run_command("uname -r", True)
        string_to_match = '/vmlinuz-' + kernel_ver.strip()
        grub_info = ''

        with open('/boot/grub2/grub.cfg') as old_file:
            for line in old_file:
                if string_to_match in line:
                    grub_info = line

        for line in grub_info.splitlines():
            arr = line.replace('"', '').split()
            for opt in range(len(arr)):
                self.scan_param(self.GRUB, arr, opt, len(arr))
        tstr = self.get_grub_options()
        return tstr

    def scan_cmdline(self):
        """
        Scans commandline to check what boot
        parameters that the server is booted with.

        Returns:
        str: tstr: Commandline options and their values.

        """
        log("        /proc/cmdline..............:")
        cmd = ["cat", "/proc/cmdline"]
        out = self.run_command(cmd, False)

        arr = out.replace('"', '').split()
        for i in range(len(arr)):
            self.scan_param(self.CMDLINE, arr, i, len(arr))
        tstr = self.get_cmdline_options()

        if tstr != "":
            logn(tstr)
        else:
            logn("None")

        return tstr

    def is_grubby_supported(self):
        """
        Method to check if grubby is supported.

        Returns:
        int: 1: if it's supported, else returns 0.

        """
        cmd = ["grubby", "--info=/boot/vmlinuz-" + self.kver]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        if not err:
            return 1
        else:
            return 0

    def scan_grub(self):
        """
        Scans grub file to check values for
        various boot parameters for different
        variants.

        """
        log("        grub settings..............:")

        # On some systems, grubby is not supported, use alternate ways of
        # updating grub cmdline
        if self.is_grubby_supported():
            cmd = ["grubby", "--info=/boot/vmlinuz-" + self.kver]
            out = self.run_command(cmd, False)
            for line in out.splitlines():
                arr = line.replace('"', '').split()
                for opt in range(len(arr)):
                    self.scan_param(self.GRUB, arr, opt, len(arr))
            tstr = self.get_grub_options()
            if tstr != "":
                logn(tstr)
            else:
                logn("None")
            return tstr
        else:
            self.get_grub_info_xen()

    def update_grub(self, args):
        """
        Method to update grub file based on
        the values provided for specific
        commandline options. Uses grubby
        if it's supported, else updates grub
        file directly.

        Parameters:
        args(list of strings): String containing
        commandine option and it's associated value.
        """
        add = delete = 0
        mitigation_string = ''
        mitigation_type = ''

        kernel_ver = self.run_command("uname -r", True)
        string_to_match = '/vmlinuz-' + kernel_ver.strip()
        if args.startswith("--args"):
            mitigation_string = args[7:].replace('"', '')
            mitigation_type = mitigation_string.split("=")[0]
            add = 1
        if args.startswith("--remove"):
            mitigation_string = args[14:].replace('"', '')
            mitigation_type = mitigation_string.split("=")[0].strip()
            delete = 1

        # On some systems, grubby is not supported, use alternate ways of
        # updating grub cmdline
        if not self.is_grubby_supported():
            f_h, abs_path = mkstemp()
            with fdopen(f_h, 'w') as new_file:
                with open('/boot/grub2/grub.cfg') as old_file:
                    for line in old_file:
                        if string_to_match in line:
                            if mitigation_type in line:
                                arr = line.replace('"', '').split()
                                for opt in arr:
                                    if (opt.find(
                                            mitigation_type.strip()) == 0):
                                        arr.remove(opt)
                                separator = ' '
                                replaced_line = separator.join(arr)
                                if add:
                                    new_line = "     " + replaced_line.strip() +\
                                        mitigation_string + "\n"
                                elif delete:
                                    new_line = replaced_line + "\n"
                            else:
                                if add:
                                    new_line = "	" + line.strip() +\
                                        mitigation_string + "\n"
                                elif delete:
                                    new_line = line.replace(
                                        mitigation_string, '')
                            line = new_line
                        new_file.write(line)
            remove('/boot/grub2/grub.cfg')
            move(abs_path, '/boot/grub2/grub.cfg')
        else:
            cmd = "grubby --update-kernel=/boot/vmlinuz-" + self.kver + " " +\
                args
            try:
                out = os.system(cmd)
                logn(out)
            except ValueError as err:
                print err
                raise ValueError("ERROR: updating grub")

    def display(self):
        """
        Displays various boot options.

        """
        for i in range(len(self.options)):
            print self.options[i]

    def enable_mitigation(self, variant):
        """
        Enables mitigation at boot time by
        setting the appropriate variable values.
        Updates grub accordingly.

        Parameters:
        variant(int): Variant type.

        """
        remove = ""
        add = ""
        on = False

        for arr in self.options:
            if arr[0] == self.CMDLINE:
                continue
            if arr[1] != self.vtype:
                continue
            if arr[3] == self.OFF:
                if variant.mitigated_kernel:
                    if (arr[1] == 2) or (arr[1] == 3):
                        add = add + arr[2] + "=on "
                    elif arr[1] == 4:
                        add = add + arr[2] + "=prctl "
                    elif arr[1] == 5:
                        add = add + arr[2] + "=full,force "
                    elif (arr[1] == 6) or (arr[1] == 8):
                        add = add + arr[2] + "=full,nosmt"
            if arr[3] is None and arr[2] == "nospectre_v1":
                remove = remove + arr[2] + " "
            if arr[3] == self.ON:
                on = True

        if remove:
            remove = "--remove-args=\"" + remove + "\""
            self.update_grub(remove)

        if not on:
            b_o = self.get_boot_options()
            if len(b_o) != 0:
                if b_o[0] == "spectre_v2" or b_o[0] == "pti":
                    add = "--args=\"" + " " + b_o[0] + "=on\""
                elif b_o[0] == "spec_store_bypass_disable":
                    add = "--args=\"" + " " + b_o[0] + "=prctl\""
                elif b_o[0] == "l1tf":
                    add = "--args=\"" + " " + b_o[0] + "=full,force\""
                elif b_o[0] == "mds":
                    add = "--args=\"" + " " + b_o[0] + "=full,nosmt\""
                elif b_o[0] == "tsx_async_abort":
                    add = "--args=\"" + " " + b_o[0] + "=full,nosmt\""
                elif b_o[0] == "tsx":
                    add = "--args=\"" + " " + b_o[0] + "=off\""

        if add != "":
            self.update_grub(add)

    def disable_mitigation(self, variant):
        """
        Disables mitigation at boot time by
        setting the appropriate variable values.
        Updates grub accordingly.

        Parameters:
        variant(int): Variant type.

        """
        add = ""
        off = False

        for arr in self.options:
            if arr[0] == self.CMDLINE:
                continue
            if arr[1] != self.vtype:
                continue
            if arr[3] == self.ON:
                if variant.mitigated_kernel:
                    if not arr[1] == 1:
                        add = add + arr[2] + "=off "
                    else:
                        add = add + arr[2]
            if (arr[3] == self.OFF or (
                    arr[3] is None and arr[2] == "nospectre_v1")):
                off = True

        if not off:
            b_o = self.get_boot_options()
            if len(b_o) != 0:
                if b_o[0] == "nospectre_v1":
                    add = "--args=\"" + " " + b_o[0] + "\""
                else:
                    add = "--args=\"" + " " + b_o[0] + "=off\""

        if add != "":
            self.update_grub(add)

    def reset_mitigation(self, variant):
        """
        Resets mitigation at boot time by
        setting the appropriate variable values.
        Updates grub accordingly.

        Parameters:
        v(int): Variant type.

        """

        remove = ""

        for arr in self.options:
            if arr[0] == self.CMDLINE:
                continue
            if arr[1] != self.vtype:
                continue
            if (arr[3] is None or arr[3] ==
                    self.OFF or (arr[2].find("no") == 0)):
                remove = remove + arr[2] + " "
            if arr[3] == self.ON:
                if variant.mitigated_kernel:
                    remove = remove + arr[2] + " "
        if remove:
            remove = "--remove-args=\"" + remove + "\""
            self.update_grub(remove)

    def __init__(self, vtype, kver):
        """
        Init function for boot class.
        Initializes the kernel version and
        variant type.

        Also initializes options array.

        """
        if (vtype not in [self.SPECTRE_V1,
                          self.SPECTRE_V2,
                          self.MELTDOWN,
                          self.SSBD,
                          self.L1TF,
                          self.MDS,
                          self.ITLB_MULTIHIT,
                          self.TSX_ASYNC_ABORT]):
            raise ValueError("ERROR: Unrecognized boot variant")

        self.kver = kver
        self.vtype = vtype
        self.options = []
