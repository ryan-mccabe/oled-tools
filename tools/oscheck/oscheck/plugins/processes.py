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

"""processes OS Health Checker plugin"""

import os
import re
import logging
import fnmatch

from oscheck.core.engine import validate_rule, rule_implies_nonexistence
from oscheck.core.util import open_file
from oscheck.plugins.base import OSCheckPlugin

INTERNAL = logging.getLogger("oschecker.internal")
EXTERNAL = logging.getLogger("oschecker.external")


PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
CLK_TCK = os.sysconf("SC_CLK_TCK")


def collect_process_info(proc_root, pid):
    path = os.path.join(proc_root, pid)
    try:
        data = {"pid": int(pid)}
        data = {"exists": True}
        parse_status(path, data)
        parse_stat(path, data)
        parse_statm(path, data)
        parse_limits(path, data)
        parse_cmdline(path, data)
        parse_symlinks(path, data)
        parse_io(path, data)
        parse_selinux(path, data)
        parse_cgroup(path, data)
        count_fds(path, data)
        if (len(data["name"]) == 15 and
                data.get("cmdline_name", None) and
                len(data["cmdline_name"]) > 15
           ):
            data["name"] = data["cmdline_name"]

        #INTERNAL.debug(f"---\n{data}\n--------")
        return data
    except Exception as e:
        #INTERNAL.debug(f"*** ERROR {e}")
        return None


def normalize_key(key: str) -> str:
    """Normalize python dict keys"""
    key = key.strip().lower().replace(" ", "_")
    return re.sub(r'[^0-9a-zA-Z_]', "_", key)


def cmdline_to_name(cmdline: str) -> str:
    """Extract process name from cmdline"""
    cmd = cmdline.split()
    if cmd and cmd[0]:
        return os.path.basename(cmd[0])
    return cmdline


def parse_status(path, data):
    with open_file(path, "status") as f:
        for line in f:
            if ":" not in line:
                continue
            raw_key, value = line.split(":", 1)
            key = normalize_key(raw_key)
            parts = value.strip().split()

            if key == "name":
                data["name"] = value.strip()
                # in case we overwrite later if the process
                # name for the rule is > 15 chars
                data["name_status"] = data["name"]
            elif key == "uid" and len(parts) >= 4:
                data["uid"] = int(parts[0])
                data["euid"] = int(parts[1])
                data["suid"] = int(parts[2])
                data["fsuid"] = int(parts[3])
            elif key == "gid" and len(parts) >= 4:
                data["gid"] = int(parts[0])
                data["egid"] = int(parts[1])
                data["sgid"] = int(parts[2])
                data["fsgid"] = int(parts[3])

            # State: keep only the first character like 'R'
            elif key == "state" and parts:
                data["state"] = parts[0]

            # Drop "kB" from memory lines
            elif len(parts) == 2 and parts[1].lower() == "kb":
                try:
                    data[key] = int(parts[0])
                except ValueError:
                    data[key] = parts[0]

            # Single value field (int or string)
            elif len(parts) == 1:
                try:
                    data[key] = int(parts[0])
                except ValueError:
                    data[key] = parts[0]

            # Multi-value fields (groups, nstgid, etc.)
            elif len(parts) > 1:
                try:
                    data[key] = [int(p) for p in parts]
                except ValueError:
                    data[key] = parts


def parse_stat(path, data):
    try:
        with open_file(path, "stat") as f:
            parts = f.read().split()
            data["session"] = int(parts[5])
            data["tty_nr"] = int(parts[6])
            data["nice"] = int(parts[18])
            utime = int(parts[13])
            stime = int(parts[14])
            data["cpu_user_time_sec"] = utime / CLK_TCK
            data["cpu_sys_time_sec"] = stime / CLK_TCK
            data["start_time_ticks"] = int(parts[21])
    except Exception:
        pass


def parse_statm(path, data):
    try:
        with open_file(path, "statm") as f:
            parts = f.read().split()
            data["vmsize_kb"] = int(parts[0]) * PAGE_SIZE
            data["rss_kb"] = int(parts[1]) * PAGE_SIZE
    except Exception:
        pass


def parse_limits(path, data):
    try:
        with open_file(path, "limits") as f:
            for line in f:
                if ":" not in line:
                    continue
                name, rest = line.split(":", 1)
                key = "limit_" + name.strip().lower().replace(" ", "_")
                data[key] = rest.strip().split()[0]
    except Exception:
        pass


def parse_cmdline(path, data):
    try:
        with open_file(path, "cmdline") as f:
            raw = f.read()
            cmd = raw.replace("\x00", " ").strip()
            data["cmdline"] = cmd
            data["cmdline_name"] = cmdline_to_name(cmd)
    except Exception as e:
        data["cmdline"] = ""


def parse_symlinks(path, data):
    for name in ["exe", "cwd", "root"]:
        try:
            data[name] = os.readlink(os.path.join(path, name))
        except Exception:
            data[name] = ""


def parse_io(path, data):
    try:
        with open(os.path.join(path, "io")) as f:
            for line in f:
                key, value = line.strip().split(":")
                data["io_" + key.strip().lower()] = int(value.strip())
    except Exception:
        pass


def parse_selinux(path, data):
    try:
        with open(os.path.join(path, "attr", "current")) as f:
            data["selinux_context"] = f.read().strip()
    except Exception:
        data["selinux_context"] = ""


def parse_cgroup(path, data):
    try:
        with open(os.path.join(path, "cgroup")) as f:
            data["cgroups"] = [line.strip() for line in f]
    except Exception:
        data["cgroups"] = []


def count_fds(path, data):
    try:
        fd_dir = os.path.join(path, "fd")
        data["fd_count"] = len(os.listdir(fd_dir))
    except Exception:
        data["fd_count"] = 0


class Processes(OSCheckPlugin):
    @property
    def name(self):
        return "processes"

    def run(self, rules, base_path="/") -> int:
        proc_path = os.path.join(base_path, "proc")
        all_processes = []
        fails = 0

        for pid in os.listdir(proc_path):
            if pid.isdigit():
                proc_data = collect_process_info(proc_path, pid)
                if proc_data:
                    all_processes.append(proc_data)

        for pattern, rule in rules.items():
            matched = [p for p in all_processes
                       if fnmatch.fnmatch(p["name"], pattern)]
            if not matched:
                if rule_implies_nonexistence(rule):
                    dummy = {"exists": False}
                    context = f"PROCESS {pattern} (not found)"
                    fatal_err = []
                    passed, failures = validate_rule(
                        dummy, rule, pattern, context,
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
                else:
                    EXTERNAL.error(
                        f"❌ PROCESS {pattern}: no matching process found")
                    fails += 1
                continue

            for p in matched:
                context = f"PROCESS {pattern} pid={p['pid']}"
                fatal_err = []
                passed, failures = validate_rule(
                    p, rule, pattern, context,
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
