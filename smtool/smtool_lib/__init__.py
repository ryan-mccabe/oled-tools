#!/usr/bin/python
# Copyright (c) 2021, Oracle and/or its affiliates.
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

# allows other modules to import smtool_lib.Parser, etc.
import sys
if (sys.version_info[0] == 3):
    from .boot import Boot
    from .command import Cmd
    from .cpu import Cpu
    from .distro import Distro
    from .host import Host
    from .kernel import Kernel
    from .microcode import Microcode
    from .parser import Parser
    from .server import Server
    from .sysfile import Sysfile
    from .variant import Variant
    from .vulnerabilities import Vulnerabilities
else:
    from boot import Boot
    from command import Cmd
    from cpu import Cpu
    from distro import Distro
    from host import Host
    from kernel import Kernel
    from microcode import Microcode
    from parser import Parser
    from server import Server
    from sysfile import Sysfile
    from variant import Variant
    from vulnerabilities import Vulnerabilities
