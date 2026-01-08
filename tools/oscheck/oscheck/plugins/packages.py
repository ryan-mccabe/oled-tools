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

"""Package checker plugin"""

import os
import fnmatch
import re
import subprocess
import logging

from typing import Dict, Any, List, Optional, Tuple

import rpm

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core import engine
from oscheck.core.util import open_file

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


def _package_gt(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) > 0


def _package_ge(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) >= 0


def _package_lt(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) < 0


def _package_le(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) <= 0


def _package_eq(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) == 0


def _package_ne(l: str, r: str):
    left = evr_to_tuple(l)
    right = evr_to_tuple(r)
    return rpm.labelCompare(left, right) != 0


package_ops = {
    "package_gt": _package_gt,
    "package_ge": _package_ge,
    "package_lt": _package_lt,
    "package_le": _package_le,
    "package_eq": _package_eq,
    "package_ne": _package_ne
}


def _parse_rpm_name(rpmname: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Parses an RPM name into a 4-tuple: (name, version, release, arch)
    Example:
      'kernel-tools-libs-4.18.0-553.50.1.el8_10.x86_64' ->
        ('kernel-tools-libs', '4.18.0', '553.50.1.el8_10', 'x86_64')
    """
    pattern = (
        r"^(?P<name>.+)-"
        r"(?P<version>[^-]+)-"
        r"(?P<release>[^-]+)\."
        r"(?P<arch>[^.]+)$"
    )
    match = re.match(pattern, rpmname)
    if match:
        return (
            match.group("name"),
            match.group("version"),
            match.group("release"),
            match.group("arch")
        )
    return None


def _parse_package_data(pdata: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parses RPM package info content into a structured dictionary"""
    packages = {}
    for line in pdata.splitlines():
        line = line.strip()
        if "\t" in line:
            parts = line.split("\t")
            if len(parts) < 7:
                INTERNAL.debug(f"Malformed pkg line: {line}")
                continue

            rpmname = parts[0]
            try:
                (name, version, release, arch) = _parse_rpm_name(rpmname)
                if not name:
                    raise ValueError(f"Name not found for {rpmname}")
            except Exception as e:
                INTERNAL.debug(f"Malformed pkg name: {rpmname}: {e}")
                continue

            val = {
                "exists": True,
                "name": name,
                "version": f"{version}-{release}",
                "ver": version,
                "release": release,
                "arch": arch,
                "rpm": rpmname,
                "installdate": parts[1],
                "installtime": parts[2],
                "vendor": parts[3],
                "buildhost": parts[4],
                "signature": parts[5],
                "key": parts[6]
            }

            # Some packages can have multiple versions installed
            packages.setdefault(name, []).append(val)

    # INTERNAL.debug(f"Returning packages = {packages}")
    return packages


def _get_pkgs_installed(base_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run dnf/yum on live system, or read from sosreport path.
    """
    content = None
    if base_path == "/":
        try:
            result = subprocess.run(["/usr/bin/dnf", "list", "installed"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True,
                                    universal_newlines=True)
            content = result.stdout
        except FileNotFoundError:
            try:
                result = subprocess.run(["/usr/bin/yum", "list", "installed"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        check=True,
                                        universal_newlines=True)
                content = result.stdout
            except Exception as e:
                print(f"Error running yum: {e}")
        except Exception as e:
            print(f"Error running dnf: {e}")
    else:
        sos_paths = [
            os.path.join(base_path, "sos_commands/dnf/dnf_list_installed"),
            os.path.join(base_path, "sos_commands/yum/yum_list_installed"),
        ]
        for path in sos_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        content = f.read()
                        break
                except Exception as e:
                    print(f"Failed to read {path}: {e}")
    if not content:
        return {}
    return _parse_pkgs_installed(content.strip())


def evr_to_tuple(evr: str) -> Tuple[str, str, str]:
    """
    Convert an evr epoch:version-release or version-release
    string to a 3-tuple. Sets any missing element to ""
    """

    if ":" in evr:
        epoch, version = evr.split(":", 1)
    else:
        version = evr
        epoch = ""

    if "-" in version:
        version, release = version.split("-", 1)
    else:
        release = ""

    return (epoch, version, release)


def _parse_pkgs_installed(content: str) -> Dict[str, List[Dict[str, Any]]]:
    packages = {}
    for line in content.splitlines():
        if not line.strip():
            continue
        if line.startswith("Installed Packages"):
            continue
        fields = line.split()
        if len(fields) < 3:
            continue
        name_arch, version, repo = fields[-3:]
        if "." not in name_arch:
            continue
        name, arch = name_arch.rsplit(".", 1)

        (epoch, ver, rel) = evr_to_tuple(version)
        if epoch:
            evr = f"{epoch}:{ver}-{rel}"
        else:
            evr = f"{ver}-{rel}"

        val = {
            "exists": True,
            "name": name,
            "version": f"{ver}-{rel}",
            "ver": ver,
            "epoch": epoch,
            "evr": evr,
            "release": rel,
            "arch": arch,
            "repo": repo
        }

        packages.setdefault(name, []).append(val)
    return packages


def _get_live_rpms() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get live package data in a format that matches what sosreport collects
    """
    cmd = ["rpm", "--nodigest", "-qa", "--queryformat",
           "%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\\t"
           "%{INSTALLTIME:date}\\t%{INSTALLTIME}\\t"
           "%{VENDOR}\\t%{BUILDHOST}\\t"
           "%{SIGPGP}\\t%{SIGPGP:pgpsig}\\n"]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            universal_newlines=True
        )
        return _parse_package_data(result.stdout)
    except Exception as e:
        EXTERNAL.error(f"Failed to run rpm command: {e}")
        return {}


def _get_sosreport_rpms(base_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse package-data file from sosreport"""
    path = "sos_commands/rpm/package-data"
    f = open_file(base_path, path)
    if not f:
        EXTERNAL.error(f"Unable to open sosreport package data: {path}")
        return {}
    return _parse_package_data(f.read())


def _get_rpms_installed(base_path: str) -> Dict[str, List[Dict[str, Any]]]:
    if base_path == "/":
        return _get_live_rpms()
    return _get_sosreport_rpms(base_path)


def _merge_pkg_data(
        rpm_pkgs: Dict[str, List[Dict[str, Any]]],
        pkg_list: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    result = {}

    # Build reverse index of rpm_pkgs by (name, version, arch)
    rpm_index = {}
    for name, entries in rpm_pkgs.items():
        for entry in entries:
            key = (name, entry.get("version"), entry.get("arch"))
            rpm_index[key] = entry

    seen_keys = set()

    # Merge data from pkg_list, augment with matching rpm data
    for name, entries in pkg_list.items():
        merged_entries = []
        for entry in entries:
            key = (name, entry.get("version"), entry.get("arch"))
            seen_keys.add(key)
            rpm_data = rpm_index.get(key)
            if rpm_data:
                # Merge all keys from rpm_data not already in entry
                for k, v in rpm_data.items():
                    if k not in entry:
                        entry[k] = v
                    else:
                        if entry[k] != v:
                            INTERNAL.debug(
                                f"mismatch {entry[k]} vs {v} for {name}"
                            )
            else:
                EXTERNAL.warning(
                    f"Package {name}-{entry.get('version')}."
                    f"{entry.get('arch')} found in dnf/yum but "
                    "missing in rpm/package-data"
                )
            merged_entries.append(entry)
        result[name] = merged_entries

    # Log any entries in rpm data that weren't in dnf/yum
    for name, entries in rpm_pkgs.items():
        for entry in entries:
            key = (name, entry.get("version"), entry.get("arch"))
            if key not in seen_keys:
                EXTERNAL.debug(
                    f"Package {name}-{entry.get('version')}."
                    f"{entry.get('arch')} found in rpm/package-data but "
                    "missing in dnf/yum list"
                )
    return result


class PackagesPlugin(OSCheckPlugin):
    """Packages checker plugin"""

    @property
    def name(self):
        return "packages"

    def run(self, rules: Dict[str, Any],
            base_path: Optional[str] = "/") -> int:
        packages_rpm = _get_rpms_installed(base_path)
        packages_list = _get_pkgs_installed(base_path)
        packages = _merge_pkg_data(packages_rpm, packages_list)

        fails = 0
        for pattern, condition in rules.items():
            matched = [p for name in packages
                       if fnmatch.fnmatch(name, pattern)
                       for p in packages[name]]

            if not matched:
                dummy = {"exists": False}
                context = f"PACKAGE {pattern} (not installed)"
                fatal_err = []
                passed, failures = engine.validate_rule(
                    dummy, condition, pattern,
                    context, fatal_err=fatal_err,
                    plugin_ops=package_ops
                )
                if passed and not fatal_err:
                    EXTERNAL.info(f"✅ {context} passed all checks")
                else:
                    EXTERNAL.error(f"❌ {context} failed validation")
                    for f in failures + fatal_err:
                        EXTERNAL.error(f"  ↳ {f}")
                    fails += 1
                continue

            for entry in matched:
                context = f"PACKAGE {entry['name']} {entry['version']}"
                req_attrs = engine.get_required_attributes(condition)
                filtered = {k: v for k, v in entry.items() if k in req_attrs}
                fatal_err = []
                passed, failures = engine.validate_rule(
                    filtered, condition, pattern,
                    context, fatal_err=fatal_err,
                    plugin_ops=package_ops
                )
                if passed and not fatal_err:
                    EXTERNAL.info(f"✅ {context} passed all checks")
                else:
                    EXTERNAL.error(f"❌ {context} failed validation")
                    for f in failures + fatal_err:
                        EXTERNAL.error(f"  ↳ {f}")
                    fails += 1
        return fails
