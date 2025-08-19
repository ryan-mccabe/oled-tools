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
# 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
#
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.

SCRIPTSDIR := $(OLEDBINDIR)/scripts.d

TOOL_NAME := signal_snooper
PROG_NAME := kill_trace
OBSERVER_SCRIPT := $(PROG_NAME).sh

all:
	@echo "all:$(CURDIR)"

$(TOOL_NAME).8: $(TOOL_NAME).8.scd
	scdoc < $< > $@

$(PROG_NAME).8: $(PROG_NAME).8.scd
	scdoc < $< > $@

man: $(TOOL_NAME).8 $(PROG_NAME).8	
	gzip -c $(CURDIR)/$(TOOL_NAME).8 > $(MANDIR)/$(TOOL_NAME).8.gz
	gzip -c $(CURDIR)/$(PROG_NAME).8 > $(MANDIR)/$(PROG_NAME).8.gz
	chmod 644 $(MANDIR)/$(PROG_NAME).8.gz
	chmod 644 $(MANDIR)/$(TOOL_NAME).8.gz

clean:
	@echo "clean:$(CURDIR)"	
	rm -f $(CURDIR)/$(PROG_NAME).8
	rm -f $(CURDIR)/$(TOOL_NAME).8


install: man
	@echo "install:$(CURDIR)"
	install -D --mode=755 $(CURDIR)/$(OBSERVER_SCRIPT) $(SCRIPTSDIR)/$(OBSERVER_SCRIPT)
	install -D --mode=644 $(CURDIR)/$(TOOL_NAME).service \
		$(DESTDIR)/usr/lib/systemd/system/$(TOOL_NAME).service
	@echo "$(TOOL_NAME) successfully installed!"

uninstall:
	@echo "uninstall:$(CURDIR)"
	rm -f $(MANDIR)/$(TOOL_NAME).8.gz
	rm -f $(MANDIR)/$(PROG_NAME).8.gz
	rm -f $(SCRIPTSDIR)/$(OBSERVER_SCRIPT)
	rm -f $(DESTDIR)/usr/lib/systemd/system/$(TOOL_NAME).service
	@echo "$(TOOL_NAME) successfully uninstalled!"
