#!/usr/sbin/dtrace -Cqs

/*
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 2 only, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * version 2 for more details (a copy is included in the LICENSE file that
 * accompanied this code).
 *
 * You should have received a copy of the GNU General Public License version
 * 2 along with this work; if not, see <https://www.gnu.org/licenses/>.
 *
 * Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
 * or visit www.oracle.com if you need additional information or have any
 * questions.
 */

/*
 * Author: Arumugam Kolappan
 * Purpose: This script tracks how long RDS sockets are congested and provides
 * histogram of congestion duration in usec. You can pass port and/or IP_address as
 * arguments to the script.
 * ex: ./rds_cong_track.d -DIP="192.168.100.10" -DPORT=5042
 *
 * Prerequisites: Refer to the file rds_cong_track_example.txt
 * Sample output: Refer to the file rds_cong_track_example.txt
 */

/*
 * min_kernel 4.14.35-2042,5.4.17-2136.323.8.1,5.15.0-300.153.1,6.12.0-0.4.2
 */

#define NANO2USEC (1000)
#define NANO2SEC (1000 * 1000 * 1000)

#define _STR(x) #x
#define STR(x)  _STR(x)

dtrace:::BEGIN
{
	port = 0;
#ifdef PORT
	port = PORT;
#endif
	ip_addr = "";
#ifdef IP
	ip_addr = STR(IP);
#endif
	flt = 0;
	flt = (ip_addr != "" && port != 0) ? 1 : flt;
	flt = (flt == 0 && ip_addr != "")? 2: flt;
	flt = (flt == 0 && port != 0) ? 3: flt;
	flt = (flt == 0) ? 4: flt;

	start_ts = timestamp;
	congested = 0;

        printf(" Track RDS socket congestion Timing\n");
        printf("   ('value' in usec)  \n\n");
        printf("  Arg IP: %s\n", (ip_addr == "") ? "-": ip_addr);
        printf("Arg Port: %d\n\n", port);
        printf("Start Time: %Y [%d]\n\n", walltimestamp, start_ts);
}

fbt:rds:rds_cong_set_bit:entry
{
	this->map = (struct rds_cong_map *)arg0;
	this->port = ntohs(arg1);
	this->addr = inet_ntoa(&this->map->m_addr.in6_u.u6_addr32[3]);
	setbit[this->addr, this->port]= timestamp;
}

fbt:rds:rds_cong_clear_bit:entry
{
	this->map = (struct rds_cong_map *)arg0;
	this->port = ntohs(arg1);
	this->addr = inet_ntoa(&this->map->m_addr.in6_u.u6_addr32[3]);
}

/* case 1: IP and PORT are given */
fbt:rds:rds_cong_clear_bit:entry
/
  (flt == 1) &&
  (port == this->port) &&
  (ip_addr == this->addr) &&
  (setbit[this->addr, this->port] != 0)
/
{
	this->set_ts = setbit[this->addr, this->port];
	this->delta = (timestamp - this->set_ts)/NANO2USEC;
	@cong_ip_port[this->addr, this->port, pid, execname] = quantize(this->delta);
	congested = 1;
}

/* case 2: Only IP is given */
fbt:rds:rds_cong_clear_bit:entry
/
  (flt == 2) &&
  (ip_addr == this->addr) &&
  (setbit[this->addr, this->port] != 0)
/
{
	this->set_ts = setbit[this->addr, this->port];
	this->delta = (timestamp - this->set_ts)/NANO2USEC;
	@cong_ip_port[this->addr, this->port, pid, execname] = quantize(this->delta);
	@cong_allports[this->addr, "all_ports"] = quantize(this->delta);
	congested = 1;
}

/* case 3: Only PORT is given */
fbt:rds:rds_cong_clear_bit:entry
/
  (flt == 3) &&
  (port == this->port) &&
  (setbit[this->addr, this->port] != 0)
/
{
	this->set_ts = setbit[this->addr, this->port];
	this->delta = (timestamp - this->set_ts)/NANO2USEC;
	@cong_ip_port[this->addr, this->port, pid, execname] = quantize(this->delta);
	congested = 1;
}

/* case 4: PORT and IP are not given */
fbt:rds:rds_cong_clear_bit:entry
/
  (flt == 4) &&
  (setbit[this->addr, this->port] != 0)
/
{
	this->set_ts = setbit[this->addr, this->port];
	this->delta = (timestamp - this->set_ts)/NANO2USEC;
	@cong_ip_port[this->addr, this->port, pid, execname] = quantize(this->delta);
	@cong_allports[this->addr, "all_ports"] = quantize(this->delta);
	@cong_allip_allport["all_ips", "all_ports"] = quantize(this->delta);
	congested = 1;
}

fbt:rds:rds_cong_clear_bit:entry
{
	setbit[this->addr, this->port] = 0;
}

dtrace:::END
/
  (congested == 1)
/
{
        end_ts = timestamp;
        run_ts = end_ts - start_ts;
        printf("End Time: %Y [%d]\n", walltimestamp, end_ts);
        printf("Run duration = %d sec\n", run_ts/NANO2SEC);
        printf("----------------------------------\n");
        printf("***  Congestion Detected ***\n");
        printf("----------------------------------\n");
        printf("\n%15s %42s %8s   %-7s\n", "IP_ADDRESS", "Port", "PID", "COMM");
        printf("%15s %42s %8s   %-7s", "----------", "----", "---", "----");
}

dtrace:::END
/
  (congested == 0)
/
{
        end_ts = timestamp;
        run_ts = end_ts - start_ts;
        printf("End Time: %Y [%d]\n", walltimestamp, end_ts);
        printf("Run duration = %d sec\n", run_ts/NANO2SEC);
        printf("----------------------------------\n");
        printf("***   No Congestion Detected   ***\n");
        printf("----------------------------------\n");
}
