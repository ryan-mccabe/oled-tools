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
Contains class Microcode which
lists microcode versions that support mitigation
for various vulnerabilities based on cpu type.
Contains methods to identify the
minimum microcode version based on the vulnerability
type, get the highest microcode version that supports
fix for all vulnerabilities and get the current
microcode version.

"""
import sys
if (sys.version_info[0] == 3):
    from . import parser
    from .base import Base
else:
    import parser
    from base import Base
    from command import Cmd


class Microcode(Base):
    """
    Lists microcode versions for different vulnerabilities
    based on cpu type. Contains methods to identify the
    minimum microcode version based on the vulnerability
    type, get the highest microcode version that supports
    fix for all vulnerabilities and get the current
    microcode version.

    """
    cur_microcode_ver = ""
    SPECTRE_V2_MICROCODE = {"78_3": ["0x00c2"],
                            "78_1": ["0x00c2"],
                            "158_11": ["0x0084"],
                            "70_1": ["0x0019"],
                            "158_9": ["0x0084"],
                            "61_4": ["0x002a"],
                            "86_3": ["0x7000012"],
                            "45_7": ["0x0713"],
                            "42_7": ["0x002d"],
                            "45_6": ["0x061c"],
                            "142_9": ["0x0084"],
                            "158_10": ["0x0084"],
                            "142_10": ["0x0084"],
                            "63_2": ["0x003c"],
                            "94_3": ["0x00c2"],
                            "86_2": ["0x0015"],
                            "63_4": ["0x0011"],
                            "62_4": ["0x042c"],
                            "85_4": ["0x2000043"],
                            "86_4": ["0xf000011"],
                            "85_5": ["0xe000009"],
                            "60_3": ["0x0024"],
                            "71_1": ["0x001d"],
                            "58_1": ["0x001d"],
                            "69_1": ["0x0023"],
                            "79_1": ["0xb00002c"]}

    SSBD_MICROCODE = {"78_3": ["0x00c6"],
                      "122_1": ["0x0028"],
                      "158_11": ["0x008e"],
                      "70_1": ["0x001a"],
                      "158_9": ["0x008e"],
                      "61_4": ["0x002b"],
                      "86_3": ["0x7000013"],
                      "45_7": ["0x0714"],
                      "42_7": ["0x002e"],
                      "45_6": ["0x061d"],
                      "142_9": ["0x008e"],
                      "158_10": ["0x0096"],
                      "142_10": ["0x0096"],
                      "63_2": ["0x003d"],
                      "94_3": ["0x00c6"],
                      "86_2": ["0x0017"],
                      "63_4": ["0x0012"],
                      "62_4": ["0x042d"],
                      "85_4": ["0x200004d"],
                      "86_4": ["0xf000012"],
                      "62_7": ["0x714"],
                      "85_5": ["0xe00000a"],
                      "60_3": ["0x0025"],
                      "71_1": ["0x001e"],
                      "58_9": ["0x0020"],
                      "69_1": ["0x0024"],
                      "79_1": ["0xb00002e"],
                      "26_5": ["0x001d"],
                      "30_5": ["0x000a"],
                      "37_2": ["0x0011"],
                      "37_5": ["0x0007"],
                      "44_2": ["0x001f"],
                      "46_6": ["0x000d"],
                      "47_2": ["0x003b"],
                      "92_2": ["0x0014"],
                      "92_9": ["0x0032"],
                      "92_11": ["0x000c"],
                      "95_1": ["0x0024"]}

    L1TF_MICROCODE = {"78_3": ["0x00c6"],
                      "78_1": ["0x0028"],
                      "158_11": ["0x008e"],
                      "70_1": ["0x001a"],
                      "158_9": ["0x008e"],
                      "61_4": ["0x002b"],
                      "86_3": ["0x7000013"],
                      "42_7": ["0x002e"],
                      "142_9": ["0x008e"],
                      "158_10": ["0x0096"],
                      "142_10": ["0x0096"],
                      "94_3": ["0x00c6"],
                      "86_2": ["0x0017"],
                      "86_4": ["0xf000012"],
                      "60_3": ["0x0025"],
                      "71_1": ["0x001e"],
                      "58_9": ["0x0020"],
                      "69_1": ["0x0024"],
                      "26_5": ["0x001d"],
                      "30_5": ["0x0000a"],
                      "37_2": ["0x0011"],
                      "37_5": ["0x00007"],
                      "44_2": ["0x001f"],
                      "46_6": ["0x000d"],
                      "47_2": ["0x003b"],
                      "92_2": ["0x0014"],
                      "92_9": ["0x0032"],
                      "92_11": ["0x000c"],
                      "95_1": ["0x0024"]}

    MDS_MICROCODE = {"78_3": ["0x00cc"],
                     "122_1": ["0x002e"],
                     "158_11": ["0x0084"],
                     "70_1": ["0x001a"],
                     "158_9": ["0x0084"],
                     "61_4": ["0x002d"],
                     "86_3": ["0x7000017"],
                     "45_7": ["0x0718"],
                     "42_7": ["0x002f"],
                     "45_6": ["0x061f"],
                     "142_9": ["0x0084"],
                     "158_10": ["0x0084"],
                     "142_10": ["0x0084"],
                     "63_2": ["0x0043"],
                     "94_3": ["0x00cc"],
                     "86_2": ["0x001a"],
                     "63_4": ["0x0014"],
                     "62_4": ["0x042e"],
                     "85_4": ["0x200005e"],
                     "86_4": ["0xf000015"],
                     "62_7": ["0x715"],
                     "85_5": ["0xe00000d"],
                     "60_3": ["0x0027"],
                     "71_1": ["0x0020"],
                     "58_9": ["0x0021"],
                     "69_1": ["0x0025"],
                     "79_1": ["0xb000036"],
                     "92_9": ["0x0038"],
                     "92_11": ["0x0016"],
                     "95_1": ["0x002e"]}

    TAA_MICROCODE = {"78_3": ["0x00d4"],
                     "142_9": ["0x00c6"],
                     "158_9": ["0x00c6"],
                     "158_10": ["0x00c6"],
                     "158_11": ["0x00c6"],
                     "158_13": ["0x00c6"],
                     "142_10": ["0x00c6"],
                     "142_11": ["0x00c6"],
                     "142_12": ["0x00c6"],
                     "63_2": ["0x0043"],
                     "94_3": ["0x00d4"],
                     "86_2": ["0x001a"],
                     "85_4": ["0x2000064"],
                     "85_7": ["0x500002b"]}

    def get_cur_microcode(self):
        """
        Gets current microcode version.

        Returns:
        str: microcode version that the server
        is currently running.

        """
        cmd = "cat /proc/cpuinfo | grep microcode"

        microcode = self.run_command(cmd)
        if microcode != "":
            cur_ver = microcode.split("\n")[0].split(":")[1].strip()
            if cur_ver.find("0x") != -1:
                return int(cur_ver.split("0x")[1], 16)
        else:
            return 0

    def get_min_microcode_version(self, vtype):
        """
        Gets minimum microcode version that supports fix
        for a specific vulnerability.

        Parameters:
        vtype(int): Vulnerability type.

        Returns:
        str: microcode version that supports the fix
        for the specific vulnerability.

        """
        cmd = "cat /proc/cpuinfo | grep stepping"
        stepping = self.run_command(cmd)

        stepping_val = stepping.split("\n")[0].split(":")[1].strip()

        cmd = "cat /proc/cpuinfo | grep model"

        model = self.run_command(cmd)
        model_id = model.split("\n")[0].split(":")[1].strip()
        model_stepping_string = model_id + "_" + stepping_val

        if vtype == self.SPECTRE_V2:
            if model_stepping_string in list(self.SPECTRE_V2_MICROCODE.keys()):
                min_microcode_ver = int(
                    self.SPECTRE_V2_MICROCODE[model_stepping_string][0].
                    split("0x")[1], 16)
                return min_microcode_ver
            return False

        if vtype == self.SSBD:
            if model_stepping_string in list(self.SSBD_MICROCODE.keys()):
                min_microcode_ver = int(
                    self.SSBD_MICROCODE[model_stepping_string][0].
                    split("0x")[1], 16)
                return min_microcode_ver
            return False

        if vtype == self.L1TF:
            if model_stepping_string in list(self.L1TF_MICROCODE.keys()):
                min_microcode_ver = int(
                    self.L1TF_MICROCODE[model_stepping_string][0].
                    split("0x")[1], 16)
                return min_microcode_ver
            return False

        if vtype == self.MDS:
            if model_stepping_string in list(self.MDS_MICROCODE.keys()):
                min_microcode_ver = int(
                    self.MDS_MICROCODE[model_stepping_string][0].
                    split("0x")[1], 16)
                return min_microcode_ver
            return False

        if vtype == self.TSX_ASYNC_ABORT:
            if model_stepping_string in list(self.TAA_MICROCODE.keys()):
                min_microcode_ver = int(
                    self.TAA_MICROCODE[model_stepping_string][0].
                    split("0x")[1], 16)
                return min_microcode_ver
            return False

        return False

    def __init__(self):
        """
        Init function for the microcode class.

        Sets the cur_microcode_ver variable to the
        current running microcode version.

        """
        self.cur_microcode_ver = self.get_cur_microcode()
