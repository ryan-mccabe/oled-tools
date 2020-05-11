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

TOPDIR=$$PWD
subdirs=kdump-utils lkce gather smtool

rev_subdirs:=$(shell echo -n "$(subdirs) " | tac -s ' ')
BINDIR_PREFIX=/usr
BINDIR=$(BINDIR_PREFIX)/sbin

# run ./configure generate oled-env.sh
-include oled-env.sh
export OLED_DIST
export PYTHON_SITEDIR

all:
	$(foreach dir,$(subdirs), make TOPDIR=$(TOPDIR) BINDIR=$(BINDIR)/oled-tools -C $(dir) all || exit 1;)

clean:

	$(foreach dir,$(subdirs), make TOPDIR=$(TOPDIR) BINDIR=$(BINDIR)/oled-tools -C $(dir) clean;)
	[ -f oled-env.sh ] && rm -f oled-env.sh || :

install:
	@echo "install:$(CURDIR)"
	make all
	mkdir -p /etc/oled
	mkdir -p $(BINDIR)/oled-tools
	install -m 755 oled.py $(BINDIR)/oled
	gzip -c oled.man > /usr/share/man/man8/oled.8.gz; chmod 644 /usr/share/man/man8/oled.8.gz
	$(foreach dir,$(subdirs), make TOPDIR=$(TOPDIR) BINDIR=$(BINDIR)/oled-tools -C $(dir) install || exit 1;)
	@echo "OLED_TOOLS successfully installed!"

uninstall:
	@echo "uninstall:$(CURDIR)"
	$(foreach dir, $(rev_subdirs), make TOPDIR=$(TOPDIR) BINDIR=$(BINDIR)/oled-tools -C $(dir) uninstall || exit 1;)
	rm -f /usr/share/man/man8/oled.8.gz
	rm -f $(BINDIR)/oled
	rmdir $(BINDIR)/oled-tools
	rmdir /etc/oled
	@echo "OLED_TOOLS successfully uninstalled!"

rpm:
	rm -rf oled-tools-0.1
	rm -f ./oled-tools-0.1.tar.gz
	mkdir oled-tools-0.1
	cp -R Makefile oled-env.sh oled.man oled.py oled-tools-0.1/
	cp -R kdump-utils oled-tools-0.1/
	cp -R lkce oled-tools-0.1/
	cp -R gather oled-tools-0.1/
	cp -R smtool oled-tools-0.1/
	tar chozf oled-tools-0.1.tar.gz oled-tools-0.1
	#rpmbuild
	mkdir -p `pwd`/rpmbuild/{RPMS,BUILD{,ROOT},SRPMS}
ifeq ($(OLED_DIST),OL6)
	exec rpmbuild -ba \
	--define="_topdir `pwd`/rpmbuild" \
	--define="_sourcedir `pwd`" \
	--define="_specdir `pwd`" \
	--define="_tmppath `pwd`/rpmbuild/BUILDROOT" \
	buildrpm/ol6/oled-tools.spec
else ifeq ($(OLED_DIST),OL7)
	exec rpmbuild -ba \
	--define="_topdir `pwd`/rpmbuild" \
	--define="_sourcedir `pwd`" \
	--define="_specdir `pwd`" \
	--define="_tmppath `pwd`/rpmbuild/BUILDROOT" \
	buildrpm/ol7/oled-tools.spec
else
	@echo "Unknown dist. Running './configure' can fix this issue"
endif
	rm -rf oled-tools-0.1
	rm -f ./oled-tools-0.1.tar.gz

rpm_clean:
	rm -rf ./rpmbuild
