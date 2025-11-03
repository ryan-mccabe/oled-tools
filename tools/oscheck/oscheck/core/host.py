#!/usr/bin/python3
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
#
# Authors:
#   Ryan McCabe <ryan.m.mccabe@oracle.com>

"""Host system information populator"""

import os
import re
import logging

from oscheck.core.engine import global_vars
from oscheck.core.util import open_file


EXTERNAL = logging.getLogger("oschecker.external")
INTERNAL = logging.getLogger("oschecker.internal")


def get_uek_ver(uname_rel: str) -> str:
    """Get the kernel UEK version, if any"""
    if not uname_rel:
        return ""

    uek_ver_regex = {
        r"^4\.14\..*el.*uek": "UEK5",
        r"^5\.4\..*el.*uek": "UEK6",
        r"^5\.15\..*el.*uek": "UEK7",
        r"^6\.12\..*el.*uek": "UEK8",
    }

    for p, ver in uek_ver_regex.items():
        if re.match(p, uname_rel):
            return ver

    return ""


class OLHost:
    """Host information used to determine which rules to check"""
    def __init__(self, base_path: str = "/"):
        """Initialize host data collection"""
        self.base_path = base_path.rstrip("/")
        if self.base_path == "":
            self.base_path = "/"

        self.os_major = ""
        self.os_minor = ""
        self.exadata = False
        self.ovs_server = False
        self.virt_guest = False
        self.kernel_ver = ""
        self.uek_ver = ""
        self.hw_vendor = ""
        self.hw_product = ""
        self.hw_asset_tag = ""

        self._populate_meminfo()       # memory info into global_vars
        self._populate_os_version()    # os_major, os_minor
        self._populate_kernel_info()   # uek_ver
        self._populate_hw_info()       # vendor, product, asset tag
        self._populate_virt_guest()    # virtualized host
        self._populate_cpu()           # cores, loigcal units, hypervisor
        self._check_exadata()          # exadata flag
        self._check_ovs_server()       # OVS server flag
        self._populate_global_vars()
        INTERNAL.debug(f"Global vars: {global_vars}")

    def get_os_major(self) -> int:
        """Returns OS major version"""
        return self.os_major

    def get_os_minor(self) -> int:
        """Returns OS minor version"""
        return self.os_minor

    def get_uek_ver(self) -> str:
        """Returns UEK kernel version"""
        return self.uek_ver

    def get_kernel_ver(self) -> str:
        """Returns kernel version"""
        return self.uek_ver

    def get_hw_vendor(self) -> str:
        """Returns system hardware vendor"""
        return self.hw_vendor

    def get_hw_product(self) -> str:
        """Returns system hardware product"""
        return self.hw_product

    def get_hw_asset_tag(self) -> str:
        """Returns system hw asset tag"""
        return self.hw_asset_tag

    def get_role(self) -> str:
        """Returns role (e.g. oci node, bare metal, exadata host, etc)"""
        if self.virt_guest:
            if self.hw_product == "HVM domU":
                return "OVM_host"
            if self.hw_asset_tag == "OracleCloud.com":
                return "OCI_guest"
            if self.exadata:
                return "Exadata_guest"
        else:
            if self.ovs_server:
                return "OVS_server"
            if self.exadata:
                return "Exadata_host"
            return "Baremetal"
        return ""

    def get_exadata(self) -> bool:
        """Returns true if an Exadata system otherwise false"""
        return self.exadata

    def get_virt_guest(self) -> bool:
        """Returns true if virt guest otherwise false"""
        return self.virt_guest

    def _populate_global_vars(self):
        global_vars["HOST_OS_MAJOR"] = self.os_major
        global_vars["HOST_OS_MINOR"] = self.os_minor
        global_vars["HOST_EXADATA"] = int(self.exadata)
        global_vars["HOST_VIRT"] = int(self.virt_guest)
        global_vars["HOST_UEK_VER"] = self.uek_ver
        global_vars["HOST_KERNEL_VER"] = self.kernel_ver
        global_vars["HOST_HW_VENDOR"] = self.hw_vendor
        global_vars["HOST_HW_PRODUCT"] = self.hw_product
        global_vars["HOST_HW_ASSET_TAG"] = self.hw_asset_tag
        global_vars["HOST_HW_EXADATA"] = self.exadata
        global_vars["HOST_ROLE"] = self.get_role()

    def _populate_meminfo(self):
        """
        Read memory info from /proc/meminfo or equivalent
        and store in global_vars.
        """
        meminfo_file = open_file(self.base_path, "/proc/meminfo")
        if not meminfo_file:
            EXTERNAL.error("Unable to load meminfo")
            return

        for line in meminfo_file:
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue
            key = parts[0].strip()
            val_str = parts[1].strip()
            # Remove any unit suffix (e.g. kB) and convert to
            # bytes as integer if possible
            val_tokens = val_str.split()
            if not val_tokens:
                continue
            try:
                value = int(val_tokens[0])
                if len(val_tokens) > 1 and val_tokens[1] == "kB":
                    value = value * 1024
            except ValueError:
                # if not an integer, store the string
                value = val_tokens[0]
            key = re.sub(r"[^\w]", "_", key)
            if key.endswith("_"):
                key = key[:-1]
            global_vars[key] = value

    def _populate_cpu(self):
        """Parse /proc/cpuinfo and extract CPU info"""
        cpuinfo = []
        cpu = {}

        try:
            with open_file(self.base_path, "/proc/cpuinfo") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        if cpu:
                            cpuinfo.append(cpu)
                            cpu = {}
                        continue

                    if ":" in line:
                        k, v = [s.strip() for s in line.split(":", 1)]
                        cpu[k] = v
            if cpu:
                cpuinfo.append(cpu)
        except Exception as e:
            EXTERNAL.error(f"Failed to parse /proc/cpuinfo: {e}")
            return

        physical_cores = set()

        for proc in cpuinfo:
            phys_id = proc.get("physical id", proc.get("processor", "0"))
            core_id = proc.get("core id", proc.get("processor", "0"))
            physical_cores.add((phys_id, core_id))

        global_vars["HOST_CPU_CORES"] = len(physical_cores)
        global_vars["HOST_CPU_LOGICAL"] = len(cpuinfo)

    def _populate_os_version(self):
        """Parse /etc/os-release to set os_major and os_minor."""
        os_release_file = open_file(self.base_path, "/etc/os-release")
        if not os_release_file:
            EXTERNAL.error("Unable to read /etc/os-release")
            return
        version_id = None

        for line in os_release_file:
            # Look for a line like VERSION_ID="8.7" or VERSION_ID=8.7
            if line.strip().startswith("VERSION_ID"):
                # Format could be VERSION_ID="8.7" or VERSION_ID=8.7
                parts = line.split("=", 1)
                if len(parts) < 2:
                    continue
                version_id = parts[1].strip().strip('"').strip("'")
                break

        if version_id:
            # Split major.minor (e.g. "7.9" -> ["7","9"] or "8" -> ["8", "0"])
            ver_parts = version_id.split(".")
            try:
                self.os_major = int(ver_parts[0])
            except ValueError:
                self.os_major = ""
            if len(ver_parts) > 1:
                try:
                    self.os_minor = int(ver_parts[1])
                except ValueError:
                    self.os_minor = ""
            else:
                # If no minor version in string, set minor to 0
                self.os_minor = 0

    def _populate_kernel_info(self):
        """Obtain kernel (UEK) version string and store in uek_ver."""
        if self.base_path == "/":
            # Live system: use os.uname()
            try:
                uname = os.uname()
                if hasattr(uname, "release"):
                    kernel_release = uname.release
                else:
                    kernel_release = uname[2]
            except Exception:
                kernel_release = ""
        else:
            kernel_release = ""
            uname_file = open_file(self.base_path,
                                   "/sos_commands/kernel/uname_-a")
            if uname_file:
                with uname_file as uf:
                    line = uf.readline().strip()
                    if line:
                        tokens = line.split()
                        if len(tokens) >= 3:
                            kernel_release = tokens[2]
        self.kernel_ver = kernel_release
        self.uek_ver = get_uek_ver(kernel_release)

    def _populate_hw_info(self):
        """
        Gather hardware info: vendor, product, asset tag
        via DMI or dmidecode.
        """
        if self.base_path == "/":
            # Live system: read from /sys/class/dmi/id/ files
            vendor_file = open_file(self.base_path,
                                    "/sys/class/dmi/id/sys_vendor")
            if vendor_file:
                self.hw_vendor = vendor_file.read().strip() or ""

            product_file = open_file(self.base_path,
                                     "/sys/class/dmi/id/product_name")
            if product_file:
                self.hw_product = product_file.read().strip() or ""

            asset_file = open_file(self.base_path,
                                   "/sys/class/dmi/id/chassis_asset_tag")
            if asset_file:
                self.hw_asset_tag = asset_file.read().strip() or ""
        else:
            # sosreport: parse dmidecode output if available
            dmidecode_file = open_file(self.base_path,
                                       "/sos_commands/hardware/dmidecode")
            if not dmidecode_file:
                EXTERNAL.error("Unable to read demidecode output")
                return

            vendor = product = asset = ""
            in_sysinfo = in_chassis = in_oem = False
            with dmidecode_file as df:
                for raw_line in df:
                    line = raw_line.strip()
                    if not line:
                        # blank line indicates end of a section
                        in_sysinfo = in_chassis = in_oem = False
                        continue
                    if line.startswith("System Information"):
                        in_sysinfo = True
                        in_oem = False
                        in_chassis = False
                        continue
                    if line.startswith("Chassis Information"):
                        in_chassis = True
                        in_oem = False
                        in_sysinfo = False
                        continue
                    if line.startswith("OEM-specific Type"):
                        in_oem = True
                        in_chassis = False
                        in_sysinfo = False
                    if in_sysinfo:
                        if line.startswith("Manufacturer:"):
                            vendor = line.split(":", 1)[1].strip() or ""
                        elif line.startswith("Product Name:"):
                            product = line.split(":", 1)[1].strip() or ""
                    if in_chassis:
                        if line.startswith("Asset Tag:"):
                            asset = line.split(":", 1)[1].strip() or ""
                    if in_oem:
                        if "Exadata" in line:
                            self.exadata = True

            self.hw_vendor = vendor
            self.hw_product = product
            self.hw_asset_tag = asset

    def _populate_virt_guest(self):
        product = self.hw_product.lower()
        vendor = self.hw_vendor.lower()

        products = ["vmware", "kvm", "standard pc", "virtual machine",
                    "virtualbox", "xen", "aws"]
        vendors = ["vmware", "qemu", "microsoft",
                   "innotek", "xen", "amazon"]
        p_match = any(p in product or product in p for p in products)
        v_match = any(v in vendor or vendor in v for v in vendors)
        self.virt_guest = self.virt_guest or p_match or v_match

    def _check_exadata(self):
        """
        Set self.exadata True if this host appears to be
        part of an Oracle Exadata system.
        """
        if self.hw_product.startswith("ORACLE SERVER X"):
            self.exadata = True
            return

        exadata_path = "/etc/tmpfiles.d/exadata.conf"
        if self.base_path != "/":
            exadata_path = f"{self.base_path}{exadata_path}"
        try:
            if os.path.exists(exadata_path):
                self.exadata = True
        except Exception:
            pass

    def _check_ovs_server(self):
        """
        Set self.ovs_server True if this host appears to be
        an OVS server host
        """
        ovs_path = "/etc/ovs-release"
        if self.base_path != "/":
            ovs_path = f"{self.base_path}/{ovs_path}"

        try:
            if os.path.exists(ovs_path):
                self.ovs_server = True
        except Exception:
            pass
