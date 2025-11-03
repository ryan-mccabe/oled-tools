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

"""sysctl OS Health Checker plugin"""

import os
import fnmatch
import logging
import subprocess

from typing import Any, Dict

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core import engine
from oscheck.core.util import open_file, list_files, parse_kv_file

JsonDict = Dict[str, Any]

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


class SysctlCollector:
    """
    Collects sysctl values and config from either
    a live system or a sosreport directory.
    """

    def __init__(self, base_path="/"):
        """
        Initialize the collector.

        :param base_path: "/" for live system, or sosreport root directory.
        """
        self.base_path = base_path
        self.live_data: Dict[str, Any] = {}
        self.config_data: Dict[str, Dict[str, Any]] = {}

    def collect(self):
        """
        Collect both live and configured sysctl values,
        depending on whether using a live system or sosreport.
        """
        if self.base_path == "/":
            self._collect_live_sysctl()
        else:
            self._collect_sosreport_sysctl()

        self._collect_config_files()

    def _parse_sysctl_output(self, output: str):
        """
        Parse output from `sysctl -a` or sosreport and populate live_data.

        :param output: Raw sysctl output.
        """
        for line in output.splitlines():
            if "=" in line:
                k, v = map(str.strip, line.split("=", 1))
                try:
                    self.live_data[k] = int(v)
                except ValueError:
                    self.live_data[k] = v

    def _collect_live_sysctl(self):
        """
        Collect sysctl values using `sysctl -a` on the live system.
        """
        INTERNAL.debug("Getting sysctl -a output from command")
        try:
            output = subprocess.run(
                ["sysctl", "-a"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                universal_newlines=True
            ).stdout.strip()
            self._parse_sysctl_output(output)
        except subprocess.CalledProcessError as e:
            EXTERNAL.error(f"Unable to run 'sysctl -a': {e}")

    def _collect_sosreport_sysctl(self):
        """
        Collect sysctl values from a sosreport file.
        """
        path = "sos_commands/kernel/sysctl_-a"

        INTERNAL.debug(f"Getting sysctl -a output from file {path}")
        f = open_file(self.base_path, path)
        if not f:
            EXTERNAL.error(f"No sysctl -a output at {path}")
            return
        content = f.read()
        if content:
            self._parse_sysctl_output(content)

    def _collect_config_files(self):
        """
        Collect sysctl config values from live files or sosreport files.
        """
        config_files = [os.path.join(self.base_path, "etc/sysctl.conf")]
        config_files.extend(list_files(
            self.base_path, "etc/sysctl.d",
            suffix=".conf"
        ))

        for path in config_files:
            if not os.path.exists(path):
                INTERNAL.debug(f"{path} does not exist, skipping")
                continue

            INTERNAL.debug(f"Reading configured sysctl data from {path}")
            result = parse_kv_file(path, sep="=")
            if result:
                self.config_data[path] = result
            else:
                INTERNAL.debug(f"No config data in file {path}")

    def get_live(self) -> Dict[str, Any]:
        """
        Return sysctl values from `sysctl -a` or sosreport file.
        """
        return self.live_data

    def get_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Return parsed sysctl config values from config files or sosreport.
        """
        return self.config_data


def validate_sysctl_sources(rules: JsonDict,
                            live_sysctl: Dict[str, Any],
                            config_sources: Dict[str, Dict[str, Any]]) -> int:
    """
    Validate sysctl keys against rules using both live values
    and config file definitions. Report validation failures with context.
    """
    errors = 0
    for pattern, rule in rules.items():
        matching_keys = [k for k in live_sysctl if fnmatch.fnmatch(k, pattern)]
        found_key = bool(matching_keys)

        # Live sysctl values
        for k in matching_keys:
            INTERNAL.debug(f"Evaluating live sysctl key {k}")
            fatal_err = []
            result, failures = engine.validate_rule(
                live_sysctl[k], rule, k,
                f"LIVE SYSCTL {k}",
                fatal_err=fatal_err
            )
            if not result or fatal_err:
                errors = errors + 1
                EXTERNAL.error(f"❌ LIVE SYSCTL: {k} failed validation")
                for failure in failures + fatal_err:
                    EXTERNAL.error(f"  ↳ {failure}")
            else:
                EXTERNAL.info(f"✅️ LIVE SYSCTL {k} passed all checks.")

        # Config values from individual files
        for path, file_dict in config_sources.items():
            for k, v in file_dict.items():
                if fnmatch.fnmatch(k, pattern):
                    found_key = True
                    INTERNAL.debug(f"Evaluating sysctl config {k} from {path}")
                    fatal_err = []
                    result, failures = engine.validate_rule(
                        v, rule, k,
                        f"CONFIG SYSCTL {k} from {path}",
                        fatal_err=fatal_err
                    )
                    if not result or fatal_err:
                        errors = errors + 1
                        EXTERNAL.error(
                            f"❌ CONFIG SYSCTL: {k} from {path} "
                            "failed validation"
                        )
                        for failure in failures + fatal_err:
                            EXTERNAL.error(f"  ↳ {failure}")
                    else:
                        EXTERNAL.info(
                            f"✅️ CONFIG SYSCTL {k} from {path} "
                            "passed all checks")

        # Report missing sysctls as failure
        if not found_key:
            errors = errors + 1
            EXTERNAL.error(
                f"❌ SYSCTL: {pattern} is missing from sysctl sources")
    return errors


class SysctlPlugin(OSCheckPlugin):
    """Sysctl checker plugin"""

    @property
    def name(self):
        return "sysctl"

    def run(self, rules, base_path="/") -> int:
        """
        Execute the plugin to validate sysctl settings.

        :param rules: The rules block under "sysctl" in the input JSON.
        :param base_path: "/" for live system or path to sosreport.
        """
        c = SysctlCollector(base_path=base_path)
        c.collect()
        return validate_sysctl_sources(rules, c.get_live(), c.get_config())
