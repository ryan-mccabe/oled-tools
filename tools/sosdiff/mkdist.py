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
"""
Create a zipapp distribution of sosdiff which can be executed directly
"""
import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="create sosdiff distributions"
    )
    parser.add_argument(
        "--interpreter",
        default="/usr/bin/python3",
        help="Set the interpreter (default: /usr/bin/python3)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="sosdiff.pyz",
        help="Set the output file",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent / "sosdiff"
    entry_point = "sosdiff.__main__:main"

    # The __pycache__ files created by Python contain bytecode. This _is_
    # useful, but only for specific Python versions. We can't generate it for
    # every Python version, and it is rather wasteful to include it in the
    # zipapp if it won't be applicable. So remove it.
    cache_dir = base_dir / "__pycache__"
    if cache_dir.is_dir():
        shutil.rmtree(cache_dir)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        shutil.copytree(base_dir, tmp / "sosdiff")
        zipapp.create_archive(
            td,
            args.output,
            interpreter=args.interpreter,
            main=entry_point,
        )


if __name__ == "__main__":
    main()
