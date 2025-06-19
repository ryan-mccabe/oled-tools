# Copyrigcanht (c) 2023, Oracle and/or its affiliates.
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

WORKLOADDIR := $(OLEDBINDIR)/workloads

all:
	@echo "all:$(CURDIR)"

clean:
	@echo "clean:$(CURDIR)"

install:
	@echo "install:$(CURDIR)"
	mkdir -p $(WORKLOADDIR)
	install -m 755 $(CURDIR)/profile.py $(OLEDBINDIR)/profile
	install -m 755 $(CURDIR)/kern_cpuhp.fnlist $(WORKLOADDIR)/kern_cpuhp.fnlist
	install -m 755 $(CURDIR)/libvirt_cpuhp.fnlist $(WORKLOADDIR)/libvirt_cpuhp.fnlist
	install -m 755 $(CURDIR)/qemu_cpuhp.fnlist $(WORKLOADDIR)/qemu_cpuhp.fnlist
	gzip -c $(CURDIR)/profile.man > $(MANDIR)/oled-profile.8.gz
	chmod 644 $(MANDIR)/oled-profile.8.gz
	@echo "profile successfully installed!"

uninstall:
	@echo "uninstall:$(CURDIR)"
	rm -f $(OLEDBINDIR)/profile
	rm -f $(WORKLOADDIR)
	rm -f $(MANDIR)/oled-profile.8.gz
	@echo "profile successfully uninstalled!"
