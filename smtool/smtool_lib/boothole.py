#!/usr/bin/env python
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
Module contains class to detect
mitigations for boothole vulnerability.

"""

import binascii
import glob
import os
import re
import subprocess
import sys

if (sys.version_info[0] == 3):
    from .base import Base
    from .command import Cmd
else:
    from base import Base
    from command import Cmd


class Boothole(Base):
    def is_secure_boot_available(self):
        out = self.run_command("ls /sys/firmware/efi/vars | grep SecureBoot")
        if (out):
            return True
        return False

    def is_secure_boot_enabled(self):
        filename = glob.glob("/sys/firmware/efi/vars/SecureBoot*/data")[0]
        f = open(filename, "rb")
        is_enabled = int(binascii.hexlify(f.read(1)), 16)
        f.close()
        if (is_enabled):
            return True
        return False

    def is_verification_disabled(self):
        filelist = glob.glob("/sys/firmware/efi/vars/MokSBStateRT*/data")
        if (not filelist):
            return True
        else:
            f = open(filelist[0], "rb")
            is_enabled = int(binascii.hexlify(f.read(1)), 16)
            f.close()
            if (is_enabled):
                return True
            return False

    def is_shim_updated(self):
        out = self.run_command("rpm -q --requires shim-x64 | grep grub2-sig-key")
        if ("202007" in out):
            return True
        return False

    def is_grub2_updated(self):
        out = self.run_command("rpm -q --provides grub2-efi-x64 | grep grub2-sig-key")
        if ("202007" in out):
            return True
        return False

    def get_kernels(self):
        out = self.run_command("rpm -q --whatprovides 'kernel(printk)'")
        return out.splitlines()

    def verify_kernel_signature(self, kernel):
        package = kernel
        out = self.run_command("rpm -q --provides %s | grep kernel-sig-key" % package)

        if ("202007" in out):
            return True
        return False

    def verify_bootable_kernels(self):
        is_verify = 0
        need_shim_grub_update = 0
        need_grub_update = 0
        kernel_list = self.get_kernels()
        print("Verifying kernels for boothole mitigation...")
        for kernel in kernel_list:
            pattern = re.compile(
                r'(\s|-|\.)?(\d{1,4})(\.)(\d{1,4})(\.)(\d{1,4})(\.)(el)')
            if (pattern.search(kernel) is not None):
                kernel_signed = self.verify_kernel_signature(kernel)
                is_verify = 1
            else:
                print(
                    "Non-production kernel %s will not be verified for"
                    " boothole mitigations." % kernel)
            out = self.run_command("rpm -q shim-x64")
            if (out):
                is_shim_updated = self.is_shim_updated()
                is_grub_updated = self.is_grub2_updated()
                if (is_shim_updated == False):
                    need_shim_update = 1
                if (((is_shim_updated == True) and
                        (is_grub_updated == False)) or
                        ((is_shim_updated == False) and
                         (is_grub_updated == True))):
                    need_shim_grub_update = 1
            else:
                is_grub_updated = self.is_grub2_updated()
                if (is_grub_updated == False):
                    need_grub_update = 1
            if (is_shim_updated == is_grub_updated):
                if (is_verify):
                    if (kernel_signed):
                        print(kernel + " has boothole mitigations"
                            " enabled and is bootable in the"
                            " current configuration.")
                    else:
                        print(kernel + " does not have boothole"
                           " mitigations and is not bootable in"
                           " the current configuration.")
            elif (need_shim_grub_update):
                    print("Please yum update 'shim-*'"
                          " 'grub2-*' to repair or"
                          "Secure Boot will fail.")
            elif (need_grub_update):
                    print("Please yum update "
                          "'grub2-efi-x64' to repair or "
                          " Secure Boot will fail.")


    def verify(self):
        if (not self.is_secure_boot_available()):
            return
        else:
            if (not self.is_secure_boot_enabled()):
                print("Secure boot is available but is not "
                      "enabled on the system. Hence, system "
                      "will not be verified for boothole "
                      "mitigations.")
                return
            elif (not self.is_verification_disabled()):
                print("Secure Boot is enabled but "
                      "integrity checking for boothole mitigations "
                      "is disabled.")
                return
            else:
                self.verify_bootable_kernels()

    def __init__(self):
        self.verify()
