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

"""OS Health Checker plugin loader"""

import os
import importlib
import inspect

from typing import Dict

from oscheck.plugins.base import OSCheckPlugin


def load_plugins() -> Dict[str, OSCheckPlugin]:
    """Load all available OS Health checker plugins"""
    plugins = {}
    plugin_dir = os.path.dirname(__file__)

    for f in os.listdir(plugin_dir):
        if f.endswith(".py") and not f.startswith("__"):
            if f == "base.py":
                continue
            plugin_name = f"oschecker.modules.{f[:-3]}"
            try:
                module = importlib.import_module(plugin_name)

                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, OSCheckPlugin) \
                       and obj is not OSCheckPlugin:
                        instance = obj()
                        plugins[instance.name] = instance
                    else:
                        raise Exception(
                            f"Incompatible plugin class {instance.name}")
            except Exception as e:
                print(f"Failed to load plugin {plugin_name}: {e}")

    return plugins
