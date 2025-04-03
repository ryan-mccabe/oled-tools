sosdiff(8)

# NAME

sosdiff - Compare two sos reports

# SYNOPSIS

sosdiff [-h|--help] [-d|--detail] [-o|--override] [-c|--color] dir1 dir2

# DESCRIPTION

*sosdiff* is used to compare two different sos reports, and will highlight the differences between the two. The tool has several modules, each of which will compare a section of the two sos reports, for example, meminfo output, sysctl settings, and uname.  The idea behind the tool is to highlight the differences between the sos reports.  In this way you can compare a working system with a system that has an issue, or compare a system before and after upgrading.

# OPTIONS

*-h|--help*
	Display help.

*-d|--detail*
	By default *sosdiff* will display only those values that differ between the two reports.  Specifying *--detail* will instruct *sosdiff* to show all the values.  Values that differ are identified by a leading ">".

*-o|--override*
	*sosdiff* will refuse to compare two sos reports where the OS Version or architecture differs.  However you can specify *--override* to force the tool to compare anyway.

*-c|--color*
	The output of *sosdiff* automatically has the differences in values highlighted using *bold*.  If you redirect the output this formatting is removed.  You can specify --color to leave the formatting in when redirecting.

*dir1 and dir2*
	These are the paths to the top level sosreport directory.  

# EXAMPLES

- Run *sosdiff* and pipe it to *less* and retain the *bold* characters.

```
	$ sosdiff --color /var/tmp/sosreport-host1/ /var/tmp/sosreport-host2/ | less -r
```


- Run *sosdiff* showing all the data, not just the values that differ.  This could produce a lot of output.

```
	$ sosdiff --detail /var/tmp/sosreport-host1/ /var/tmp/sosreport-host2/ | less
```

# EXAMPLE OUTPUT

```
sosdiff v0.2  Arguments validated .. beginning analysis ...
   First Report                       Second Report
>  myhostname                         myhostname
>  5.4.17-2136.336.5.1.el8uek.x86_64  5.4.17-2136.337.5.1.el8uek.x86_64


Meminfo Comparison_______________________________________________________________
       Name    First Report    Second Report         Diff
>  MemTotal     65276328 kB      65276320 kB        -8 kB
>   MemFree     18850388 kB      41213680 kB  22363292 kB
>  SwapFree     31454972 kB      31457276 kB      2304 kB
>      Slab      1529188 kB        912924 kB   -616264 kB
>    Percpu        73472 kB         21184 kB    -52288 kB


RPM Comparison__________________________________________________________________
   RPM Name                      First Report                                        Second Report
>  McAfeeESP                     MISSING                                             10.7.18-3097.x86_64
>  McAfeeFW                      MISSING                                             10.7.18-102.x86_64
>  McAfeeRt                      MISSING                                             10.7.18-3097.x86_64
>  bcc                           0.25.0-7.el8.x86_64                                 0.25.0-9.el8_10.x86_64
>  bcc-tools                     0.25.0-7.el8.x86_64                                 0.25.0-9.el8_10.x86_64
>  binutils                      2.30-123.0.2.el8.x86_64                             2.30-125.0.1.el8_10.x86_64
```

# SEE ALSO

oled(8)
