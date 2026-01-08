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

"""OS Health Checker files validator plugin"""

import os
import glob
import subprocess
import logging
import pwd
import grp
from typing import Any, Dict, List, Optional

import selinux

from oscheck.plugins.base import OSCheckPlugin
from oscheck.core.engine import get_file_contents, validate_rule, \
                        get_required_attributes

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


def get_xattr(path: str) -> List[str]:
    """
    Returns a list of extended attributes in the same format as `getfattr -d`,
    i.e., attr_name="attr_value"
    """
    try:
        xattrs = os.listxattr(path)
        out = []
        for attr in xattrs:
            try:
                xattr_bytes = os.getxattr(path, attr)
                try:
                    xattr_str = xattr_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    xattr_str = repr(xattr_bytes)
                out.append(f'{attr}="{xattr_str}"')
            except OSError as e:
                EXTERNAL.error(
                    f"ERROR: Unable to retrieve xattr for {path}: {e}")
        return out
    except OSError as e:
        EXTERNAL.error(f"ERROR: get_xattr: {e}")
        return []


def get_chattr_flags(path: str) -> str:
    """Retrieve chattr flags for a file."""
    try:
        chattr_output = subprocess.run(["lsattr", path],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       check=True,
                                       universal_newlines=True).stdout.strip()

        # Extract chattr flags (first field in lsattr output)
        chattr_flags = chattr_output.split()[0] if chattr_output else ""

        INTERNAL.debug(
            f"OK: Retrieved chattr flags for {path}: {chattr_flags}")
        return chattr_flags
    except subprocess.CalledProcessError:
        EXTERNAL.warning(f"No chattr flags found for {path}")
        return ""
    except FileNotFoundError:
        EXTERNAL.error(f"ERROR: get_chattr_flags: File not found: {path}")
        return ""
    except PermissionError:
        EXTERNAL.error(
            f"ERROR: get_chattr_flags: Permission denied for {path}")
        return ""
    except Exception as e:
        EXTERNAL.error(
            f"ERROR: get_chattr_flags: Failed to retrieve "
            f"chattr flags for {path}: {e}")
        return ""


def get_selinux_context(path: str) -> str:
    """Return the SELinux contest for @path"""
    try:
        ret, context = selinux.getfilecon(path)
        if ret > 0:
            return context
        EXTERNAL.error(f"Error: selinux.getfilecon {path} returned {ret}")
    except Exception as e:
        EXTERNAL.error(f"Error: selinux.getfilecon {path}: {e}")
    return ""


def get_file_attrs(
        path: str,
        req_attr: List[str],
        fatal_err: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """Retrieve mode, owner, group, size, timestamps, SELinux context,
    xattr, and chattr_flags.
    loads file contents only if required.
    """
    try:
        stats = os.stat(path)

        # file mode in octal
        mode = stats.st_mode & 0o777

        try:
            user = pwd.getpwuid(stats.st_uid).pw_name
        except KeyError:
            user = f"UID:{stats.st_uid}"

        try:
            group = grp.getgrgid(stats.st_gid).gr_name
        except KeyError:
            group = f"GID:{stats.st_gid}"

        # Retrieve extended attributes (xattr) if required
        xattr = get_xattr(path) if "xattr" in req_attr else None

        # Retrieve chattr flags if required
        chattr_flags = \
            get_chattr_flags(path) if "chattr_flags" in req_attr else None

        # Retrieve selinux context if required
        selinux_context = \
            get_selinux_context(path) if "selinux_context" in req_attr \
            else None

        # Lazy load file contents if/when required
        file_contents = None

        if any(attr in req_attr for
               attr in ["file_contents", "identical", "contains", "regex"]):
            file_contents = get_file_contents(path)
            if file_contents is None:
                INTERNAL.debug(f"Get file contents returned None for {path}")
                # This is a fatal error
                return None

        return {
            "exists": True,
            "size": stats.st_size,
            "mode": mode,
            "user": user,
            "uid": stats.st_uid,
            "group": group,
            "gid": stats.st_gid,
            "mtime": stats.st_mtime,
            "atime": stats.st_atime,
            "ctime": stats.st_ctime,
            "selinux_context": selinux_context,
            "xattr": xattr,
            "chattr_flags": chattr_flags,
            "file_contents": file_contents,
        }
    except FileNotFoundError:
        return {"exists": False}
    except PermissionError:
        err_msg = f"ERROR: Permission denied: {path}"
        if fatal_err is not None:
            fatal_err.append(err_msg)
        else:
            EXTERNAL.error("%s", err_msg)

    except Exception as e:
        err_msg = f"ERROR: Failed to retrieve attributes for {path}: {e}"
        if fatal_err is not None:
            fatal_err.append(err_msg)
        else:
            EXTERNAL.error("%s", err_msg)

    return None


class FilesPlugin(OSCheckPlugin):
    """File checker plugin class"""
    @property
    def name(self):
        return "files"

    def run(self, rules, base_path=None) -> int:
        if base_path not in ("/", None):
            EXTERNAL.error("The files plugin does not support sosreport yet")
            return -1

        errors = 0
        for pattern, rule in rules.items():
            if any(c in pattern for c in "*?[]"):
                matching_paths = glob.glob(pattern, recursive=True)
                if not matching_paths:
                    errors = errors + 1
                    EXTERNAL.error(
                        f"❌ No matching paths found for glob: {pattern}")
                    continue
            else:
                matching_paths = [pattern]

            for path in matching_paths:
                fatal_err = []
                INTERNAL.debug(f"DEBUG: validate_files for {path} called")

                req_attr = get_required_attributes(rule)
                attributes = \
                    get_file_attrs(path, req_attr, fatal_err=fatal_err)

                if not attributes:
                    errors = errors + 1
                    EXTERNAL.error(f"❌ FILE: {path} failed validation.")
                    EXTERNAL.error(f"  ↳ Could not get all file attributes.")
                    for failure in fatal_err:
                        EXTERNAL.error(f"  ↳ {failure}")
                    continue

                INTERNAL.debug(f"DEBUG: evaluating rule for {path}: {rule}")
                result, failures = \
                    validate_rule(attributes, rule, "files", path,
                                  fatal_err=fatal_err)
                if not result or fatal_err:
                    errors = errors + 1
                    EXTERNAL.error(f"❌ FILE: {path} failed validation.")
                    err_sources = failures
                    if not os.path.exists(path):
                        EXTERNAL.error(f"  ↳ {path} does not exist.")
                    else:
                        err_sources = failures + fatal_err

                    for failure in err_sources:
                        EXTERNAL.error(f"  ↳ {failure}")
                else:
                    EXTERNAL.info(f"✅️ FILE: {path} passed all checks.")

                # release file contents from memory, if loaded
                attributes["file_contents"] = ""
        return errors
