Name:		oled-tools
Version:	0.6
Release:	LATEST_UNSTABLE%{?dist}
Summary:	Diagnostic tools for more efficient and faster debugging on Oracle Linux
Requires:	zlib
Requires:	bzip2-libs
Requires:	elfutils-libs
Requires:	python3
BuildRequires:	python3-devel
BuildRequires:	zlib-devel
BuildRequires:	bzip2-devel
BuildRequires:	elfutils-devel
Group:		Development/Tools
License:	GPLv2
URL:		https://github.com/oracle/oled-tools.git
Source0:	%{name}-%{version}.tar.gz


%description
oled-tools is a collection of command line tools, scripts, config files, etc.,
that will aid in faster and better debugging of problems on Oracle Linux. It
contains: lkce, memstate, kstack, filecache, dentrycache and syswatch.

%prep
%setup -q

%build
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT DIST=%{?dist} SPECFILE="1"

%define oled_d %{_usr}/lib/oled-tools
%define oled_etc_d /etc/oled/
%define memstate_lib %{python3_sitelib}/memstate_lib/
%define lkce_d %{oled_etc_d}/lkce
%define lkce_kdump_d %{lkce_d}/lkce_kdump.d
%define scripts_d %{oled_d}/scripts
%define scripts_docs_d %{oled_d}/scripts/docs

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

# memstate
%exclude %{memstate_lib}/__pycache__/*.pyc
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

#scripts
%{scripts_d}/arp_origin.d
%{scripts_docs_d}/arp_origin_example.txt
%{scripts_d}/rds_bcopy_metric.d
%{scripts_docs_d}/rds_bcopy_metric_example.txt
%{scripts_d}/rds_check_tx_stall.d
%{scripts_docs_d}/rds_check_tx_stall_example.txt
%{scripts_d}/rds_conn2irq.d
%{scripts_docs_d}/rds_conn2irq_example.txt
%{scripts_d}/rds_egress_TP.d
%{scripts_docs_d}/rds_egress_TP_example.txt
%{scripts_d}/rds_rdma_lat.d
%{scripts_docs_d}/rds_rdma_lat_example.txt
%{scripts_d}/rds_rdma_xfer_rate.d
%{scripts_docs_d}/rds_rdma_xfer_rate_example.txt
%{scripts_d}/rds_tx_funccount.d
%{scripts_docs_d}/rds_tx_funccount_example.txt
%{scripts_d}/ping_lat.d
%{scripts_docs_d}/ping_lat_example.txt
%{scripts_d}/spinlock_time.d
%{scripts_docs_d}/spinlock_time_example.txt

#syswatch
%{oled_d}/syswatch
%{_mandir}/man8/oled-syswatch.8.gz

%changelog
* Mon Jan 30 2023 Manjunath Patil <manjunath.b.patil@oracle.com> 0.6-1
- Remove tools memtracker, smtool and topstack
- Add diagnostic DTrace scripts (Manjunath Patil, Praveen Kumar Kannoju,
  Rama Nichanamatlu)
- Add tool syswatch (Jose Lombera)

* Fri Sep 17 2021 Aruna Ramakrishna <aruna.ramakrishna@oracle.com> - 0.5-5
- Several fixes to smtool (Mridula Shastry, Aruna Ramakrishna)
- Rewrite lkce; absorb kdump tool (Manjunath Patil)
- Remove tool gather
- Add support for OL8 in lkce and smtool (Mridula Shastry)
- Vendor and patch makedumpfile to use as a library (Wengang Wang)
- Add tool filecache (Wengang Wang)
- Add tool dentrycache (Wengang Wang)
- Add tool memtracker (Aruna Ramakrishna)
- Add tool memstate (Aruna Ramakrishna)
- Add tool topstack (Cesar Roque)
- Add tool kstack (Cesar Roque)

* Sun May 10 2020 Manjunath Patil <manjunath.b.patil@oracle.com> 0.1-5
- First release
- Add tool gather (Jeffery Yoder)
- Add tool kdump (Manjunath Patil)
- Add tool lkce (Manjunath Patil)
- Add tool smtool (Mridula Shastry)
