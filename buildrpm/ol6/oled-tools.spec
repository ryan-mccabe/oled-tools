Name: oled-tools
Version: 0.1
Release: 2%{?dist}
Summary: Diagnostic tools for more efficient and faster debugging on Oracle Linux

Group: Development/Tools
License: UPL
URL: https://linux-git.us.oracle.com/oled/oled-tools
ExclusiveArch: x86_64
ExclusiveOS: linux

# Run the following command to download the source as a compressed tarball:
# git archive --format=tar.gz --prefix=oled-tools-0.1/
#		--remote=git@linux-git.us.oracle.com:oled/oled-tools.git
#		staging -o oled-tools-0.1.tar.gz
Source0: %{name}-%{version}.tar.gz

%description
oled-tools is a collection of command line tools, scripts, config files, etc.,
that will aid in faster and better debugging of problems on Oracle Linux. It
contains: lkce, gather and smtool presently

%prep
%setup

%build
make all

%install
mkdir -p %{buildroot}

#oled-tools
mkdir -p %{buildroot}/etc/oled
mkdir -p %{buildroot}/usr/sbin/oled-tools
mkdir -p %{buildroot}/usr/share/man/man8/
install -m 755 oled.py %{buildroot}/usr/sbin/oled
gzip -c oled.man > %{buildroot}/usr/share/man/man8/oled.8.gz
chmod 644 %{buildroot}/usr/share/man/man8/oled.8.gz

#kdump-utils
mkdir -p %{buildroot}/etc/oled/kdump_pre.d
install -m 755 kdump-utils/kdump-utils.py %{buildroot}/usr/sbin/oled-tools/kdump

# lkce
mkdir -p %{buildroot}/etc/oled/lkce
install --mode=755 lkce/scripts/lkce.py %{buildroot}/usr/sbin/oled-tools/lkce
install --mode=755 lkce/scripts/lkce-kdump.py %{buildroot}/usr/sbin/oled-tools/lkce-kdump
gzip -c lkce/lkce.man > %{buildroot}/usr/share/man/man8/oled-lkce.8.gz
chmod 644 %{buildroot}/usr/share/man/man8/oled-lkce.8.gz

#gather
install --mode=755 gather/gather %{buildroot}/usr/sbin/oled-tools/gather
gzip -c gather/gather.man > %{buildroot}/usr/share/man/man8/oled-gather.8.gz
chmod 644 %{buildroot}/usr/share/man/man8/oled-gather.8.gz

#smtool
mkdir -p %{buildroot}%{python_sitelib}/smtool_lib
install --mode=755 smtool/smtool.py %{buildroot}/usr/sbin/oled-tools/smtool
install --mode=644 smtool/smtool_lib/__init__.py  %{buildroot}%{python_sitelib}/smtool_lib/__init__.py
install --mode=644 smtool/smtool_lib/base.py %{buildroot}%{python_sitelib}/smtool_lib/base.py
install --mode=644 smtool/smtool_lib/boot.py %{buildroot}%{python_sitelib}/smtool_lib/boot.py
install --mode=644 smtool/smtool_lib/cpu.py %{buildroot}%{python_sitelib}/smtool_lib/cpu.py
install --mode=644 smtool/smtool_lib/distro.py %{buildroot}%{python_sitelib}/smtool_lib/distro.py
install --mode=644 smtool/smtool_lib/host.py %{buildroot}%{python_sitelib}/smtool_lib/host.py
install --mode=644 smtool/smtool_lib/kernel.py %{buildroot}%{python_sitelib}/smtool_lib/kernel.py
install --mode=644 smtool/smtool_lib/microcode.py %{buildroot}%{python_sitelib}/smtool_lib/microcode.py
install --mode=644 smtool/smtool_lib/parser.py %{buildroot}%{python_sitelib}/smtool_lib/parser.py
install --mode=644 smtool/smtool_lib/server.py %{buildroot}%{python_sitelib}/smtool_lib/server.py
install --mode=644 smtool/smtool_lib/sysfile.py %{buildroot}%{python_sitelib}/smtool_lib/sysfile.py
install --mode=644 smtool/smtool_lib/variant.py %{buildroot}%{python_sitelib}/smtool_lib/variant.py
install --mode=644 smtool/smtool_lib/vulnerabilities.py %{buildroot}%{python_sitelib}/smtool_lib/vulnerabilities.py
gzip -c smtool/smtool.man > %{buildroot}/usr/share/man/man8/oled-smtool.8.gz
chmod 644 %{buildroot}/usr/share/man/man8/oled-smtool.8.gz

#post install
%post

#kdump-utils
python /usr/sbin/oled-tools/kdump --add > /dev/null
service kdump restart > /dev/null || :

# lkce
if [ -f /etc/oled/lkce/lkce.conf ]
then
	mv /etc/oled/lkce/lkce.conf /etc/oled/lkce/lkce.conf.old
	/usr/sbin/oled-tools/lkce configure --default > /dev/null

	# We have to use the existing config file
	mv /etc/oled/lkce/lkce.conf /etc/oled/lkce/lkce.conf.rpmnew
	mv /etc/oled/lkce/lkce.conf.old /etc/oled/lkce/lkce.conf
fi

#Before uninstall
%preun
if [ $1 -eq 0 ]
then
	#kdump-utils
	python /usr/sbin/oled-tools/kdump --remove > /dev/null
	service kdump restart > /dev/null || :
fi

#After uninstall
%postun
if [ $1 -eq 0 ]
then
	# lkce
	if [ -f /etc/oled/lkce/lkce.conf ]
	then
		rm -f /etc/oled/kdump_pre.d/lkce-kdump
		rm -f /etc/oled/lkce/crash_cmds
		rm -f /etc/oled/lkce/lkce.conf.rpmnew
		rm -f /etc/oled/lkce/lkce.conf
		rmdir /etc/oled/lkce
	fi

	#kdump-utils
	rm -f /etc/oled/kdump_pre.sh
	rmdir /etc/oled/kdump_pre.d

        #smtool
        rm -f %{python_sitelib}/smtool_lib/*.pyc
        rm -f %{python_sitelib}/smtool_lib/*.pyo
        rmdir %{python_sitelib}/smtool_lib/

	#oled
	rmdir /usr/sbin/oled-tools
fi

%clean
rm -rf %{buildroot}

%files
#oled-tools
/usr/sbin/oled
/usr/share/man/man8/oled.8.gz

#kdump-utils
/usr/sbin/oled-tools/kdump

# lkce
/usr/sbin/oled-tools/lkce
/usr/sbin/oled-tools/lkce-kdump
/usr/share/man/man8/oled-lkce.8.gz

#gather
/usr/sbin/oled-tools/gather
/usr/share/man/man8/oled-gather.8.gz

#smtool
/usr/sbin/oled-tools/smtool
%exclude %{python_sitelib}/smtool_lib/*.pyc
%exclude %{python_sitelib}/smtool_lib/*.pyo
%{python_sitelib}/smtool_lib/vulnerabilities.py
%{python_sitelib}/smtool_lib/variant.py
%{python_sitelib}/smtool_lib/sysfile.py
%{python_sitelib}/smtool_lib/server.py
%{python_sitelib}/smtool_lib/parser.py
%{python_sitelib}/smtool_lib/microcode.py
%{python_sitelib}/smtool_lib/kernel.py
%{python_sitelib}/smtool_lib/host.py
%{python_sitelib}/smtool_lib/distro.py
%{python_sitelib}/smtool_lib/cpu.py
%{python_sitelib}/smtool_lib/boot.py
%{python_sitelib}/smtool_lib/base.py
%{python_sitelib}/smtool_lib/__init__.py
/usr/share/man/man8/oled-smtool.8.gz

%changelog
* Mon Jun 8 2020 Manjunath Patil <manjunath.b.patil@oracle.com> [0.2]
- Bug fixes post QA on oled-tools-0.1-1
- Bugs fixed: 31221495, 31226705, 31396705, 31410360, 31417143, 31454410

* Sun May 10 2020 Manjunath Patil <manjunath.b.patil@oracle.com> [0.1]
- first version
