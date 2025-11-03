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

"""systemd OS Health Checker plugin"""

import fnmatch
import logging
import subprocess

from typing import Any, Dict, List

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core import engine
from oscheck.core.util import open_file

JsonDict = Dict[str, Any]

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


class SystemdCollector:
    """Collects systemd unit metadata from live system or sosreport."""
    def __init__(self, base_path: str = "/"):
        self.base_path = base_path
        self.unit_attrs: Dict[str, Dict[str, str]] = {}

    def collect(self):
        """Collect unit attributes from systemctl -a output."""
        raw = self._get_systemctl_output()
        self._parse_unit_output(raw)

    def _get_systemctl_output(self) -> str:
        """Return output of systemctl -a from live or sosreport."""
        if self.base_path == "/":
            try:
                cmd = ["systemctl", "list-units", "--all",
                       "--no-legend", "--no-pager"]
                out = subprocess.run(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     check=True,
                                     universal_newlines=True)
                return out.stdout.strip()
            except Exception as e:
                cmd_str = " ".join(cmd)
                EXTERNAL.error(f"Error running '{cmd_str}': {e}")
                return ""
        else:
            rel_path = "sos_commands/systemd/systemctl_list-units_--all"
            INTERNAL.debug(f"Reading unit attributes from {rel_path}")
            content = open_file(self.base_path, rel_path)
            if not content:
                EXTERNAL.error(f"Unable to read {rel_path}")
                return ""
            return content.read()

    def _parse_unit_output(self, output: str):
        """Parse output of systemctl -a and populate unit_attrs."""
        for line in output.splitlines():
            parts = line.split(None, 4)
            if len(parts) < 4:
                continue

            unit = parts[0]
            load = parts[1]
            active = parts[2]
            sub = parts[3]
            description = parts[4] if len(parts) > 4 else ""

            self.unit_attrs[unit] = {
                "unit": unit,
                "load": load,
                "active": active,
                "sub": sub,
                "description": description,
                "exists": "1",
                "state": f"{active}/{sub}"
            }

    def get_required_attributes(self,
                                unit: str,
                                required: List[str]) -> Dict[str, str]:
        """Return dict of only required attributes for @unit."""
        full = self.unit_attrs.get(unit, {})
        return {k: full[k] for k in required if k in full}

    def get_unit_names(self) -> List[str]:
        """Return a list of all discovered unit names"""
        return list(self.unit_attrs.keys())


def validate_systemd(rules: JsonDict, collector: SystemdCollector):
    """Validate rules for systemd units."""
    errors = 0
    for pattern, rule in rules.items():
        matched_units = [
            unit for unit in collector.get_unit_names()
            if fnmatch.fnmatch(unit, pattern)
        ]

        # If no units matched, create a dummy entry for the pattern
        # so we can handle rules like { "not": { "exists: 1 } }
        if not matched_units:
            INTERNAL.debug(
                f"{pattern} not found in unit list, evaluating rule anyway")
            context = f"SYSTEMD UNIT {pattern} (not found)"
            attrs = {"exists": 0}
            fatal_err = []
            passed, failures = engine.validate_rule(
                attrs, rule, "systemd", context,
                fatal_err=fatal_err
            )
            if passed and not fatal_err:
                EXTERNAL.info(f"✅ {context} passed all checks")
            else:
                errors = errors + 1
                EXTERNAL.error(f"❌ {context} failed validation")
                for f in failures + fatal_err:
                    EXTERNAL.error(f"  ↳ {f}")
            continue

        req_attr = engine.get_required_attributes(rule)
        for unit in matched_units:
            attrs = collector.get_required_attributes(unit, req_attr)
            if not attrs:
                errors = errors + 1
                EXTERNAL.error(
                    f"❌ SYSTEMD: {unit} attributes missing or unreadable")
                continue

            context = f"SYSTEMD UNIT {unit}"
            fatal_err = []
            passed, failures = engine.validate_rule(
                attrs, rule, "systemd", context,
                fatal_err=fatal_err
            )
            if passed and not fatal_err:
                EXTERNAL.info(f"✅ {context} passed all checks")
            else:
                errors = errors + 1
                EXTERNAL.error(f"❌ {context} failed validation")
                for f in failures + fatal_err:
                    EXTERNAL.error(f"  ↳ {f}")
    return errors


class SystemdPlugin(OSCheckPlugin):
    """Systemd checker plugin"""

    @property
    def name(self):
        return "systemd"

    def run(self, rules, base_path="/") -> int:
        """
        Run validation for systemd units.

        :param rules: The JSON rules block under "systemd".
        :param base_path: "/" or root of sosreport.
        """
        c = SystemdCollector(base_path=base_path)
        c.collect()
        return validate_systemd(rules, c)
