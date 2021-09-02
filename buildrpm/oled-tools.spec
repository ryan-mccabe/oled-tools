Name:		oled-tools
Version:	0.5
Release:	1%{?dist}
Summary:	Diagnostic tools for more efficient and faster debugging on Oracle Linux
Requires:	zlib
Requires:	bzip2-libs
Requires:	elfutils-libs
BuildRequires:	zlib-devel
BuildRequires:	bzip2-devel
BuildRequires:	elfutils-devel
Group:		Development/Tools
License:	UPL
URL:		https://github.com/oracle/oled-tools.git
Source0:	%{name}-%{version}.tar.gz


%description
oled-tools is a collection of command line tools, scripts, config files, etc.,
that will aid in faster and better debugging of problems on Oracle Linux. It
contains: lkce, smtool, memstate, memtracker, kstack, topstack, filecache and
dentrycache.

# avoid OL8 build error. We have to fix this eventually
%if 0%{?el8}
%define debug_package %{nil}
%endif

%prep
%setup -q

%if 0%{?el8}
find -type f -exec sed -i '1s=^#!/usr/bin/\(python\|env python\)[23]\?=#!%{__python3}=' {} +
find . -type f -name "Makefile" -print0 | xargs -0 sed -i  's/\bpython\b/python3/g'
find -type f -exec sed -i 's/\braw_input\b/input/g' {} \;
%endif

%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT DIST=%{?dist} SPECFILE="1"

%define oled_d %{_usr}/lib/oled-tools
%define oled_etc_d /etc/oled/
%if 0%{?el8}
%define smtool_lib %{python3_sitearch}/smtool_lib/
%define memstate_lib %{python3_sitearch}/memstate_lib/
%else
%define smtool_lib %{python_sitelib}/smtool_lib/
%define memstate_lib %{python_sitelib}/memstate_lib/
%endif
%define lkce_d %{oled_etc_d}/lkce
%define lkce_kdump_d %{lkce_d}/lkce_kdump.d

%post
[ -f %{lkce_d}/lkce.conf ] || oled lkce configure --default > /dev/null

%preun
if [ $1 -lt 1 ] ; then
# package uninstall, not upgrade
	oled lkce disable > /dev/null || :
fi

%postun
if [ $1 -lt 1 ] ; then
# package uninstall, not upgrade
	#smtool
	%if 0%{?el8}
		rm -rf %{smtool_lib}/__pycache__
	%else
		rm -f %{smtool_lib}/*.pyc || :
		rm -f %{smtool_lib}/*.pyo || :
	%endif

	#memstate
	%if 0%{?el8}
		rm -rf %{memstate_lib}/__pycache__
	%else
		rm -f %{memstate_lib}/*.pyc || :
		rm -f %{memstate_lib}/*.pyo || :
	%endif

	#lkce
	rm -rf %{lkce_kdump_d} || :
	rm -rf %{lkce_d} || :

	#oled
	rmdir %{oled_etc_d} || :
fi


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)

#oled-tools
%{_sbindir}/oled
%{_mandir}/man8/oled.8.gz

#smtool
%{oled_d}/smtool
%if 0%{?el8}
%exclude %{smtool_lib}/__pycache__/*.pyc
%else
%exclude %{smtool_lib}/*.pyc
%exclude %{smtool_lib}/*.pyo
%endif
%{smtool_lib}/vulnerabilities.py
%{smtool_lib}/variant.py
%{smtool_lib}/sysfile.py
%{smtool_lib}/server.py
%{smtool_lib}/parser.py
%{smtool_lib}/microcode.py
%{smtool_lib}/kernel.py
%{smtool_lib}/host.py
%{smtool_lib}/distro.py
%{smtool_lib}/cpu.py
%{smtool_lib}/command.py
%{smtool_lib}/boot.py
%{smtool_lib}/base.py
%{smtool_lib}/__init__.py
%{_mandir}/man8/oled-smtool.8.gz

# memstate
%if 0%{?el8}
%exclude %{memstate_lib}/__pycache__/*.pyc
%else
%exclude %{memstate_lib}/*.pyc
%exclude %{memstate_lib}/*.pyo
%endif
%{oled_d}/memstate
%{memstate_lib}/base.py
%{memstate_lib}/buddyinfo.py
%{memstate_lib}/constants.py
%{memstate_lib}/hugepages.py
%{memstate_lib}/logfile.py
%{memstate_lib}/meminfo.py
%{memstate_lib}/numa.py
%{memstate_lib}/pss.py
%{memstate_lib}/slabinfo.py
%{memstate_lib}/swap.py
%{memstate_lib}/__init__.py
%{_mandir}/man8/oled-memstate.8.gz

#memtracker
%{oled_d}/memtracker
%{_mandir}/man8/oled-memtracker.8.gz

# lkce
%{oled_d}/lkce
%{lkce_kdump_d}/kdump_report
%{_mandir}/man8/oled-lkce.8.gz

# kcore-utils
%{oled_d}/dentrycache
%{oled_d}/dentrycache_uek4
%{oled_d}/filecache
%{oled_d}/filecache_uek4
%{_mandir}/man8/oled-dentrycache.8.gz
%{_mandir}/man8/oled-filecache.8.gz

#kstack
%{oled_d}/kstack
%{_mandir}/man8/oled-kstack.8.gz

#topstack
%{oled_d}/topstack
%{_mandir}/man8/oled-topstack.8.gz

%changelog
* Thu Sep 02 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Smtool: Avoid failure when mitigation for a particular variant is
 not available [Orabug: 33287128]
- Smtool: Avoid redundant messages during verbose scan [Orabug: 33309752]
 
* Wed Jul 07 2021 Manjunath Patil <manjunath.b.patil@oracle.com>
- Prod release oled-tools-0.5-1

* Thu Jun 24 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Smtool: Add support for detection/mitigation for SRBDS [Orabug: 33032240]
- Smtool: Fix scanning of commandline parameters for TSX_Async_Abort [Orabug: 33043269]
- Smtool: Fix verbose scan [Orabug: 33044339]

* Mon Jun 14 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Smtool: Minor bug fixes [Orabug: 32999593]
- Smtool: Fix scan/verbose scan and enable/disable mitigations
  on Oracle VM Servers [Orabug: 33005737]
- Smtool: Fix enabling/disabling mitigations for
  TSX Async Abort [Orabug: 33005751]

* Thu Jun 10 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Smtool: Remove boothole module [Orabug: 32921120]

* Thu Jun 10 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Smtool: Misc bug fixes [Orabug: 32920986]

* Mon May 31 2021 Manjunath Patil <manjunath.b.patil@oracle.com>
- rewrite lkce

* Wed May 19 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Add man pages for filecache and dentrycache

* Thu Apr 8 2021 Cesar Roque <cesar.roque@oracle.com>
- Integrate topstack into oled-tools [Orabug: 32734650]

* Thu Apr 8 2021 Cesar Roque <cesar.roque@oracle.com>
- Integrate kstack into oled-tools [Orabug: 32545451]

* Thu Apr 1 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Fix kcore-utils Jenkins build issues

* Wed Mar 31 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Remove gather from oled-tools [Orabug: 32461332]

* Tue Mar 30 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Integrate memtracker into oled-tools [Orabug: 32430673]

* Fri Mar 19 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Integrate memstate into oled-tools [Orabug: 32425345]

* Fri Mar 19 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com>
- Add filecache and dentrycache to oled-tools rpm build.

* Tue Jan 5 2021 Mridula Shastry <mridula.c.shastry@oracle.com>
- Enable smtool on OL8. Also verification for boothole [Orabug: 30441144]
- Enabled kdump-utils and lkce to run on OL8. [Orabug: 32299961]

* Fri Sep 4 2020 Manjunath Patil <manjunath.b.patil@oracle.com>
- remove release string from oled version [Orabug: 31793813]

* Mon Aug 17 2020 Manjunath Patil <manjunath.b.patil@oracle.com>
- Prod Release oled-tools-0.1-4

* Fri Jul 17 2020 Manjunath Patil <manjunath.b.patil@oracle.com>
- re-organize Makefile and spec files

* Sun May 10 2020 Manjunath Patil <manjunath.b.patil@oracle.com> [0.1]
- first version
