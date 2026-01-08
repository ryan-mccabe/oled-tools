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

import argparse
import json
import logging
import importlib
import pkgutil

from typing import Any, Dict

import oscheck.plugins as plugins

from oscheck.core.host import OLHost
from oscheck.plugins.base import OSCheckPlugin

JsonDict = Dict[str, Any]

LOG_FILE = "oschecker.log"

RULES_PATH = "/etc/oled/oscheck/rules/"

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


def setup_logging(debug: bool) -> None:
    """Set up OHC logging"""

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="w"),
            logging.StreamHandler()
        ]
    )


def load_plugins() -> Dict[str, OSCheckPlugin]:
    """Load all OHC plugins"""
    plugin_dict = {}

    for _, module_name, _ in pkgutil.iter_modules(plugins.__path__):
        if module_name == "base":
            continue
        full_module_name = f"oscheck.plugins.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except ModuleNotFoundError as e:
            EXTERNAL.error(
                f"Unable to load {full_module_name} due "
                f"to missing module: {e}"
            )
            continue
        except Exception as e:
            EXTERNAL.error(f"Unable to load {full_module_name}: {e}")
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) \
               and issubclass(attr, OSCheckPlugin) \
               and attr is not OSCheckPlugin:
                instance = attr()
                plugin_dict[instance.name] = instance

    return plugin_dict


def load_json_rules(rules_file: str) -> JsonDict:
    """Load and parse json @rules_file"""
    try:
        with open(rules_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Unable to load rules file {rules_file}: {e}")
        return None

def determine_rules_file(host: OLHost) -> str:
    role = host.get_role()
    major = host.get_os_major()
    default_rules = f"{role}/{major}/rules.json"
    return default_rules


def main():
    """OHC main"""
    parser = argparse.ArgumentParser(description="OS Health Checker")
    parser.add_argument("rules", nargs='?', default=None,
                        help="Path to rules json file")
    parser.add_argument("--sos",
                        metavar="sosreport_dir",
                        help="Path to sosreport directory")
    parser.add_argument("--debug",
                        action="store_true", help="Enable debug output")
    args = parser.parse_args()

    setup_logging(args.debug)

    ohc_plugins = load_plugins()

    host = OLHost(base_path=args.sos or "/")
    INTERNAL.debug(f"OS Major: {host.get_os_major()}")
    INTERNAL.debug(f"OS Minor: {host.get_os_minor()}")
    INTERNAL.debug(f"UEK version: {host.get_uek_ver()}")
    INTERNAL.debug(f"HW product: {host.get_hw_product()}")
    INTERNAL.debug(f"HW vendor: {host.get_hw_vendor()}")
    INTERNAL.debug(f"HW asset: {host.get_hw_asset_tag()}")
    INTERNAL.debug(f"HW role: {host.get_role()}")
    INTERNAL.debug(f"Exadata: {host.get_exadata()}")
    INTERNAL.debug(f"Virt Guest: {host.get_virt_guest()}")

    if args.rules:
        rules = load_json_rules(args.rules)
    else:
        rules = load_json_rules(f"{RULES_PATH}{determine_rules_file(host)}")

    if not rules:
        return 1

    for name, plugin in ohc_plugins.items():
        if name in rules:
            INTERNAL.debug(f"Running plugin: {name} with base path {args.sos}")
            err = plugin.run(rules[name], base_path=args.sos or "/")
            if err != 0:
                INTERNAL.debug(f"{err} failures running plugin {name}")

    return 0

if __name__ == "__main__":
    main()
