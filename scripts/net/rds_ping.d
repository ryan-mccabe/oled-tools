#!/usr/sbin/dtrace -Cqs

/*
 * Author(s): Juan Manuel Garcia Briones, Nagappan Ramasamy Palaniappan.
 * Purpose: This script is intended to track latencies between the kernel
 * functions that are used for rds-ping for ping and pong side.
 * Prerequisites: Refer to the file rds_ping_latency_example.txt
 * Sample output: Refer to the file rds_ping_latency_example.txt
 */

/*
 * min_kernel 4.14.35-2042,5.4.17-2136.323.8.1,5.15.0-300.153.1,6.12.0-0.4.2
 */

#define RDS_MSG_SIZE_PING_PONG 48
#define NANO2USEC (1000)

#pragma D option dynvarsize=32000000

dtrace:::BEGIN
{
    self->conn = (struct rds_connection *) 0;
    self->inc = (struct rds_incoming *) 0;
    self->rm = (struct rds_message *) 0;
    self->ret = (int) 0;

#ifdef MIN_LAT
    min_lat = MIN_LAT;
#else
    min_lat = 500000; /* 0.5 sec */
#endif

#ifdef DEBUG
    printf("==============================================================================================\n");
    printf("| rds-ping application                       |                         user space            |\n");
    printf("==============================================================================================\n");
    printf("          v                       ^                                                           \n");
    printf("          |                       |                                                           \n");
    printf("  +------------------+    +-------------------------+            +------------------+         \n");
    printf("  |    rds_sendmsg   |    | rds_ib_inc_copy_to_user |            |  rds_send_pong   | <------ \n");
    printf("  +------------------+    +-------------------------+            +------------------+       | \n");
    printf("          |                       |                                     |                   | \n");
    printf("          v                       ^                                     v                   | \n");
    printf("  +------------------+        +--------------------+             +------------------+       | \n");
    printf("  |   rds_ib_xmit    |        | rds_recv_incoming  |             |   rds_ib_xmit    |       | \n");
    printf("  +------------------+        +--------------------+             +------------------+       | \n");
    printf("          |                       ^                                     |                   | \n");
    printf("          v                       |                                     v                   | \n");
    printf("  +--------------------+          |                         +--------------------+          | \n");
    printf("  |  rds_message_put   |          ------------------------  |   rds_message_put  |          | \n");
    printf("  +--------------------+                                    +--------------------+          | \n");
    printf("          |                                                                                 | \n");
    printf("          |                                                                                 | \n");
    printf("          |                                                                                 | \n");
    printf("          |                                          +-------------------+                  | \n");
    printf("          |----------------------------------------- | rds_recv_incoming | ------------------ \n");
    printf("                                                     +-------------------+                    \n");
    printf(" |---------------------Ping-----------------------| |=================Pong==================|\n\n\n");

    printf("====Time measurements on Ping side====                                                                                \n\n");
    printf("         Δtime = sendq_wt       Δtime = comp_wt                                 Δtime = recvq_wt                        \n");
    printf("        /                \\   /                \\                             /                  \\                     \n");
    printf("       /                  \\ /                  \\                           /                    \\                    \n");
    printf("+-------------+      +-------------+      +-----------------+      +-------------------+     +-------------------------+\n");
    printf("| rds_sendmsg |  =>  | rds_ib_xmit |  =>  | rds_message_put |  =>  | rds_recv_incoming | ... | rds_ib_inc_copy_to_user |\n");
    printf("+-------------+      +-------------+      +-----------------+      +-------------------+     +-------------------------+\n");
    printf("      \\                                                                                           /                    \n");
    printf("       \\ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ Δtime = total _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ /                 \n\n\n");
    printf("====Time measurements on Pong side====                                                                                \n\n");
    printf("               Δtime = recvq_wt         Δtime = sendq_wt       Δtime = comp_wt                                          \n");
    printf("             /                \\      /                \\    /                 \\                                       \n");
    printf("            /                  \\    /                  \\  /                   \\                                      \n");
    printf("+-------------------+      +---------------+      +-------------+      +-----------------+                              \n");
    printf("| rds_recv_incoming |  =>  | rds_send_pong |  =>  | rds_ib_xmit |  =>  | rds_message_put |                              \n");
    printf("+-------------------+      +---------------+      +-------------+      +-----------------+                              \n");
    printf("           \\                                                                   /                                       \n");
    printf("            \\ _ _ _ _ _ _ _ _ _ _ _ _ Δtime = total _ _ _ _ _ _ _ _ _ _ _ _ _ /                                        \n\n\n");
    printf("DEBUG Enabled\n");
#endif
    printf("Note: Displaying only packets with lat >= MIN_LAT (%d USEC)\n", min_lat);
    /*
     * Column explanation:
     *
     * sendq_wt: Time in usec [from pong_send to xmit in case for pong] and [from send_msg to xmit for ping].
     * comp_wt: Time in usec from xmit to sendcomp.
     * recvq_t: Time in usec [from recv_inc to pong_send for pong] and [from recv_in to copy_to_user for ping]
     * total: Is the total latency from end-to-end on the respective side
     * */
    printf("[%-20s] %-38s %-4s %4s %12s %12s %12s %12s\n",
           "Time", "Connection", "Req", "SrcPort",
           "sendq_wt", "comp_wt", "recvq_wt", "total");
}

/* BEGIN PING */

fbt:rds:rds_sendmsg:entry
/
  (arg0 != 0) &&
  (self->rs = (struct rds_sock *) ((struct socket *) arg0)->sk) &&
  (self->rs->rs_conn_port == 0) &&
  (arg2 == 0)
/
{
    this->rs = self->rs;
    this->msgp = (struct msghdr *) arg1;
    this->usin = (struct sockaddr_in*) this->msgp->msg_name;
    this->saddr = inet_ntoa(&this->rs->rs_bound_sin6.sin6_addr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->usin->sin_addr.s_addr);
    this->qos = this->rs->rs_tos;
    this->sport = this->rs->rs_bound_sin6.sin6_port;
    this->dport = this->rs->rs_conn_port;

    sendmsg[this->saddr, this->daddr, this->qos, this->sport, this->dport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_sendmsg] <%s,%s,%d> ping sport=%d dport=%d rs=%p\n",
           walltimestamp, timestamp, this->saddr, this->daddr, this->qos,
           this->sport, this->dport, this->rs);
#endif
    self->rs = 0;
}

fbt:rds:rds_sendmsg:return
{
    self->rs = 0;
}

fbt:rds_rdma:rds_ib_xmit:entry
/
  (arg1 != 0) &&
  (self->rm = (struct rds_message *) arg1) &&
  (self->inc = (struct rds_incoming *) &(self->rm->m_inc)) &&
  (self->rds_hdr = ((struct rds_header *) &(self->inc->i_hdr))) &&
  (self->rds_hdr->h_sport != 0) &&
  (self->rds_hdr->h_dport == 0) &&
  (self->rds_hdr->h_len == 0)
/
{
  /* Blank */
}

fbt:rds_rdma:rds_ib_xmit:return
/
  (arg1 != 0) &&
  (self->ret = arg1) &&
  (self->rm != 0) &&
  (self->ret == RDS_MSG_SIZE_PING_PONG) &&
  (self->rds_hdr->h_sport != 0) &&
  (self->rds_hdr->h_dport == 0) &&
  (self->rds_hdr->h_len == 0)
/
{
    this->inc = (struct rds_incoming*) &self->rm->m_inc;
    this->rds_hdr = (struct rds_header*) &this->inc->i_hdr;
    this->cpath = (struct rds_conn_path*) this->inc->i_conn_path;
    this->conn = (struct rds_connection*) this->cpath->cp_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;
    this->sport = this->rds_hdr->h_sport;
    this->dport = this->rds_hdr->h_dport;

    xmit[this->saddr, this->daddr, this->qos, this->sport, this->dport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_ib_xmit] <%s,%s,%d> ping sport=%d dport=%d conn=%p inc=%p cpath=%p rds_hdr=%p\n",
           walltimestamp, timestamp, this->saddr, this->daddr, this->qos,
           this->sport, this->dport, this->conn, this->inc, this->cpath, this->rds_hdr);
#endif

    self->rm = 0;
    self->ret = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

/* fbt:rds_rdma:rds_ib_xmit:return look at the pong side. */

/* rawtp:*:*:rds_ib_send_cqe_handler look at the pong side. */

fbt:rds:rds_message_put:entry
/
  (self->conn != 0) &&
  (arg0 != 0) &&
  (self->rm = (struct rds_message *) arg0) &&
  (self->inc = (struct rds_incoming *) &(self->rm->m_inc)) &&
  (self->rds_hdr = ((struct rds_header *) &(self->inc->i_hdr))) &&
  (self->rds_hdr->h_sport != 0) &&
  (self->rds_hdr->h_dport == 0) &&
  (self->rds_hdr->h_len == 0)
/
{
    this->rm = (struct rds_message *) arg0;
    this->inc = (struct rds_incoming *) &this->rm->m_inc;
    this->rds_hdr = (struct rds_header *) &this->inc->i_hdr;
    this->cpath = (struct rds_conn_path *) this->inc->i_conn_path;
    this->conn = (struct rds_connection *) this->cpath->cp_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;
    this->sport = this->rds_hdr->h_sport;
    this->dport = this->rds_hdr->h_dport;

    sendcomp[this->saddr, this->daddr, this->qos, this->sport, this->dport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_message_put] <%s,%s,%d> ping sport=%d dport=%d conn=%p rm=%p inc=%p rds_hdr=%p cpath=%p\n",
           walltimestamp, timestamp, this->saddr, this->daddr, this->qos,
           this->sport, this->dport, this->conn, this->rm, this->inc, this->rds_hdr, this->cpath);
#endif

    self->conn = 0;
    self->rm = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

/* fbt:rds:rds_message_put:return look at the pong side */

fbt:rds:rds_recv_incoming:entry
/
  (arg0 != 0) &&
  (self->conn = (struct rds_connection *) arg0) &&
  (arg3 != 0) &&
  (self->inc = (struct rds_incoming *) arg3) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0)
/
{
    this->saddr = inet_ntoa(&((struct in6_addr *) arg1)->in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&((struct in6_addr *) arg2)->in6_u.u6_addr32[3]);
    this->qos = self->conn->c_tos;
    this->inc = self->inc;
    this->rds_hdr = self->rds_hdr;
    this->dport = this->rds_hdr->h_dport;
    this->sport = this->rds_hdr->h_sport;

    /* incoming ping: hence switching addrs and ports. */
    recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_recv_incoming] <%s,%s,%d> ping sport=%d dport=%d inc=%p rds_hdr=%p\n",
           walltimestamp, timestamp, this->daddr, this->saddr, this->qos,
           this->dport, this->sport, this->inc, this->rds_hdr);
#endif

    self->conn = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

/* fbt:rds:rds_recv_incoming:return is on the pong side. */
fbt:rds_rdma:rds_ib_inc_copy_to_user:entry
/
  #ifdef uek8
	(arg1 != 0) &&
	(self->inc = (struct rds_incoming *) arg1)
  #else
	(arg0 != 0) &&
	(self->inc = (struct rds_incoming *) arg0)
  #endif
/
{
  /* Blank */
}

fbt:rds_rdma:rds_ib_inc_copy_to_user:return
/
  (arg1 >= 0) &&
  (self->inc != 0) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0)
/
{
  this->conn = (struct rds_connection *) self->inc->i_conn;
  this->saddr_cmp = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
  this->daddr_cmp = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
  self->time_diff = (timestamp - sendmsg[this->saddr_cmp, this->daddr_cmp, this->conn->c_tos, self->rds_hdr->h_dport, self->rds_hdr->h_sport])/NANO2USEC;
}

fbt:rds_rdma:rds_ib_inc_copy_to_user:return
/
  (arg1 >= 0) &&
  (self->inc != 0) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0) &&
  (self->time_diff != 0) &&
  (self->time_diff >= min_lat)
/
{
    this->inc = (struct rds_incoming *) self->inc;
    this->rds_hdr = (struct rds_header *)&this->inc->i_hdr;
    this->cpath = (struct rds_conn_path *)this->inc->i_conn_path;
    this->conn = (struct rds_connection *)this->inc->i_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;
    this->sport = this->rds_hdr->h_sport;
    this->dport = this->rds_hdr->h_dport;

    /* incoming ping: hence switch sport and dport */
    copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_ib_inc_copy_to_user] <%s,%s,%d> Ping sport=%d dport=%d conn=%p inc=%p rds_hdr=%p cpath=%p comm=%s sendmsg_ts=%d xmit_ts=%d sendcomp_ts=%d recv_inc_ts=%d copy_to_user_ts=%d\n",
           walltimestamp, timestamp, this->saddr, this->daddr, this->qos,
           this->dport, this->sport, this->conn, this->inc, this->rds_hdr,
           this->cpath, execname,
           sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport],
           xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport],
           sendcomp[this->saddr, this->daddr, this->qos, this->dport, this->sport],
           recv_inc[this->saddr, this->daddr, this->qos, this->dport, this->sport],
           copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport]);
#endif

    sendq_wt = (xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport] - sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport])/NANO2USEC;
    comp_wt = (sendcomp[this->saddr, this->daddr, this->qos, this->dport, this->sport] - xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport])/NANO2USEC;
    recvq_wt = (copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] - recv_inc[this->saddr, this->daddr, this->qos, this->dport, this->sport])/NANO2USEC;
    rds_wt = (copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] - sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport])/NANO2USEC;

    this->sep = ((this->qos >= 100)? "" : (this->qos >= 10)? " " : "  ");
    printf("[%Y] <%s,%s,%d> %s %4s %7d %12s %12s %12s %12s\n",
           walltimestamp, this->saddr, this->daddr, this->qos, this->sep, "Ping", this->dport,
           (xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport] && sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport])? lltostr(sendq_wt) : "-1",
           (sendcomp[this->saddr, this->daddr, this->qos, this->dport, this->sport] && xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport])? lltostr(comp_wt) : "-1",
           (copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] && recv_inc[this->saddr, this->daddr, this->qos, this->dport, this->sport])? lltostr(recvq_wt) : "-1",
           (copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] && sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport])? lltostr(rds_wt) : "-1");

    xmit[this->saddr, this->daddr, this->qos, this->dport, this->sport] = 0;
    sendmsg[this->saddr, this->daddr, this->qos, this->dport, this->sport] = 0;
    sendcomp[this->saddr, this->daddr, this->qos, this->dport, this->sport] = 0;
    copy_to_user[this->saddr, this->daddr, this->qos, this->dport, this->sport] = 0;
    recv_inc[this->saddr, this->daddr, this->qos, this->dport, this->sport] = 0;
    self->ret = 0;
    self->inc = 0;
    self->rds_hdr = 0;
    self->time_diff = 0;
}

fbt:rds_rdma:rds_ib_inc_copy_to_user:return
{
    self->ret = 0;
    self->inc = 0;
    self->rds_hdr = 0;
    self->time_diff = 0;
}

/* BEGIN PONG */
fbt:rds:rds_recv_incoming:entry
/
  (arg0 != 0) &&
  (self->conn = (struct rds_connection *) arg0) &&
  (arg3 != 0) &&
  (self->inc = (struct rds_incoming *) arg3) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport != 0) &&
  (self->rds_hdr->h_dport == 0) &&
  (self->rds_hdr->h_len == 0)
/
{
    this->saddr = inet_ntoa(&((struct in6_addr *) arg1)->in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&((struct in6_addr *) arg2)->in6_u.u6_addr32[3]);
    this->rds_hdr = self->rds_hdr;
    this->dport = this->rds_hdr->h_dport;
    this->sport = this->rds_hdr->h_sport;
    this->qos = self->conn->c_tos;

    /* incoming pong: hence switching addrs and ports. */
    pong_recv_inc[this->saddr, this->daddr, this->qos, this->sport, this->dport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_recv_incoming] <%s,%s,%d> pong sport=%d dport=%d rds_hdr=%p\n",
           walltimestamp, timestamp, this->saddr, this->daddr, this->qos,
           this->sport, this->dport, this->rds_hdr);
#endif

    self->conn = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

/* This return clause works for ping and pong side. */
fbt:rds:rds_recv_incoming:return
{
    self->conn = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

fbt:rds:rds_send_pong:entry
{
    this->cp = (struct rds_conn_path *) arg0;
    this->dport = (__be16 ) arg1;
    this->sport = 0; /* For pong sport will be 0 */
    this->conn = (struct rds_connection *) this->cp->cp_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;

    pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_send_pong] <%s,%s,%d> pong sport=%d dport=%d conn=%p cp=%p\n",
           walltimestamp, timestamp, this->daddr, this->saddr, this->qos,
           this->dport, this->sport, this->conn, this->cp);
#endif
}


fbt:rds_rdma:rds_ib_xmit:entry
/
  (arg1 != 0) &&
  (self->rm = (struct rds_message *) arg1) &&
  (self->inc = (struct rds_incoming *) &self->rm->m_inc) &&
  (self->rds_hdr = (struct rds_header *) &self->inc->i_hdr) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0)
/
{
  /* Blank */
}

fbt:rds_rdma:rds_ib_xmit:return
/
  (arg1 != 0) &&
  (self->ret = arg1) &&
  (self->rm != 0) &&
  (self->ret == RDS_MSG_SIZE_PING_PONG) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0)
/
{
    this->inc = (struct rds_incoming *) &self->rm->m_inc;
    this->rds_hdr = (struct rds_header *) &this->inc->i_hdr;
    this->cpath = (struct rds_conn_path *) this->inc->i_conn_path;
    this->conn = (struct rds_connection *) this->cpath->cp_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;
    this->sport = this->rds_hdr->h_sport;
    this->dport = this->rds_hdr->h_dport;

    pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_ib_xmit] <%s,%s,%d> pong sport=%d dport=%d conn=%p cp=%p inc=%p rds_hdr=%p\n",
           walltimestamp, timestamp, this->daddr, this->saddr, this->qos,
           this->dport, this->sport, this->conn, this->cpath, this->inc, this->rds_hdr);
#endif

    self->ret = 0;
    self->rm = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

/* This probe works for ping and pong side. */
fbt:rds_rdma:rds_ib_xmit:return
{
    self->ret = 0;
    self->rm = 0;
    self->inc = 0;
    self->rds_hdr = 0;
}

#ifdef uek5
fbt:rds_rdma:rds_ib_send_cqe_handler:entry
#else
rawtp:*:*:rds_ib_send_cqe_handler
#endif
/
  (self->conn == 0) &&
  (arg2 != 0) &&
  (self->conn = (struct rds_connection*) arg2)
/
{
  /* Blank */
}

#ifdef uek5
fbt:rds_rdma:rds_ib_send_cqe_handler:return
#else
*:rds_rdma:poll_scq:return
#endif
{
  self->conn = 0;
}

fbt:rds:rds_message_put:entry
/
  (self->conn != 0) &&
  (arg0 != 0) &&
  (self->rm = (struct rds_message *) arg0) &&
  (self->inc = (struct rds_incoming *) &(self->rm->m_inc)) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0)
/
{
  this->conn = (struct rds_connection *) self->inc->i_conn;
  this->saddr_cmp = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
  this->daddr_cmp = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
  self->time_diff = (timestamp - pong_recv_inc[this->daddr_cmp, this->saddr_cmp, this->conn->c_tos, self->rds_hdr->h_dport, self->rds_hdr->h_sport])/NANO2USEC;
}

fbt:rds:rds_message_put:entry
/
  (self->conn != 0) &&
  (arg0 != 0) &&
  (self->rm = (struct rds_message *) arg0) &&
  (self->inc = (struct rds_incoming *) &(self->rm->m_inc)) &&
  (self->rds_hdr = ((struct rds_header *) &self->inc->i_hdr)) &&
  (self->rds_hdr->h_sport == 0) &&
  (self->rds_hdr->h_dport != 0) &&
  (self->rds_hdr->h_len == 0) &&
  (self->time_diff != 0) &&
  (self->time_diff >= min_lat)
/
{
    this->rm = (struct rds_message *) arg0;
    this->inc = (struct rds_incoming *) &this->rm->m_inc;
    this->rds_hdr = (struct rds_header *) &this->inc->i_hdr;
    this->cpath = (struct rds_conn_path *) this->inc->i_conn_path;
    this->conn = (struct rds_connection *) this->cpath->cp_conn;
    this->saddr = inet_ntoa(&this->conn->c_laddr.in6_u.u6_addr32[3]);
    this->daddr = inet_ntoa(&this->conn->c_faddr.in6_u.u6_addr32[3]);
    this->qos = this->conn->c_tos;
    this->sport = this->rds_hdr->h_sport;
    this->dport = this->rds_hdr->h_dport;

    pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] = timestamp;

#ifdef DEBUG
    printf("[%Y.%lu] DEBUG[rds_message_put] <%s,%s,%d> Pong sport=%d dport=%d conn=%p cp=%p inc=%p rm=%p rds_hdr=%p comm=%s pong_send_ts=%d pong_xmit_ts=%d pong_sendcomp_ts=%d pong_recv_inc_ts=%d\n",
           walltimestamp, timestamp, this->daddr, this->saddr, this->qos,
           this->dport, this->sport, this->conn, this->cpath, this->inc,
           this->rm, this->rds_hdr, execname,
           pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport],
           pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport],
           pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport],
           pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport]);
#endif

    pong_recvq_wt = (pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport] - pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport])/NANO2USEC;
    pong_sendq_wt = (pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport] - pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport])/NANO2USEC;
    pong_sendcomp_wt = (pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] - pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport])/NANO2USEC;
    pong_rds_wt = (pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] - pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport])/NANO2USEC;

    this->sep = ((this->qos >= 100)? "" : (this->qos >= 10)? " " : "  ");
    printf("[%Y] <%s,%s,%d> %s %4s %7d %12s %12s %12s %12s\n",
           walltimestamp, this->daddr, this->saddr, this->qos, this->sep, "Pong", this->dport,
           (pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport] && pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport])? lltostr(pong_sendq_wt) : "-1",
           (pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] && pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport])? lltostr(pong_sendcomp_wt) : "-1",
           (pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport] && pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport])? lltostr(pong_recvq_wt) : "-1",
           (pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] && pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport])? lltostr(pong_rds_wt) : "-1");

    pong_send[this->daddr, this->saddr, this->qos, this->dport, this->sport] = 0;
    pong_recv_inc[this->daddr, this->saddr, this->qos, this->dport, this->sport] = 0;
    pong_xmit[this->daddr, this->saddr, this->qos, this->dport, this->sport] = 0;
    pong_sendcomp[this->daddr, this->saddr, this->qos, this->dport, this->sport] = 0;
    self->conn = 0;
    self->rm = 0;
    self->inc = 0;
    self->rds_hdr = 0;
    self->time_diff = 0;
}

/* This entry works for ping and pong side. */
fbt:rds:rds_message_put:return
{
    self->conn = 0;
    self->rm = 0;
    self->inc = 0;
    self->rds_hdr = 0;
    self->time_diff = 0;
}

