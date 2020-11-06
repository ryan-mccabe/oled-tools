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
Contains Parser class that
parses, validates various
user provided options while running
Smtool.

"""
import sys
import getopt

if (sys.version_info[0] == 3):
    from .base import Base
    from .distro import Distro
    from .server import Server
else:
    from base import Base
    from distro import Distro
    from server import Server

VERBOSE = False  # type: bool


def log(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if VERBOSE:
        print(msg)
    return


def error(msg):
    """
    Logs error messages.

    """
    print("ERROR: " + msg)
    return


class Parser(Base):
    """
    Parses and validates various
    user provided options and thier
    combinations.
    Also sets appropriate variables
    based on user provided options.

    """
    verbose = False
    scan_only = False
    yes = False
    help = False
    runtime = False
    enable_default = False
    disable_all = False
    enable_full = False
    dry_run = False
    valid = True
    distro = server = None

    def get_server_type(self):
        """
        Identify type of server.

        Returns:
        str: server type.

        """
        self.distro = Distro(False)                  # Oracle distro object
        # Baremetal, hypervisor, VM
        self.server = Server(self.distro, False)
        server_type = self.server.scan_server(self.distro)
        return server_type

    def usage(self):
        """
        Prints details about various
        options that the tool supports
        and their usage.

        """
        print(" smtool - Scans and mitigates the following")
        print(" vulnerabilities:")
        print("                 Spectre V1,")
        print("                 Spectre V2,")
        print("                 Meltdown,")
        print("                 SSBD,")
        print("                 L1TF,")
        print("                 ITLB_Multihit,")
        print("                 TSX Async Abort.")
        print(" NOTE:")
        print("     This script must be run as root and requires")
        print("     virt-what package to be installed on the machine.")
        print(" USAGE:")
        print("       smtool [-hvsyrd]<options>")
        print("       -h, --help       help")
        print("       -v, --verbose    verbose")
        print("       -s, --scan-only  scan current state of the host")
        print("       -y, --yes        make changes without prompt")
        print("       -r, --runtime    runtime only changes")
        print("       -d, --dry-run    don't make changes yet")
        print(" OPTIONS:")
        print("         --enable-default-mitigation [-yd]")
        print("         --disable-mitigations [-yrd]")
        print("         --enable-full-mitigation [-yrd]")

    def print_options(self):
        """
        Prints various options
        that the tool can be run with.

        """
        opt = ""
        if self.verbose:
            opt += "verbose"

        if self.scan_only:
            opt += ", scan only"

        if self.yes:
            opt += ", yes"

        if self.runtime:
            opt += ", runtime"

        if self.dry_run:
            opt += ", dry run"

        if self.enable_default:
            opt += ", enable default"

        if self.disable_all:
            opt += ", disable all"

        if self.enable_full:
            opt += ", enable full"

        if self.help:
            opt += ", help"

        log("   Options: " + opt)
        return

    def validate_options(self):
        """
        Validates various options
        and their combinations and reports
        any mismatch to the user.

        """
        if self.scan_only:
            if (self.dry_run or self.disable_all or self.enable_full or
                    self.runtime or self.enable_default):
                error("No action(s) during scan")
                return False

        if self.disable_all and self.enable_full:
            error("Can't disable/enable all Mitigations at the same time")
            return False

        if self.enable_default:
            if self.disable_all or self.enable_full:
                error("Can't enable default mitigations with these options")
                return False

        if self.dry_run:
            if self.disable_all or self.enable_full or self.enable_default:
                if ((self.get_server_type() == 2) or (
                        self.get_server_type() == 3)):
                    error("Cannot use this option on Xen hypervisor or "
                          "PV guest")
                    return False

        if self.runtime:
            if self.disable_all or self.enable_full:
                return True
            if self.enable_default:
                error("Cannot enable default mitigations in runtime")
                return False

        if self.yes or self.dry_run:
            if self.disable_all or self.enable_full or self.enable_default:
                return True
            else:
                error(
                    "This option needs to be used in conjunction with "
                    "enable-full-mitigation or disable-mitigations or"
                    " enable-default-mitigation")
                return False

        if (not self.disable_all and not self.enable_full
                and not self.enable_default and
                not self.scan_only and not self.verbose
                and not self.help):
            error("No action specified")

        return True

    def parse_options(self, argv):
        """
        Parses various user provided
        options.

        """
        global VERBOSE
        try:
            options = ['help', 'scan-only', 'yes', 'runtime',
                       'disable-mitigations', 'enable-full-mitigation',
                       'enable-default-mitigation', 'dry-run']

            opts, args = getopt.getopt(argv[1:], 'hvyrsd', options)
        except getopt.GetoptError as err:
            print(err)
            self.usage()
            sys.exit(2)

        if not opts:
            self.usage()
            return False

        for opt, arg in opts:
            if opt == '-h' or opt == '--help':
                self.help = True
                self.usage()
                return True

            if opt == '-v' or opt == '--verbose':
                VERBOSE = True
                self.verbose = True
                log("Parsing options: ")

            if opt == '-s' or opt == '--scan-only':
                self.scan_only = True

            if opt == '-r' or opt == '--runtime-only':
                self.runtime = True

            if opt == '-d' or opt == '--dry-run':
                self.dry_run = True

            if opt == '-y' or opt == '--yes':
                self.yes = True

            if opt == '--disable-mitigations':
                self.disable_all = True

            if opt == '--enable-full-mitigation':
                self.enable_full = True

            if opt == '--enable-default-mitigation':
                self.enable_default = True

        if self.verbose:
            self.print_options()

        return True
