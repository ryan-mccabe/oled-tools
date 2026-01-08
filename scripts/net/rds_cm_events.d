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
 * Author(s): Manjunath Patil.
 * Purpose: This script tracks CM packet completions
 * Prerequisites: Refer to the file rds_cm_events_example.txt
 * Sample output: Refer to the file rds_cm_events_example.txt
 */

/*
 * min_kernel 5.4.17-2122.303.1,5.15.0-2.52.2,6.12.0-0.0.1
 */

::BEGIN
{
/*
enum rdma_cm_event_type {
        RDMA_CM_EVENT_ADDR_RESOLVED,
        RDMA_CM_EVENT_ADDR_ERROR,
        RDMA_CM_EVENT_ROUTE_RESOLVED,
        RDMA_CM_EVENT_ROUTE_ERROR,
        RDMA_CM_EVENT_CONNECT_REQUEST,
        RDMA_CM_EVENT_CONNECT_RESPONSE,
        RDMA_CM_EVENT_CONNECT_ERROR,
        RDMA_CM_EVENT_UNREACHABLE,
        RDMA_CM_EVENT_REJECTED,
        RDMA_CM_EVENT_ESTABLISHED,
        RDMA_CM_EVENT_DISCONNECTED,
        RDMA_CM_EVENT_DEVICE_REMOVAL,
        RDMA_CM_EVENT_MULTICAST_JOIN,
        RDMA_CM_EVENT_MULTICAST_ERROR,
        RDMA_CM_EVENT_ADDR_CHANGE,
*/

        CM_EVENT[0] = "ADDR_RESOLVED";
        CM_EVENT[1] = "ADDR_ERROR";
        CM_EVENT[2] = "ROUTE_RESOLVED";
        CM_EVENT[3] = "ROUTE_ERROR";
        CM_EVENT[4] = "CONNECT_REQUEST";
        CM_EVENT[5] = "CONNECT_RESPONSE";
        CM_EVENT[6] = "CONNECT_ERROR";
        CM_EVENT[7] = "UNREACHABLE";
        CM_EVENT[8] = "REJECTED";
        CM_EVENT[9] = "ESTABLISHED";
        CM_EVENT[10] = "DISCONNECTED";
        CM_EVENT[11] = "DEVICE_REMOVAL";
        CM_EVENT[12] = "MULTICAST_JOIN";
        CM_EVENT[13] = "MULITCAST_ERROR";
        CM_EVENT[14] = "ADDR_CHANGE";
}

::rds_rdma_cm_event_handler_cmn:entry
/ arg2 /
{
        this->event = (struct rdma_cm_event *)arg1;
        this->conn = (struct rds_connection *)arg2;
        this->ic = (struct rds_ib_connection *)this->conn->c_path[0].cp_transport_data;
        this->sip = &this->conn->c_laddr.in6_u.u6_addr32[3];
        this->dip = &this->conn->c_faddr.in6_u.u6_addr32[3];
        this->tos = this->conn->c_tos;

        printf("%Y %lu %s: [<%s,%s,%d>] %s\n",
                walltimestamp, timestamp, probefunc,
                inet_ntoa(this->sip), inet_ntoa(this->dip), this->tos,
                CM_EVENT[this->event->event]);
}

::rds_rdma_cm_event_handler_cmn:entry
/ !arg2 /
{
        self->track_rds_conn_create = 1;
        self->event = (struct rdma_cm_event *)arg1;
}

::rds_conn_create:return
/ self->track_rds_conn_create /
{
        this->conn = (struct rds_connection *)arg1;
        this->event = self->event;

        this->ic = (struct rds_ib_connection *)this->conn->c_path[0].cp_transport_data;
        this->sip = &this->conn->c_laddr.in6_u.u6_addr32[3];
        this->dip = &this->conn->c_faddr.in6_u.u6_addr32[3];
        this->tos = this->conn->c_tos;

        printf("%Y %lu %s: [<%s,%s,%d>] %s\n",
                walltimestamp, timestamp, probefunc,
                inet_ntoa(this->sip), inet_ntoa(this->dip), this->tos,
                CM_EVENT[this->event->event]);

        self->track_rds_conn_create = 0;
}

