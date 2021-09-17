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

SMTOOL_LIB=$(DESTDIR)$(PYTHON_SITEDIR)/smtool_lib
CUR_LIB=$(CURDIR)/smtool_lib

all:
	@echo "all:$(CURDIR)"

clean:
	@echo "clean:$(CURDIR)"

install:
	@echo "install:$(CURDIR)"
	@echo "$(CURLIB)"
	@echo "$(SMTOOL_LIB)"
	mkdir -p $(SMTOOL_LIB)
	install -m 755 $(CURDIR)/smtool.py $(BINDIR)/smtool
	install -m 755 $(CUR_LIB)/__init__.py $(SMTOOL_LIB)/__init__.py
	install -m 755 $(CUR_LIB)/base.py $(SMTOOL_LIB)/base.py
	install -m 755 $(CUR_LIB)/boot.py $(SMTOOL_LIB)/boot.py
	install -m 755 $(CUR_LIB)/command.py $(SMTOOL_LIB)/command.py
	install -m 755 $(CUR_LIB)/cpu.py $(SMTOOL_LIB)/cpu.py
	install -m 755 $(CUR_LIB)/distro.py $(SMTOOL_LIB)/distro.py
	install -m 755 $(CUR_LIB)/host.py $(SMTOOL_LIB)/host.py
	install -m 755 $(CUR_LIB)/kernel.py $(SMTOOL_LIB)/kernel.py
	install -m 755 $(CUR_LIB)/microcode.py $(SMTOOL_LIB)/microcode.py
	install -m 755 $(CUR_LIB)/parser.py $(SMTOOL_LIB)/parser.py
	install -m 755 $(CUR_LIB)/server.py $(SMTOOL_LIB)/server.py
	install -m 755 $(CUR_LIB)/sysfile.py $(SMTOOL_LIB)/sysfile.py
	install -m 755 $(CUR_LIB)/variant.py $(SMTOOL_LIB)/variant.py
	install -m 755 $(CUR_LIB)/vulnerabilities.py $(SMTOOL_LIB)/vulnerabilities.py
	gzip -c $(CURDIR)/smtool.man > $(MANDIR)/oled-smtool.8.gz
	chmod 644 $(MANDIR)/oled-smtool.8.gz
	@echo "smtool successfully installed"

uninstall:
	@echo "uninstall:$(CURDIR)"
	rm -f $(MANDIR)/oled-smtool.8.gz
	rm -f $(SMTOOL_LIB)/vulnerabilities.py
	rm -f $(SMTOOL_LIB)/variant.py
	rm -f $(SMTOOL_LIB)/sysfile.py
	rm -f $(SMTOOL_LIB)/server.py
	rm -f $(SMTOOL_LIB)/parser.py
	rm -f $(SMTOOL_LIB)/microcode.py
	rm -f $(SMTOOL_LIB)/kernel.py
	rm -f $(SMTOOL_LIB)/host.py
	rm -f $(SMTOOL_LIB)/distro.py
	rm -f $(SMTOOL_LIB)/cpu.py
	rm -f $(SMTOOL_LIB)/command.py
	rm -f $(SMTOOL_LIB)/boot.py
	rm -f $(SMTOOL_LIB)/base.py
	rm -f $(SMTOOL_LIB)/__init__.py
	rm -f $(SMTOOL_LIB)/*.pyc
	rm -f $(BINDIR)/smtool
	rmdir $(SMTOOL_LIB) || :
	@echo "smtool successfully installed"
