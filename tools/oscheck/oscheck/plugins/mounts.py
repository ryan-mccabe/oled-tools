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

"""Mounts plugin for OS Health Checker"""

import logging
import fnmatch

from typing import Dict, List

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core import engine
from oscheck.core.util import open_file

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


class MountsPlugin(OSCheckPlugin):
    """Plugin for /etc/fstab and /proc/mounts"""
    @property
    def name(self):
        return "mounts"

    def run(self, rules, base_path="/") -> int:
        mounts = self._parse_proc_mounts(base_path)
        fstab = self._parse_fstab(base_path)
        all_entries = mounts + fstab

        req_attr_dict = {
            k: engine.get_required_attributes(rule)
            for k, rule in rules.items()
        }

        matched = set()
        errors = 0

        for entry in all_entries:
            mnt = entry.get("mountpoint")
            if not mnt:
                continue

            for pattern, rule in rules.items():
                if fnmatch.fnmatch(mnt, pattern):
                    matched.add(pattern)
                    req_attrs = req_attr_dict.get(pattern, [])
                    filtered = {
                        k: v for k, v in entry.items() if k in req_attrs
                    }

                    context = f"MOUNT {mnt} ({entry['source']})"
                    fatal_err = []
                    passed, failures = engine.validate_rule(
                        filtered, rule, mnt, context,
                        fatal_err=fatal_err
                    )

                    if passed and not fatal_err:
                        EXTERNAL.info(f"✅ {context} passed all checks")
                    else:
                        EXTERNAL.error(f"❌ {context} failed validation")
                        for f in failures + fatal_err:
                            # XXX - HACK - the engine should not report
                            # one part of an 'or' short-circuiting as an error
                            # to the user, even though it handles the eval
                            # correctly
                            if f == str(rule):
                                continue
                            errors = errors + 1
                            EXTERNAL.error(f"  ↳ {f}")
        for pattern in rules:
            if pattern not in matched:
                errors = errors + 1
                EXTERNAL.error(
                    f"❌ MOUNT {pattern}: no matching mount found")
        return errors

    def _parse_proc_mounts(self, base_path: str) -> List[Dict[str, any]]:
        try:
            with open_file(base_path, "/proc/mounts") as f:
                return [self._parse_mount_line(
                    line, "mounts") for line in f if line.strip()]
        except Exception as e:
            EXTERNAL.error(f"Error reading /proc/mounts: %s", e)
            return []

    def _parse_fstab(self, base_path: str) -> List[Dict[str, any]]:
        f = open_file(base_path, "/etc/fstab")
        if not f:
            return []

        out = []
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parts = line.split()
                if len(parts) < 6:
                    continue
                out.append({
                    "exists": True,
                    "device": parts[0],
                    "mountpoint": parts[1],
                    "fstype": parts[2],
                    "options": set(parts[3].split(",")),
                    "dump": parts[4],
                    "pass": parts[5],
                    "source": "fstab"
                })
            except Exception as e:
                EXTERNAL.error(f"Unable to parse fstab line: {line}: {e}")
        return out

    def _parse_mount_line(self, line: str, source: str) -> Dict[str, any]:
        try:
            parts = line.split()
            if len(parts) < 6:
                return {}
            return {
                "exists": True,
                "device": parts[0],
                "mountpoint": parts[1],
                "fstype": parts[2],
                "options": set(parts[3].split(",")),
                "dump": parts[4],
                "pass": parts[5],
                "source": source
            }
        except Exception as e:
            EXTERNAL.error(f"Unable to parse mount line: {line}: {e}")
            return {}
