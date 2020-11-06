#!/usr/bin/python
# Copyright (c) 2020, Oracle and/or its affiliates.
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
Module contains command class to
run OS commands.

"""

import sys
import os
from subprocess import Popen, PIPE
from signal import SIGKILL
from shlex import split
from time import time, sleep
from re import search


class Cmd(object):
    """ Class to run OS commands """

    def __init__(self):
        self.command = None
        self.err = None
        self.out = None
        self.code = None

    def run(self, command):
        """ Runs the command passed as argument """
        self.command = command
        if "|" in self.command:
            cmd_parts = self.command.split('|')
        else:
            cmd_parts = []
            cmd_parts.append(self.command)
        i = 0
        process = {}
        try:
            for cmd_part in cmd_parts:
                cmd_part = cmd_part.strip()
                if i == 0:
                    process[i] = Popen(split(cmd_part),
                                       stdin=None,
                                       stdout=PIPE,
                                       stderr=PIPE)
                else:
                    process[i] = Popen(split(cmd_part),
                                       stdin=process[i - 1].stdout,
                                       stdout=PIPE,
                                       stderr=PIPE)
                i += 1
            self.out, self.err = process[i - 1].communicate()
            if (sys.version_info[0] == 3):
                self.out = self.out.decode("utf-8")
        except Exception:
            sys.exit(1)
