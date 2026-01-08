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

"""/proc/cmdline OS Health Checker plugin"""


import logging

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core.util import open_file, parse_kv_str
from oscheck.core import engine

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


class CmdlinePlugin(OSCheckPlugin):
    """Kernel cmdline checker plugin"""

    @property
    def name(self):
        return "cmdline"

    def run(self, rules, base_path="/") -> int:
        path = "/proc/cmdline"
        f = open_file(base_path, path)
        if not f:
            EXTERNAL.error(f"❌ {path} missing or unreadable")
            return 1

        line = f.read().strip()
        attributes = parse_kv_str(line, sep="=", include_bare_keys=True)

        req_attrs = engine.get_required_attributes(rules)
        for attr in req_attrs:
            if attr not in attributes:
                attributes[attr] = None

        fails = 0
        for rule_key, rule_val in rules.items():
            context = f"CMDLINE rule {rule_key}"
            fatal_err = []
            passed, failures = engine.validate_rule(
                attributes, {rule_key: rule_val}, rule_key, context,
                fatal_err=fatal_err,
                allow_missing_attrs=True
            )
            if passed and not fatal_err:
                EXTERNAL.info(f"✅ {context} passed all checks")
            else:
                fails += 1
                EXTERNAL.error(f"❌ {context} failed validation")
                for f in failures + fatal_err:
                    EXTERNAL.error(f"  ↳ {f}")
        return fails
