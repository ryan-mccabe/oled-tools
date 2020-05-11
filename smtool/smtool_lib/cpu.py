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
Module contains Cpu class which lists
and validates various cpu families/models.
Also checks and reports vulnerabilities that
various CPU models are susceptible to.

"""
import parser
from base import Base


VERBOSE = False  # type: bool


def log(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if parser.VERBOSE:
        print msg,
    return


def logn(msg):
    """
    Logs messages if the variable
    VERBOSE is set.

    """
    if parser.VERBOSE:
        print msg
    return


def error(msg):
    """
    Logs error messages.

    """
    print "ERROR: " + msg
    return


class Cpu(Base):
    """
    Lists various CPUs belonging to different families and
    identifies the CPUs vulnerable to different security
    vulnerabilities.

    """
    # CPU Vendor
    X86_VENDOR_INTEL = "GenuineIntel"
    X86_VENDOR_CENTAUR = "CentaurHauls"
    X86_VENDOR_AMD = "AuthenticAMD"
    X86_VENDOR_HYGON = "HygonGenuine"
    X86_VENDOR_NSC = "Geode by NSC"

    # CPU_VENDOR
    vendor = None
    family = None
    model = None

    cpuinfo_file = '/proc/cpuinfo'

    def get_cpu_vendor(self):
        """
        Returns cpu vendor.

        Returns:
        str: cpu vendor.

        """
        if not self.is_valid():
            return None

        return self.vendor

    v_1 = v_2 = v_3 = v_4 = v_5 = v_6 = v_7 = v_8 = None

    def is_valid_cpu_vendor(self, vendor):
        """
        Checks if the cpu family is valid.

        Returns:
        bool: True if vendor is valid, else returns False.

        """
        if (vendor in [self.X86_VENDOR_INTEL, self.X86_VENDOR_CENTAUR,
                       self.X86_VENDOR_AMD, self.X86_VENDOR_HYGON,
                       self.X86_VENDOR_NSC]):
            return True
        return False

    # CPU Family
    INTEL_CPU_FAMILY = [4, 5, 6]
    AMD_CPU_FAMILY = [15, 16, 17, 18, 21, 23]
    ALL_CPU_FAMILY = INTEL_CPU_FAMILY + AMD_CPU_FAMILY

    # CPU_MODEL (file arch/x86/include/asm/intel-family.h)
    INTEL_FAM6_CORE_YONAH = int("0E", 16)
    INTEL_FAM6_CORE2_MEROM = int("0F", 16)
    INTEL_FAM6_CORE2_MEROM_L = int("16", 16)
    INTEL_FAM6_CORE2_PENRYN = int("17", 16)
    INTEL_FAM6_ATOM_PINEVIEW = int("1C", 16)
    INTEL_FAM6_CORE2_DUNNINGTON = int("1D", 16)
    INTEL_FAM6_NEHALEM = int("1E", 16)
    INTEL_FAM6_NEHALEM_G = int("1F", 16)
    INTEL_FAM6_NEHALEM_EP = int("1A", 16)
    INTEL_FAM6_NEHALEM_EX = int("2E", 16)
    INTEL_FAM6_WESTMERE = int("25", 16)
    INTEL_FAM6_ATOM_LINCROFT = int("26", 16)
    INTEL_FAM6_ATOM_PENWELL = int("27", 16)
    INTEL_FAM6_WESTMERE_EP = int("2C", 16)
    INTEL_FAM6_WESTMERE_EX = int("2F", 16)
    INTEL_FAM6_SANDYBRIDGE = int("2A", 16)
    INTEL_FAM6_SANDYBRIDGE_X = int("2D", 16)
    INTEL_FAM6_IVYBRIDGE = int("3A", 16)
    INTEL_FAM6_IVYBRIDGE_X = int("3E", 16)
    INTEL_FAM6_HASWELL_CORE = int("3C", 16)
    INTEL_FAM6_HASWELL_X = int("3F", 16)
    INTEL_FAM6_HASWELL_ULT = int("45", 16)
    INTEL_FAM6_HASWELL_GT3E = int("46", 16)
    INTEL_FAM6_BROADWELL_CORE = int("3D", 16)
    INTEL_FAM6_BROADWELL_GT3E = int("47", 16)
    INTEL_FAM6_BROADWELL_X = int("4F", 16)
    INTEL_FAM6_BROADWELL_XEON_D = int("56", 16)
    INTEL_FAM6_SKYLAKE_MOBILE = int("4E", 16)
    INTEL_FAM6_SKYLAKE_DESKTOP = int("5E", 16)
    INTEL_FAM6_SKYLAKE_X = int("55", 16)
    INTEL_FAM6_KABYLAKE_MOBILE = int("8E", 16)
    INTEL_FAM6_KABYLAKE_DESKTOP = int("9E", 16)
    INTEL_FAM6_CANNONLAKE_MOBILE = int("66", 16)
    INTEL_FAM6_ATOM_BONNELL = int("1C", 16)
    INTEL_FAM6_ATOM_BONNELL_MID = int("26", 16)
    INTEL_FAM6_ATOM_CEDARVIEW = int("36", 16)
    INTEL_FAM6_ATOM_SALTWELL_MID = int("27", 16)
    INTEL_FAM6_ATOM_CLOVERVIEW = int("35", 16)
    INTEL_FAM6_ATOM_SILVERMONT1 = int("37", 16)
    INTEL_FAM6_ATOM_SILVERMONT2 = int("4D", 16)
    INTEL_FAM6_ATOM_MERRIFIELD = int("4A", 16)
    INTEL_FAM6_ATOM_AIRMONT = int("4C", 16)
    INTEL_FAM6_ATOM_MOOREFIELD = int("5A", 16)
    INTEL_FAM6_ATOM_GOLDMONT = int("5C", 16)
    INTEL_FAM6_ATOM_TREMONT_X = int("86", 16)
    INTEL_FAM6_ATOM_DENVERTON = int("5F", 16)
    INTEL_FAM6_ATOM_GEMINI_LAKE = int("7A", 16)
    INTEL_FAM6_XEON_PHI_KNL = int("57", 16)
    INTEL_FAM6_XEON_PHI_KNM = int("85", 16)

    def is_intel(self):
        """
        Checks if the CPU belongs to Intel family.

        Returns:
        bool: True if the processor is Intel, else
        returns False.

        """
        if self.vendor != self.X86_VENDOR_INTEL:
            return False

        if self.family not in self.INTEL_CPU_FAMILY:
            return False

        return True

    def is_amd(self):
        """
        Checks if the CPU belongs to AMD family.

        Returns:
        bool: True if the processor is AMD, else
        returns False.

        """
        if self.vendor != self.X86_VENDOR_AMD:
            return False

        if self.family not in self.AMD_CPU_FAMILY:
            return False

        return True

    def is_hygon(self):
        """
        Checks if the CPU belongs to Hygon family.

        Returns:
        bool: True if the processor is Hygon, else
        returns False.

        """
        if self.vendor == self.X86_VENDOR_HYGON:
            return True
        return False

    def is_centaur(self):
        """
        Checks if the CPU belongs to Centaur family.

        Returns:
        bool: True if the processor is Centaur, else
        returns False.

        """
        if self.vendor == self.X86_VENDOR_CENTAUR:
            return True
        return False

    def is_nsc(self):
        """
        Checks if the CPU belongs to NSC family.

        Returns:
        bool: True if the processor is NSC, else
        returns False.

        """
        if self.vendor == self.X86_VENDOR_NSC:
            return True
        return False

    def is_valid_cpu_model(self):
        """
        Checks if the CPU model is valid.

        Returns:
        bool: True if the model is valid, else
        returns False.

        """
        if self.is_intel():
            if (self.model in [
                    self.INTEL_FAM6_CORE_YONAH,
                    self.INTEL_FAM6_CORE2_MEROM,
                    self.INTEL_FAM6_CORE2_MEROM_L,
                    self.INTEL_FAM6_CORE2_PENRYN,
                    self.INTEL_FAM6_ATOM_PINEVIEW,
                    self.INTEL_FAM6_CORE2_DUNNINGTON,
                    self.INTEL_FAM6_NEHALEM,
                    self.INTEL_FAM6_NEHALEM_G,
                    self.INTEL_FAM6_NEHALEM_EP,
                    self.INTEL_FAM6_NEHALEM_EX,
                    self.INTEL_FAM6_WESTMERE,
                    self.INTEL_FAM6_ATOM_LINCROFT,
                    self.INTEL_FAM6_ATOM_PENWELL,
                    self.INTEL_FAM6_WESTMERE_EP,
                    self.INTEL_FAM6_WESTMERE_EX,
                    self.INTEL_FAM6_SANDYBRIDGE,
                    self.INTEL_FAM6_SANDYBRIDGE_X,
                    self.INTEL_FAM6_IVYBRIDGE,
                    self.INTEL_FAM6_IVYBRIDGE_X,
                    self.INTEL_FAM6_HASWELL_CORE,
                    self.INTEL_FAM6_HASWELL_X,
                    self.INTEL_FAM6_HASWELL_ULT,
                    self.INTEL_FAM6_HASWELL_GT3E,
                    self.INTEL_FAM6_BROADWELL_CORE,
                    self.INTEL_FAM6_BROADWELL_GT3E,
                    self.INTEL_FAM6_BROADWELL_X,
                    self.INTEL_FAM6_BROADWELL_XEON_D,
                    self.INTEL_FAM6_SKYLAKE_MOBILE,
                    self.INTEL_FAM6_SKYLAKE_DESKTOP,
                    self.INTEL_FAM6_SKYLAKE_X,
                    self.INTEL_FAM6_KABYLAKE_MOBILE,
                    self.INTEL_FAM6_KABYLAKE_DESKTOP,
                    self.INTEL_FAM6_CANNONLAKE_MOBILE,
                    self.INTEL_FAM6_ATOM_BONNELL,
                    self.INTEL_FAM6_ATOM_BONNELL_MID,
                    self.INTEL_FAM6_ATOM_CEDARVIEW,
                    self.INTEL_FAM6_ATOM_MERRIFIELD,
                    self.INTEL_FAM6_ATOM_CLOVERVIEW,
                    self.INTEL_FAM6_ATOM_SILVERMONT1,
                    self.INTEL_FAM6_ATOM_SILVERMONT2,
                    self.INTEL_FAM6_ATOM_MERRIFIELD,
                    self.INTEL_FAM6_ATOM_AIRMONT,
                    self.INTEL_FAM6_ATOM_MOOREFIELD,
                    self.INTEL_FAM6_ATOM_GOLDMONT,
                    self.INTEL_FAM6_ATOM_DENVERTON,
                    self.INTEL_FAM6_ATOM_GEMINI_LAKE,
                    self.INTEL_FAM6_XEON_PHI_KNL,
                    self.INTEL_FAM6_ATOM_TREMONT_X,
                    self.INTEL_FAM6_XEON_PHI_KNM]):
                return True

            logn("Tool doesn't support this Intel Model")
            return False

        if (self.is_amd() or self.is_hygon() or self.is_centaur() or
                self.is_nsc()):
            return True

        logn("Tool doesn't support this CPU family")
        return False

    def scan_cpuinfo(self):
        """
        Scans cpu information including cpu type,
        model type and family type and updates the
        variables with the information.

        """
        self.vendor = None
        c_f = self.cpuinfo_file

        try:
            f_p = open(c_f)
        except BaseException:
            print "ERROR opening " + c_f
            return None

        for line in f_p:
            tmp = line.split()
            if not tmp:
                continue

            if tmp[0] == 'vendor_id':
                self.vendor = tmp[2]
                continue

            if tmp[0] == 'cpu' and tmp[1] == 'family':
                self.family = int(tmp[3])
                continue

            if tmp[0] == 'model':
                self.model = int(tmp[2])
                break
        return

    def is_valid(self):
        """
        Checks if the CPU family is valid.

        Returns:
        bool: True if the cpu model is valid, else
        returns False.

        """
        if (not self.is_intel() and not self.is_amd() and not self.is_hygon()
                and not self.is_centaur() and not self.is_nsc()):
            return False

        if not self.is_valid_cpu_model():
            return False

        return True

    def get_cpu_family(self):
        """
        Function to export cpu family to other classes.

        Returns:
        str: cpu family

        """
        if not self.is_valid():
            return None

        return self.family

    def get_cpu_model(self):
        """
        Function to export cpu model to other classes.

        Returns:
        str: cpu model string.

        """
        if not self.is_valid():
            return None

        return self.model

    def is_skylake(self):
        """
        Function to check if cpu model is Skylake.

        Returns:
        bool: True if cpu model is Skylake, else
        retruns False.

        """
        if not self.is_valid():
            return None

        if self.is_intel():
            if self.family == 6:
                if (self.model in [self.INTEL_FAM6_SKYLAKE_MOBILE,
                                   self.INTEL_FAM6_SKYLAKE_DESKTOP,
                                   self.INTEL_FAM6_SKYLAKE_X]):
                    return True
            return False

    def check_all_cpus(self):
        """
        Checks which cpus are vulnerable to which
        vulnerabilities and updates specific variants with
        the appropriate bool value.

        """
        if not self.is_valid():
            logn("Invalid CPU")
            return

        self.v_1 = self.v_2 = self.v_3 = self.v_4 = True
        self.v_5 = self.v_6 = self.v_7 = self.v_8 = True
        if self.is_intel():
            if self.family == 5:
                self.v_1 = self.v_2 = self.v_3 = self.v_4 = self.v_5 = False
                self.v_7 = self.v_8 = False
                return

            if self.family == 6:
                if (self.model in [self.INTEL_FAM6_ATOM_CEDARVIEW,
                                   self.INTEL_FAM6_ATOM_CLOVERVIEW,
                                   self.INTEL_FAM6_ATOM_BONNELL_MID,
                                   self.INTEL_FAM6_ATOM_SALTWELL_MID,
                                   self.INTEL_FAM6_ATOM_BONNELL]):
                    self.v_1 = self.v_2 = self.v_3 = self.v_4 = self.v_5 = False
                    return

                if (self.model in [self.INTEL_FAM6_ATOM_CEDARVIEW,
                                   self.INTEL_FAM6_ATOM_CLOVERVIEW,
                                   self.INTEL_FAM6_ATOM_PENWELL,
                                   self.INTEL_FAM6_ATOM_PINEVIEW,
                                   self.INTEL_FAM6_ATOM_LINCROFT]):
                    self.v_1 = self.v_2 = self.v_7 = False

                if (self.model in [self.INTEL_FAM6_ATOM_SILVERMONT1,
                                   self.INTEL_FAM6_ATOM_AIRMONT,
                                   self.INTEL_FAM6_ATOM_SILVERMONT2,
                                   self.INTEL_FAM6_ATOM_MERRIFIELD,
                                   self.INTEL_FAM6_XEON_PHI_KNL,
                                   self.INTEL_FAM6_XEON_PHI_KNM]):
                    self.v_4 = self.v_5 = self.v_7 = False

                if self.model in [self.INTEL_FAM6_CORE_YONAH]:
                    self.v_4 = False

                if self.model in [self.INTEL_FAM6_ATOM_MOOREFIELD]:
                    self.v_5 = self.v_7 = False

                if (self.model in [self.INTEL_FAM6_ATOM_GOLDMONT,
                                   self.INTEL_FAM6_ATOM_DENVERTON,
                                   self.INTEL_FAM6_ATOM_GEMINI_LAKE]):
                    self.v_5 = self.v_6 = self.v_7 = False

                if self.model in [self.INTEL_FAM6_ATOM_TREMONT_X]:
                    self.v_7 = False

                if (self.model not in [self.INTEL_FAM6_KABYLAKE_MOBILE,
                                       self.INTEL_FAM6_SKYLAKE_X,
                                       self.INTEL_FAM6_KABYLAKE_DESKTOP]):
                    self.v_8 = False

                return
            return

        if self.is_amd():
            self.v_3 = self.v_5 = self.v_6 = self.v_7 = False
            if self.family in [15, 16, 17, 18]:
                self.v_4 = False
            return

        if self.is_hygon():
            self.v_3 = self.v_5 = self.v_6 = self.v_7 = False
            return

        if self.is_centaur():
            if self.family in [5]:
                self.v_1 = self.v_2 = self.v_3 = self.v_4 = self.v_5 = False
                self.v_6 = self.v_7 = False
            return

        if self.is_nsc():
            if self.family in [5]:
                self.v_1 = self.v_2 = self.v_3 = self.v_4 = self.v_5 = False
                self.v_6 = self.v_7 = False
            return

        return

    def is_vulnerable_v_1(self):
        """
        Checks if CPU is vulnerable to Spectre V1.

        Returns:
        bool: True if it's vulnerable to Spectre V1,
        else return False.

        """
        return self.v_1

    def is_vulnerable_v_2(self):
        """
        Checks if CPU is vulnerable to Spectre V2.

        Returns:
        bool: True if it's vulnerable to Spectre V2,
        else return False.

        """
        return self.v_2

    def is_vulnerable_v_3(self):
        """
        Checks if CPU is vulnerable to Meltdown.

        Returns:
        bool: True if it's vulnerable to Meltdown,
        else return False.

        """
        return self.v_3

    def is_vulnerable_v_4(self):
        """
        Checks if CPU is vulnerable to SSBD.

        Returns:
        bool: True if it's vulnerable to SSBD,
        else return False.

        """
        return self.v_4

    def is_vulnerable_v_5(self):
        """
        Checks if CPU is vulnerable to L1TF.

        Returns:
        bool: True if it's vulnerable to L1TF,
        else return False.

        """
        return self.v_5

    def is_vulnerable_v_6(self):
        """
        Checks if CPU is vulnerable to MDS.

        Returns:
        bool: True if it's vulnerable to MDS,
        else return False.

        """
        return self.v_6

    def is_vulnerable_v_7(self):
        """
        Checks if CPU is vulnerable to ITLB_Multihit.

        Returns:
        bool: True if it's vulnerable to ITLB_Multihit,
        else return False.

        """
        return self.v_7

    def is_vulnerable_v_8(self):
        """
        Checks if CPU is vulnerable to TAA.

        Returns:
        bool: True if it's vulnerable to TAA,
        else return False.

        """
        return self.v_8

    def is_cpu_vulnerable(self):
        """
        Checks if CPU is vulnerable to any of the variants.

        Returns:
        bool: True if it's vulnerable to any of the variants,
        else return False.

        """
        if (self.is_vulnerable_v_1() or self.is_vulnerable_v_2() or
                self.is_vulnerable_v_3() or self.is_vulnerable_v_4() or
                self.is_vulnerable_v_5() or self.is_vulnerable_v_6() or
                self.is_vulnerable_v_7() or self.is_vulnerable_v_8()):
            return True
        return False

    def is_vulnerable(self, vtype):
        """
        Checks if cpu is vulnerable to the specific variant.

        Parameters:
        vtype(int): Variant type.

        Returns:
        bool: True if the cpu is vulnerable to the specific variant,
        else returns False.

        """
        if vtype == self.SPECTRE_V1:
            return self.v_1

        if vtype == self.SPECTRE_V2:
            return self.v_2

        if vtype == self.MELTDOWN:
            return self.v_3

        if vtype == self.SSBD:
            return self.v_4

        if vtype == self.L1TF:
            return self.v_5

        if vtype == self.MDS:
            return self.v_6

        if vtype == self.ITLB_MULTIHIT:
            return self.v_7

        if vtype == self.TSX_ASYNC_ABORT:
            return self.v_8

    def display(self):
        """
        Displays cpu information and lists the variants
        that the cpu is vulnerable to.

        """
        print "CPU Info :"
        if self.vendor:
            print "  Vendor        :  " + self.vendor
        if self.family:
            print "  Family        :  " + str(self.family)
        if self.model:
            print "  Model         :  " + str(self.model)
        print "  Vulnerable    : " + str(self.is_cpu_vulnerable())
        print "     Spectre V1 : " + str(self.is_vulnerable_v_1())
        print "     Spectre V2 : " + str(self.is_vulnerable_v_2())
        print "     Meltdown   : " + str(self.is_vulnerable_v_3())
        print "     SSBD       : " + str(self.is_vulnerable_v_4())
        print "     L1TF       : " + str(self.is_vulnerable_v_5())
        print "     MDS        : " + str(self.is_vulnerable_v_6())
        print "     ITLB_MULTIHIT: " + str(self.is_vulnerable_v_7())
        print "    TSX_ASYNC_ABORT: " + str(self.is_vulnerable_v_8())

    # Some cpus are not vulnerable to v_1,v_2,v_3,v_4,v_5,v_6,v_7 and
    # v_8 variants.
    def scan_vulnerabilities(self):
        self.check_all_cpus()
        return

    def __init__(self):
        """
        Init function for CPU class.
        Scans cpu information and checks if the cpu model
        is valid and supported by the tool.

        """
        log("           running cpu.............:")
        self.scan_cpuinfo()
        if not self.is_valid():
            raise ValueError("Unsupported cpu(vendor='" +
                             str(self.vendor) +
                             "'. family='" +
                             str(self.family) +
                             "', model='" +
                             str(self.model) +
                             "'")

        logn(str(self.get_cpu_vendor()) +
             " (family=" +
             str(self.get_cpu_family()) +
             ", model=" +
             str(self.get_cpu_model()) +
             ")")

        return
