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

# run ./configure generate oled-env.sh
-include oled-env.sh
export DIST
export PYTHON_SITEDIR
export SPECFILE
export DESTDIR

ifeq ("$(DIST)",".el8")
subdirs := kdump-utils lkce smtool kcore-utils memstate
else
subdirs := kdump-utils lkce gather smtool kcore-utils memstate
endif
rev_subdirs := $(shell echo -n "$(subdirs) " | tac -s ' ')
OLEDDIR := $(DESTDIR)/etc/oled
SBINDIR := $(DESTDIR)/usr/sbin
MANDIR := $(DESTDIR)/usr/share/man/man8
OLEDBIN := $(DESTDIR)/usr/lib/oled-tools

export OLEDDIR
export MANDIR

all:
	echo $(subdirs)
	$(foreach dir,$(subdirs), make BINDIR=$(OLEDBIN) -C $(dir) all || exit 1;)

clean:

	$(foreach dir,$(subdirs), make BINDIR=$(OLEDBIN) -C $(dir) clean;)
	[ -f oled-env.sh ] && rm -f oled-env.sh || :

install:
	@echo "install:$(CURDIR)"
	make all
	mkdir -p $(OLEDDIR)
	mkdir -p $(SBINDIR)
	mkdir -p $(MANDIR)
	mkdir -p $(OLEDBIN)
	install -m 755 oled.py $(SBINDIR)/oled
	gzip -c oled.man > $(MANDIR)/oled.8.gz; chmod 644 $(MANDIR)/oled.8.gz
	$(foreach dir,$(subdirs), make BINDIR=$(OLEDBIN) -C $(dir) install || exit 1;)
	@echo "oled-tools installed"

uninstall:
	@echo "uninstall:$(CURDIR)"
	$(foreach dir, $(rev_subdirs), make BINDIR=$(OLEDBIN) -C $(dir) uninstall || exit 1;)
	rm -f $(MANDIR)/oled.8.gz
	rm -f $(SBINDIR)/oled
	rmdir $(OLEDBIN) || :
	rmdir $(OLEDDIR) || :
	@echo "oled-tools uninstalled"

rpm:
	rm -rf oled-tools-0.1
	rm -f ./oled-tools-0.1.tar.gz
	mkdir oled-tools-0.1
	cp -R Makefile configure oled-env.sh oled.man oled.py oled-tools-0.1/
	cp -R kdump-utils oled-tools-0.1/
	cp -R smtool oled-tools-0.1/
	cp -R lkce oled-tools-0.1/
	cp -R gather oled-tools-0.1/
	cp -R kcore-utils oled-tools-0.1/
	cp -R memstate oled-tools-0.1/
	tar chozf oled-tools-0.1.tar.gz oled-tools-0.1
	#rpmbuild
	mkdir -p `pwd`/rpmbuild/{RPMS,BUILD{,ROOT},SRPMS}
	exec rpmbuild -ba \
	--define="_topdir `pwd`/rpmbuild" \
	--define="_sourcedir `pwd`" \
	--define="_specdir `pwd`" \
	--define="_tmppath `pwd`/rpmbuild/BUILDROOT" \
	buildrpm/oled-tools.spec
	rm -rf oled-tools-0.1
	rm -f ./oled-tools-0.1.tar.gz
	@echo "oled-tools rpms built"

rpm_clean:
	rm -rf ./rpmbuild
	@echo "oled-tools RPM build dir cleaned"
