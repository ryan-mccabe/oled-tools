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
# 2 along with this work; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.
from setuptools import find_packages
from setuptools import setup
from oscheck import __version__ as VERSION

long_description = open("README.md").read()

setup(
    name="oscheck",
    version=VERSION,
    description="OS health checker tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oracle/oled-tools",
    author="Ryan McCabe",
    author_email="ryan.m.mccabe@oracle.com",
    license="GPLv2",
    packages=find_packages(include=["oscheck", "oscheck.*"]),
    package_data={
        "oscheck": ["*.txt"],
    },
    entry_points={
        "console_scripts": ["oscheck=oscheck.__main__:main"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)"
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
    ],
)
