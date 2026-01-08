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

"""Base class for OS Health Checker plugins"""

from abc import ABC, abstractmethod


class OSCheckPlugin(ABC):
    """
    Abstract base class for all OS health checker plugins.
    Plugins must implement the `run()` method and `name` property.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the plugin, used to match rule keys in the json."""

    @abstractmethod
    def run(self, rules: dict, base_path=None) -> int:
        """
        Execute validation logic based on provided rules
        and whether we're running against a live system or
        something like sosreport output.

        Returns the number of failures.
        """
