# Copyright (c) 2024, Oracle and/or its affiliates.
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
"""
plugin.py: defines sosdiff comparison plugins
"""
import importlib
import pkgutil
from argparse import Namespace
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple
from warnings import warn


Comparator = Callable[[str, str, Namespace], int]


_PLUGINS: Dict[str, Comparator] = {}
_LOADED = False


def _load_all_sosdiff_modules() -> None:
    global _LOADED
    if not _LOADED:
        paths = [str(Path(__file__).parent)]
        for mod in pkgutil.iter_modules(path=paths, prefix="sosdiff."):
            importlib.import_module(mod.name)
    _LOADED = True


def register(c: Comparator):
    """
    Decorator to register a function as a sosdiff plugin
    """
    prefix = "compare_"
    name = c.__name__

    if name.startswith(prefix):
        name = name[len(prefix):]

    if name in _PLUGINS:
        warn(f"Overwriting plugin with name {name}")
    _PLUGINS[name] = c


def _sort_key(value: Tuple[str, Comparator]) -> Tuple[int, str]:
    priority = 0 if value[0] == "unames" else 1
    return (priority, value[0])


def all_plugins() -> Iterable[Tuple[str, Comparator]]:
    """
    Return a every sosdiff plugin in execution order
    """
    _load_all_sosdiff_modules()
    items = _PLUGINS.items()
    return sorted(items, key=_sort_key)
