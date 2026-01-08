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

"""Utility functions useful in various places"""

import io
import os
import hashlib
import logging

from typing import Optional, List, Dict, Union

EXTERNAL = logging.getLogger("oschecker.external")
INTERNAL = logging.getLogger("oschecker.internal")


def open_file(base_dir: str, rel_path: str) -> io.TextIOWrapper:
    """
    open a file at base_dir + rel_path.
    """
    path = os.path.join(base_dir, rel_path.lstrip("/"))
    try:
        return open(path, "r")
    except Exception as e:
        EXTERNAL.error(f"Unable to open {path}: {e}")
        return None


def list_files(base_dir: str,
               rel_dir: str,
               suffix: Optional[str] = None) -> List[str]:
    """
    Return list of files in base_dir + rel_dir, optionally filtering
    by suffix (e.g., '.conf'). Returns an empty list on error.
    """
    dir_path = os.path.join(base_dir, rel_dir.lstrip("/"))
    try:
        files = os.listdir(dir_path)
        if suffix:
            files = [f for f in files if f.endswith(suffix)]
        return [os.path.join(dir_path, f) for f in files]
    except Exception as e:
        EXTERNAL.error(f"Unable to list directory {dir_path}: {e}")
        return []


def parse_kv_file(path: str,
                  sep: str = "=",
                  strip_quotes: bool = True,
                  include_bare_keys: bool = False) -> Dict[str, str]:
    """
    Parse key=value lines from the given string content.
    Ignores lines starting with '#' or without the separator,
    unless include_bare_keys=True, in which case bare tokens
    are treated as key=True.

    Returns a dict of key/value pairs.
    """
    result = {}
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if sep in line:
                key, value = map(str.strip, line.split(sep, 1))
                if strip_quotes and value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                result[key] = value
            elif include_bare_keys:
                result[line] = True
    return result


def parse_kv_str(content: str,
                 sep: str = "=",
                 strip_quotes: bool = True,
                 include_bare_keys: bool = False) -> Dict[str, str]:
    """
    Parse a space-delmited key=value string. Return a dict of
    dict[key] = value. If the separator is missing, if
    @include_bare_keys is True, set dict[key] = True.
    """
    result = {}
    for tok in content.strip().split():
        if sep in tok:
            key, val = tok.split(sep, 1)
            if strip_quotes and val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
        elif include_bare_keys:
            key, val = tok, True
        result[key] = val
    return result


def compute_hash(path: str) -> Optional[str]:
    """Compute SHA256 hash of file at @path."""
    if not path:
        return None

    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        EXTERNAL.error(f"sha256 hashing file {path}: {e}")
        return None


def compute_hash_from_str(contents: Union[str, bytes]) -> str:
    """Compute SHA256 hash of file @contents."""
    if not contents:
        return None

    try:
        hasher = hashlib.sha256()

        if isinstance(contents, str):
            # Convert string to bytes
            contents = contents.encode()
        hasher.update(contents)
        return hasher.hexdigest()
    except Exception as e:
        EXTERNAL.error(f"sha256 hashing string: {e}")
    return None


def get_file_contents(path: str) -> Optional[bytes]:
    """
    Return contents of @path
    """
    with open(path, "rb") as f:
        return f.read()


def compare_file_contents(expected, actual) -> bool:
    """
    Compare the contents of two files, where it's possible that
    either is bytes or str.
    """
    if isinstance(actual, bytes) and isinstance(expected, bytes):
        return actual == expected
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.strip() == expected.strip()
    if isinstance(actual, bytes):
        actual = actual.decode('utf-8')
    else:
        expected = expected.decode('utf-8')
    # XXX - do we really want to strip()?
    return actual.strip() == expected.strip()
