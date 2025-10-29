#!/usr/bin/env python3
#
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

# Author: Arumugam Kolappan <aru.kolappan@oracle.com>

"""
This tool displays IP neighbor entries reading from files or dynamically
fetch from the server. The input files are collected from RDSInfo exawatcher
logs. The script can display IP-MAC mapping based on either an IP address
or MAC address, show number of neighbor entries per sample, display
IP/mac based on MAC count etc.
"""

import sys
import time
import argparse
import subprocess

MAC_LIST = {}


def store_neighbor(ip_addr, mac):
    """
    Add mac address to the list
    """
    if ip_addr not in MAC_LIST:
        MAC_LIST[ip_addr] = set()
    MAC_LIST[ip_addr].add(mac)


def read_neighbor(files, fpopen):
    """
    Process mac from files
    """
    print(f"Reading neighbor from files...", file=fpopen)
    for infile in files:
        try:
            with open(infile, "r") as flog:
                for line in flog.readlines():
                    words = line.split()
                    if words and len(words) > 5:
                        if words[1] == "dev" and words[3] == "lladdr":
                            ip_addr = words[0]
                            mac = str(words[4])
                            store_neighbor(ip_addr, mac)
        except (PermissionError, FileNotFoundError, IOError,
                IsADirectoryError, UnicodeDecodeError):
            print("Error: File error: {0}".format(infile))
            sys.exit(1)


def show_neighbor(cond, args, fpopen):
    """
    Print the IP+mac collected
    """
    print('-' * 60, file=fpopen)
    print("{:>18}{:>16}{:>21} ".format("IP_addr", "cnt", "mac"), file=fpopen)
    print('-' * 60, file=fpopen)
    matching = False

    cnt = 1
    for ip_addr in sorted(MAC_LIST):
        mac = MAC_LIST[ip_addr]
        if cond == "both" and ip_addr == args.addr and args.mac in mac:
            matching = True
        elif cond == "addr" and ip_addr == args.addr:
            matching = True
        elif cond == "mac" and args.mac in mac:
            matching = True
        elif cond == "count" and len(mac) >= int(args.count):
            matching = True
        elif cond == "list":
            matching = True

        if matching:
            print("{:>3}) {:<25}   {:<3} [ {} ]".format(cnt, ip_addr, len(mac),
                                                        ", ".join(mac)),
                  file=fpopen)
            cnt += 1
            matching = False
    print('-' * 60, file=fpopen)


def process_one_entry(line, prev_cnt, fpopen) -> int:
    """
    process single neighbor entry
    """
    total = prev_cnt
    words = line.split()
    if words:
        if words[0] == "zzz" and words[3] == "subcount:":
            if total > -1:
                print("Number of entries = {}\n".format(total), file=fpopen)
            total = 0
            print(line, file=fpopen)
            return total

        if (len(words) > 5 and words[1] == "dev" and words[3] == "lladdr"):
            total = total + 1
    return total


def show_neigh_count(files, fp_log):
    """
    Print number of entries in each sample
    """
    cnt = -1
    if files:
        print('-' * 60, file=fp_log)
        sno = 1
        for infile in files:
            try:
                with open(infile, "r") as fp_in:
                    print(f"\n{sno:>3}) file: {infile}\n", file=fp_log)
                    sno += 1
                    cnt = -1
                    for line in fp_in.readlines():
                        line = line.strip()
                        cnt = process_one_entry(line, cnt, fp_log)
                    if cnt > -1:
                        print("Number of Entries = {}\n".format(cnt),
                              file=fp_log)
                    else:
                        print("Number of Entries = 0\n", file=fp_log)
            except (PermissionError, FileNotFoundError, IOError):
                print("Error: File error: {0}".format(infile))
                return


def open_logfile(fname):
    """
    Open the file to read
    """
    try:
        if fname:
            fopen = open(fname, "w")
        else:
            fopen = sys.stdout
    except (PermissionError, FileNotFoundError, IOError):
        print("Error: File error: {0}".format(fname))
        fopen = sys.stdout
        sys.exit(1)
    return fopen


def collect_one_neigh(line):
    """
    Process one neighbor entry
    """
    words = line.split()
    if words and len(words) > 5:
        if (words[1] == "dev" and words[3] == "lladdr"):
            ip_addr = words[0]
            mac = str(words[4])
            store_neighbor(ip_addr, mac)


def process_neighbor(interval, count, fpopen):
    """
    Process neigh entry from the system
    """
    print(f"Reading neighbor from server: interval={interval} count={count}",
          file=fpopen)
    i = 0
    while i < int(count):
        try:
            data = subprocess.run("/usr/sbin/ip neigh", shell=True, check=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print(f"command failed: err: {data.returncode}. (iteration: {i})")
            return

        for line in data.stdout.splitlines():
            collect_one_neigh(line.decode('utf-8'))
        time.sleep(interval)
        i = i+1


def get_args() -> argparse.Namespace:
    """
    Read the arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--infiles", nargs="+",
                        help="Files from RDSinfo exawatcher logs. "
                        "To process already captured data.")
    parser.add_argument("-t", action='store_true',
                        help="Entry count per sample in files. "
                        "Use with -i option")
    parser.add_argument("-a", "--addr",
                        help="Display MACs matching given IP address")
    parser.add_argument("-m", "--mac",
                        help="Display IP addresses matching given MAC")
    parser.add_argument("-c", "--count",
                        help="Display entries matching >= 'count' "
                        "MACs for an IP address")
    parser.add_argument("-T", "--interval",
                        help="Collect data every T seconds [default=2]",
                        nargs='?', type=int, const=2, default=2)
    parser.add_argument("-C", "--max_sample",
                        help="Collect C samples [default=5]", nargs='?',
                        type=int, const=5, default=5)
    parser.add_argument("-o", "--outfile", help="Write output to a file")
    args = parser.parse_args()
    return args


def main():
    """
    neighbrwatch will show all mac addresses mapped to each IP address. This
    can show discrepancies in mac assignment (could help in duplicate IP issue)
    if an IP address shows MAC association more than others. It processes
    entries from the log file as well as read current data from running system.
    Moreover, it provides other options such as: show IP-MAC list based on IP
    or mac address, neighbor entry count in each section in the log file etc.
    The output can be written to a file.
    """

    args = get_args()

    fp_open = open_logfile(args.outfile)

    if args.infiles:
        # read from file
        if args.outfile:
            print(f"Reading neighbor from files...")
        read_neighbor(args.infiles, fp_open)
    else:
        # read from system
        if args.outfile:
            print(f"Reading neighbor from server: interval={args.interval} ",
                  f"count={args.max_sample}")
        process_neighbor(args.interval, args.max_sample, fp_open)

    if args.t and args.infiles:
        show_neigh_count(args.infiles, fp_open)
    elif args.addr and args.mac:
        show_neighbor("both", args, fp_open)
    elif args.addr:
        show_neighbor("addr", args, fp_open)
    elif args.mac:
        show_neighbor("mac", args, fp_open)
    elif args.count:
        show_neighbor("count", args, fp_open)
    else:
        show_neighbor("list", 0, fp_open)

    fp_open.close()


if __name__ == "__main__":
    main()
