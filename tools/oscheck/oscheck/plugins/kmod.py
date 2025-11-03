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

"""Kernel modules checker plugin"""

import logging
from typing import Dict, Any

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core.util import open_file
from oscheck.core import engine

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


def _parse_modules(base_path: str) -> Dict[str, Dict[str, Any]]:
    f = open_file(base_path, "/proc/modules")
    if not f:
        EXTERNAL.error("Could not read /proc/modules")
        return {}

    modules = {}
    for line in f:
        try:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            name, size, usage_count, used_by, state, offset = parts[:6]
            modules[name] = {
                "exists": True,
                "size": int(size),
                "usage_count": int(usage_count),
                "used_by": used_by.split(",") if used_by != "-" else [],
                "state": state.lower(),
                "offset": offset
            }
        except Exception as e:
            ls = line.strip()
            EXTERNAL.error(
                f"Failed to parse line in /proc/modules: {ls}: {e}")
    return modules


class KernelModulesPlugin(OSCheckPlugin):
    """Kernel modules plugin"""
    @property
    def name(self) -> str:
        return "kmod"

    def run(self, rules: Dict[str, Any], base_path: str = "/") -> int:
        modules = _parse_modules(base_path)
        errors = 0

        for pattern, rule in rules.items():
            for modname, attributes in modules.items():
                if modname == pattern:
                    context = f"KERNEL MODULE {modname}"
                    req_attrs = engine.get_required_attributes(rule)
                    filtered = {k: v for k, v in attributes.items()
                                if k in req_attrs}
                    fatal_err = []
                    passed, failures = engine.validate_rule(
                        filtered, rule, modname, context,
                        fatal_err=fatal_err,
                        allow_missing_attrs=True
                    )
                    if passed and not fatal_err:
                        EXTERNAL.info(f"✅ {context} passed all checks")
                    else:
                        errors += 1
                        EXTERNAL.error(f"❌ {context} failed validation")
                        for f in failures + fatal_err:
                            EXTERNAL.error(f"  ↳ {f}")
                    break
            else:
                context = f"KERNEL {pattern} (not loaded)"
                dummy = {"exists": False}
                fatal_err = []
                passed, failures = engine.validate_rule(
                    dummy, rule, pattern, context,
                    fatal_err=fatal_err,
                    allow_missing_attrs=True
                )
                if passed and not fatal_err:
                    EXTERNAL.info(f"✅ {context} passed all checks")
                else:
                    errors += 1
                    EXTERNAL.error(f"❌ {context} failed validation")
                    for f in failures + fatal_err:
                        EXTERNAL.error(f"  ↳ {f}")
        return errors
