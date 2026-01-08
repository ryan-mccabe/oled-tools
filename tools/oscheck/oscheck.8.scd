sosdiff(8)

# NAME

oscheck - Validate system configuration

# SYNOPSIS

oled oscheck [-h|--help] [--debug] [--sos <sosreport root dir>] [<rules file>]

# DESCRIPTION

*oscheck* validates various aspects of system configuration against json
rules files. The program is plugin-based, and currently the following plugins
are supported: files, mounts, kmod, kernel command line, packages,
processes, sysctl, and systemd. There are example rule files in
*/etc/oled/oscheck/rules/example*.

# OPTIONS

*-h|--help*
	Display help.

*--debug*
	Display debugging information during the rule validation process.

*--sos <directory>*
	Run against the sosreport whose root directory is at the path specified by *<directory>*.

# EXAMPLES

- Run *oscheck* against a live system. Autodetect what kind of system it's
  running on, and automatically select the appropriate rules file.

```
	$ oled oscheck
```


- Run *oscheck* against an sosreport. Autodetect what kind of system the
  sos report was generated against, and automatically select the appropriate
  rules file.

```
	$ oled oscheck --sos /tmp/sosreport-hostname-2025-09-30-bhqykva
```

- Run *oscheck* against a live system. Specify the rules file instead
  of attempting to autodetect which rules to use.
```
	$ oled oscheck /etc/oled/oscheck/rules/OCI_guest/8/rules.json
```
# EXAMPLE OUTPUT

```
$ oled oscheck  /etc/oled/oscheck/rules/example/test.json 
ERROR: ❌ FILE: /etc/crontab failed validation.
ERROR:   ↳ /etc/crontab: size failed condition {'gt': 0}
INFO: ✅️ FILE: /etc/shadow passed all checks.
ERROR: ❌ FILE: /etc/ssh/sshd_config failed validation.
ERROR:   ↳ Could not get all file attributes.
ERROR:   ↳ ERROR: Permission denied: /etc/ssh/sshd_config
ERROR: ❌ FILE: /etc/passwd failed validation.
ERROR:   ↳ /etc/passwd: file_contents failed condition {'identical': {'type': 'sha256', 'value': 'fad2d5230196c5ee7924815bc9abfcf341c3c991d3429a3f0c6aab99ebeaff87'}}
ERROR: ❌ FILE: /tmp/known_file failed validation.
ERROR:   ↳ /tmp/known_file does not exist.
INFO: ✅️ FILE: /etc/resolv.conf passed all checks.
ERROR: ❌ FILE: /tmp/rss_key2 failed validation.
ERROR:   ↳ /tmp/rss_key2 does not exist.
INFO: ✅️ FILE: /var/log/messages passed all checks.
INFO: ✅️ FILE: /var/log/secure passed all checks.
INFO: ✅️ FILE: /var/spool/mail/root passed all checks.
ERROR: ❌ FILE: /var/spool/mail/user failed validation.
ERROR:   ↳ /var/spool/mail/user does not exist.
INFO: ✅️ FILE: /etc/group passed all checks.
ERROR: ❌ FILE: /etc/sysctl.conf failed validation.
ERROR:   ↳ /etc/sysctl.conf: file_contents failed condition {'contains': 'kernel.unknown_nmi_panic = 1'}
ERROR: ❌ FILE: /var/lib/systemd/random-seed failed validation.
ERROR:   ↳ Could not get all file attributes.
ERROR:   ↳ ERROR: Permission denied: /var/lib/systemd/random-seed
ERROR: ❌ FILE: /tmp/testfile failed validation.
ERROR:   ↳ /tmp/testfile does not exist.
INFO: ✅️ LIVE SYSCTL kernel.randomize_va_space passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.all.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.cscotun0.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.default.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.enp0s13f0u2u4i5.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.lo.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.virbr0.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.wlp0s20f3.arp_ignore passed all checks.
INFO: ✅️ LIVE SYSCTL vm.swappiness passed all checks.
INFO: ✅️ LIVE SYSCTL net.ipv4.conf.default.accept_redirects passed all checks.
INFO: ✅️ CONFIG SYSCTL net.ipv4.conf.default.accept_redirects from /etc/sysctl.d/50-libreswan.conf passed all checks
ERROR: ❌ LIVE SYSCTL: net.core.netdev_rss_key failed validation
ERROR:   ↳ LIVE SYSCTL net.core.netdev_rss_key: net.core.netdev_rss_key failed condition {'identical': {'type': 'file', 'value': '/tmp/rss_key'}}
ERROR:   ↳ LIVE SYSCTL net.core.netdev_rss_key: net.core.netdev_rss_key - Reference file '/tmp/rss_key' does not exist.
INFO: ✅️ LIVE SYSCTL kernel.hardlockup_panic passed all checks.
ERROR: ❌ LIVE SYSCTL: kernel.unknown_nmi_panic failed validation
ERROR:   ↳ LIVE SYSCTL kernel.unknown_nmi_panic: kernel.unknown_nmi_panic failed condition eq 1
INFO: ✅️ LIVE SYSCTL vm.nr_hugepages passed all checks.
```

# SEE ALSO

oled(8)
