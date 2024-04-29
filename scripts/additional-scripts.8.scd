additional-scripts(8)

# NAME

additional-scripts - Additional diagnostic scripts that are provided with Oracle Linux Enhanced Diagnostics (OLED).

# DESCRIPTION

This man page is to provide a brief description of the scripts provided with oled-tools.  These scripts are meant to be run using the *oled scripts* command.  For detailed information about each script please check out the documentation in the /usr/libexec/oled-tools/scripts/docs/ directory.

# CORE

- spinlock_time.d - Track 'the time interrupt is disabled' due to spin_lock_irq\*() kernel functions.  Takes an argument [holdtime in ms] and prints the process (and its call stack) which disables interrupt more than the given time.
	- ARGUMENTS: Time in ms (Minimum value is 2)

# NET

- arp_origin.d - This script detects and prints the details of all ARP requests, replies, and ignored packets on all the network interfaces present on the system where this script is being executed.


- cm_destroy_id.d - This dtrace script will probe for _cm_destroy_id_wait_timeout()_ and prints the cm_id, qp_num and pci_id of the associated QP.  Script will exit after 5 probes.  This script also calls mlxqpdump.sh.


- mlx_vhcaid.d - Prints 'vhca id' of the Mellanox devices (CX5) from a VM.


- mlxqpdump.sh - Used by cm_destroy_id.d.  Will collect firmware resource dumps and sysinfo-snapshots for Mellanox devices.


- ping_lat.d - This script provides latency details of the icmp packet, during its journey in the kernel. Output shows the time delta between two consecutive kernel functions through which the packet travels.


- rds_bcopy_metric.d - This script is used to trace and display the send/recv bytes per connection.


- rds_check_tx_stall.d - This script monitors the completions on all the connections and calculates the time difference between the consecutive completions. If this time difference exceeds the threshold time (in microseconds), given as input argument, message will be printed providing the details of the connection parameters.
	- ARGUMENTS: Threshold time in microseconds.  (Minimum: 500)


- rds_conn2irq.d - Display rds connection and its related qpn, cqn and ird lines.


- rds_egress_TP.d - Track egress drop reason along with pid and comm.


- rds_rdma_lat.d - Used to trace and display the rdma read/write in bytes and the corresponding latency (in usec) per connection.


- rds_rdma_xfer_rate.d - The script shows the rdma transfer rate[MB/s] for each rds connection.  It also shows histograms of inverse bandwidth in nsecs/KB [Avg number of nsecs to transfer 1KB of data].


- rds_tx_funccount.d - This script is used to trace and display rate of calls for send_xmit, ib_xmit and send_cqe_handler per 10 sec.

# IO

- nvme_io_comp.d - Measures nvme IO latency in microseconds (us).
	- ARGUMENTS: The sampling interval (in secs) for latency, the reporting period (in secs) for command completion.

- scsi_latency.d - Measures SCSI Mid Layer IO latency in milliseconds (ms) and to measure QLogic adapter layer IO latency in milliseconds(ms).

- scsi_queue.d - Measures SCSI IO queue time in milliseconds (ms).

# SEE ALSO

oled(8),
oled-scripts(8)
