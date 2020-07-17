Name:		oled-tools
Version:	0.1
Release:	3%{?dist}
Summary:	Diagnostic tools for more efficient and faster debugging on Oracle Linux

Group:		Development/Tools
License:	UPL
URL:		https://linux-git.us.oracle.com/oled/oled-tools
# Run the following command to download the source as a compressed tarball:
# git archive --format=tar.gz --prefix=oled-tools-0.1/
#		--remote=git@linux-git.us.oracle.com:oled/oled-tools.git
#		master -o oled-tools-0.1.tar.gz
Source0:	%{name}-%{version}.tar.gz


%description
oled-tools is a collection of command line tools, scripts, config files, etc.,
that will aid in faster and better debugging of problems on Oracle Linux. It
contains: lkce, gather and smtool presently


%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT DIST=%{?dist} SPECFILE="1"

%define oled_d %{_usr}/lib/oled-tools
%define oled_etc_d /etc/oled/
%define lkce_d %{oled_etc_d}/lkce
%define kdump_pre_d %{oled_etc_d}/kdump_pre.d
%define smtool_lib %{python_sitelib}/smtool_lib/

%post
#kdump-utils
oled kdump --add > /dev/null || :
%if 0%{?el6}
service kdump restart > /dev/null || :
%endif
%if 0%{?el7}
systemctl restart kdump > /dev/null || :
%endif

%preun
#kdump-utils
oled kdump --remove > /dev/null || :
%if 0%{?el6}
service kdump restart > /dev/null || :
%endif
%if 0%{?el7}
systemctl restart kdump > /dev/null || :
%endif

%postun
if [ $1 -ge 1 ] ; then
	# package upgrade, not uninstall

	#kdump-utils
	oled kdump --add > /dev/null || :

	%if 0%{?el6}
	service kdump restart > /dev/null || :
	%endif
	%if 0%{?el7}
	systemctl restart kdump > /dev/null || :
	%endif
else
	# package uninstall, not upgrade
	#smtool
	rm -f %{smtool_lib}/*.pyc || :
	rm -f %{smtool_lib}/*.pyo || :

	#lkce
	if [ -f %{lkce_d}/lkce.conf ]
	then
		rm -f %{kdump_pre_d}/lkce-kdump || :
		rm -f %{lkce_d}/crash_cmds || :
		rm -f %{lkce_d}/lkce.conf || :
	fi
	rmdir %{lkce_d} || :

	#kdump-utils
	rm -f %{oled_etc_d}/kdump_pre.sh || :
	rmdir %{kdump_pre_d} || :

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

#kdump-utils
%{oled_d}/kdump

# lkce
%{oled_d}/lkce
%{oled_d}/lkce-kdump
%{_mandir}/man8/oled-lkce.8.gz

#gather
%{oled_d}/gather
%{_mandir}/man8/oled-gather.8.gz

#smtool
%{oled_d}/smtool
%exclude %{smtool_lib}/*.pyc
%exclude %{smtool_lib}/*.pyo
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
%{smtool_lib}/boot.py
%{smtool_lib}/base.py
%{smtool_lib}/__init__.py
%{_mandir}/man8/oled-smtool.8.gz



%changelog
* Fri Jul 17 2020 Manjunath Patil <manjunath.b.patil@oracle.com> [0.1-3]
- re-organize Makefile and spec files

* Sun May 10 2020 Manjunath Patil <manjunath.b.patil@oracle.com> [0.1]
- first version
