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

LKCEDIR := $(OLEDDIR)/lkce

all:
	@echo "all:$(CURDIR)"

clean:
	@echo "clean:$(CURDIR)"

install:
	@echo "install:$(CURDIR)"
	mkdir -p $(OLEDDIR)
	mkdir -p $(MANDIR)
	install -m 755 $(CURDIR)/scripts/lkce.py $(BINDIR)/lkce
	install -m 755 $(CURDIR)/scripts/lkce-kdump.py $(BINDIR)/lkce-kdump
	gzip -c $(CURDIR)/lkce.man > $(MANDIR)/oled-lkce.8.gz
	chmod 644 $(MANDIR)/oled-lkce.8.gz
	@echo "lkce successfully installed"

uninstall:
	@echo "uninstall:$(CURDIR)"
	rm -f $(LKCEDIR)/*
	[ -f $(OLEDDIR)/kdump_pre.d/lkce-kdump ] && rm -f $(OLEDDIR)/kdump_pre.d/lkce-kdump || :
	rm -f $(BINDIR)/lkce-kdump
	rm -f $(BINDIR)/lkce
	rm -f $(MANDIR)/oled-lkce.8.gz
	rmdir $(LKCEDIR) || :
	@echo "lkce successfully uninstalled"
