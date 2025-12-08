Name: oled-tools-core
Version: 1.1.0
Release: 1test4%{?dist}
Summary: Diagnostic tools for more efficient and faster debugging on Oracle Linux
Requires: python3
Group: Development/Tools
License: GPLv2

%global debug_package %{nil}

Source0: oled-tools-%{version}.tar.bz2

%description
oled-tools-core is a collection of command line tools, scripts, config files, etc.,
that will aid in faster and better debugging of problems on Oracle Linux. It
contains syswatch.

%prep
%setup -q -n oled-tools-%{version}

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_libexecdir}/oled-tools
mkdir -p %{buildroot}%{_mandir}/man8

make -C tools/syswatch install OLEDBINDIR=%{buildroot}%{_libexecdir}/oled-tools MANDIR=%{buildroot}%{_mandir}/man8 DESTDIR=%{buildroot} DIST=%{?dist} SPECFILE="1"

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)

%license LICENSE.txt
%doc README.md
%{_libexecdir}/oled-tools/syswatch
%{_mandir}/man8/oled-syswatch.8.gz


%changelog
* Fri Dec 05 2025 Ryan McCabe <ryan.m.mccabe@oracle.com> - 1.1.0-1
- Initial release of oled-tools-core, containing syswatch
