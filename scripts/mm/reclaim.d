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
 * Author: Imran Khan.
 * Purpose: This script summarizes memory reclaim(s) duration and results.
 * Prerequisites: Refer to the file reclaim_example.txt
 * Sample output: Refer to the file reclaim_example.txt
 */

/*
 * min_kernel 4.14.35-2042,5.4.17,5.15.0-200.103.1,6.12.0-0.0.1
 */


sdt:vmscan::mm_vmscan_direct_reclaim_begin
{
    self->direct_reclaim_start=timestamp;
    self->direct_nr_reclaimed = 0;
    self->anon_lru_reclaimed = 0;
    self->file_lru_reclaimed = 0;
    self->slab_reclaimed = 0;
    self->pruned_inode_reclaimed = 0;
    self->xfs_buf_reclaimed = 0;
}

sdt:vmscan::mm_vmscan_direct_reclaim_end
/self->direct_reclaim_start/
{
    self->direct_reclaim_duration_us = (timestamp - self->direct_reclaim_start) / 1000;	
    self->direct_nr_reclaimed = arg0;

    printf("%Y Direct reclaim summary: \n", walltimestamp);
    printf("    start time: %lu \n", self->direct_reclaim_start);
    printf("    end time: %lu \n", timestamp);
    printf("    duration (usecs): %lu \n", self->direct_reclaim_duration_us);
    printf("    reclaimed pages (total) : %d \n", self->direct_nr_reclaimed);
    printf("        file lru pages : %d \n", self->file_lru_reclaimed);
    printf("        anon lru pages : %d \n", self->anon_lru_reclaimed);
    printf("        slab pages : %d \n", self->slab_reclaimed);
    printf("        pruned inode pages : %d \n", self->pruned_inode_reclaimed);
    printf("        xfs buf pages : %d \n", self->xfs_buf_reclaimed);

    self->direct_reclaim_start = 0;
}

sdt:vmscan::mm_vmscan_node_reclaim_begin
{
    self->node_reclaim_node=-1;
    self->node_reclaim_start=timestamp;
    self->node_reclaim_node=arg0;
    self->node_nr_reclaimed = 0;
    self->anon_lru_reclaimed = 0;
    self->file_lru_reclaimed = 0;
    self->slab_reclaimed = 0;
    self->pruned_inode_reclaimed = 0;
    self->xfs_buf_reclaimed = 0;
}

sdt:vmscan::mm_vmscan_node_reclaim_end
/self->node_reclaim_start &&
 self->node_reclaim_node != -1/
{
    self->node_reclaim_duration_us = (timestamp - self->node_reclaim_start) / 1000;
    self->node_nr_reclaimed = arg0;

    printf("%Y Node reclaim (node: %d) summary: \n", walltimestamp, self->node_reclaim_node);
    printf("    start time: %lu \n", self->node_reclaim_start);
    printf("    end time: %lu \n", timestamp);
    printf("    duration (usecs): %lu \n", self->node_reclaim_duration_us);
    printf("    reclaimed pages (total) : %d \n", self->node_nr_reclaimed);
    printf("        file lru pages : %d \n", self->file_lru_reclaimed);
    printf("        anon lru pages : %d \n", self->anon_lru_reclaimed);
    printf("        slab pages : %d \n", self->slab_reclaimed);
    printf("        pruned inode pages : %d \n", self->pruned_inode_reclaimed);
    printf("        xfs buf pages : %d \n", self->xfs_buf_reclaimed);

    self->node_reclaim_start = 0;
    self->node_reclaim_node = -1;
}

fbt:vmlinux:balance_pgdat:entry
{
    self->indirect_reclaim_start=timestamp;
    self->indirect_nr_reclaimed = 0;
    self->anon_lru_reclaimed = 0;
    self->file_lru_reclaimed = 0;
    self->slab_reclaimed = 0;
    self->pruned_inode_reclaimed = 0;
    self->xfs_buf_reclaimed = 0;
}

fbt:vmlinux:balance_pgdat:return
/self->indirect_reclaim_start/
{
    self->indirect_reclaim_duration_us = (timestamp - self->indirect_reclaim_start) / 1000;	
    self->indirect_nr_reclaimed = self->file_lru_reclaimed + self->anon_lru_reclaimed +
				  self->slab_reclaimed + self->pruned_inode_reclaimed +
				  self->xfs_buf_reclaimed;

    printf("%Y Indirect reclaim summary: \n", walltimestamp);
    printf("    start time: %lu \n", self->indirect_reclaim_start);
    printf("    end time: %lu \n", timestamp);
    printf("    duration (usecs): %lu \n", self->indirect_reclaim_duration_us);
    printf("    reclaimed pages (total) : %d \n", self->indirect_nr_reclaimed);
    printf("        file lru pages : %d \n", self->file_lru_reclaimed);
    printf("        anon lru pages : %d \n", self->anon_lru_reclaimed);
    printf("        slab pages : %d \n", self->slab_reclaimed);
    printf("        pruned inode pages : %d \n", self->pruned_inode_reclaimed);
    printf("        xfs buf pages : %d \n", self->xfs_buf_reclaimed);

    self->indirect_reclaim_start = 0;
}


sdt:vmscan::mm_vmscan_memcg_reclaim_begin
{
    self->memcg_reclaim_start=timestamp;
    self->memcg_nr_reclaimed = 0;
    self->anon_lru_reclaimed = 0;
    self->file_lru_reclaimed = 0;
    self->slab_reclaimed = 0;
    self->pruned_inode_reclaimed = 0;
    self->xfs_buf_reclaimed = 0;
}

sdt:vmscan::mm_vmscan_memcg_reclaim_end
/self->memcg_reclaim_start/
{
    self->memcg_reclaim_duration_us = (timestamp - self->memcg_reclaim_start) / 1000;	
    self->memcg_nr_reclaimed = arg0;
    
    printf("%Y Memcg reclaim summary: \n", walltimestamp);
    printf("    start time: %lu \n", self->memcg_reclaim_start);
    printf("    end time: %lu \n", timestamp);
    printf("    duration (usecs): %lu \n", self->memcg_reclaim_duration_us);
    printf("    reclaimed pages (total) : %d \n", self->memcg_nr_reclaimed);
    printf("        file lru pages : %d \n", self->file_lru_reclaimed);
    printf("        anon lru pages : %d \n", self->anon_lru_reclaimed);
    printf("        slab pages : %d \n", self->slab_reclaimed);
    printf("        pruned inode pages : %d \n", self->pruned_inode_reclaimed);
    printf("        xfs buf pages : %d \n", self->xfs_buf_reclaimed);
    self->memcg_reclaim_start = 0;
}

sdt:vmscan::mm_vmscan_memcg_softlimit_reclaim_begin
{
    self->memcg_softlimit_reclaim_start=timestamp;
}

sdt:vmscan::mm_vmscan_memcg_softlimit_reclaim_end
/self->memcg_softlimit_reclaim_start/
{
    self->memcg_softlimit_reclaim_duration_us = (timestamp - self->memcg_softlimit_reclaim_start) / 1000;	
    printf("%Y  memcg softlimit reclaim ran for %lu microsecs between %lu and %lu \n", walltimestamp, self->memcg_softlimit_reclaim_duration_us,
		    self->memcg_softlimit_reclaim_start, timestamp);
    self->memcg_softlimit_reclaim_start = 0;
}

sdt:vmscan::mm_shrink_slab_start
/curthread->reclaim_state/
{
#ifdef uek8
    self->reclaimed_slab_start = curthread->reclaim_state->reclaimed;
#else
    self->reclaimed_slab_start = curthread->reclaim_state->reclaimed_slab;
#endif
}

sdt:vmscan::mm_shrink_slab_end
/curthread->reclaim_state/
{
#ifdef uek8
    self->reclaimed_slab_end = curthread->reclaim_state->reclaimed;
#else
    self->reclaimed_slab_end = curthread->reclaim_state->reclaimed_slab;
#endif
    self->slab_reclaimed += self->reclaimed_slab_end - self->reclaimed_slab_start;
}

fbt:vmlinux:inode_lru_isolate:entry
/curthread->reclaim_state/
{
#ifdef uek8
    self->pruned_inode_start = curthread->reclaim_state->reclaimed;
#else
    self->pruned_inode_start = curthread->reclaim_state->reclaimed_slab;
#endif
}

fbt:vmlinux:inode_lru_isolate:return
/curthread->reclaim_state/
{
#ifdef uek8
    self->pruned_inode_end = curthread->reclaim_state->reclaimed;
#else
    self->pruned_inode_end = curthread->reclaim_state->reclaimed_slab;
#endif
    self->pruned_inode_reclaimed += self->pruned_inode_end - self->pruned_inode_start;
}

fbt:xfs:xfs_buf_free_pages:entry
/curthread->reclaim_state/
{
#ifdef uek8
    self->xfs_buf_start = curthread->reclaim_state->reclaimed;
#else
    self->xfs_buf_start = curthread->reclaim_state->reclaimed_slab;
#endif
}

fbt:xfs:xfs_buf_free_pages:return
/curthread->reclaim_state/
{
#ifdef uek8
    self->xfs_buf_end = curthread->reclaim_state->reclaimed;
#else
    self->xfs_buf_end = curthread->reclaim_state->reclaimed_slab;
#endif
    self->xfs_buf_reclaimed += self->xfs_buf_end - self->xfs_buf_start;
}


fbt:vmlinux:shrink_inactive_list:entry
{
    self->inactive_lru = arg3;
}

fbt:vmlinux:shrink_inactive_list:return
{
    self->inactive_lru = -1;
}
/*RECLAIM_WB_ANON*/
sdt:vmscan::mm_vmscan_lru_shrink_inactive
/self->inactive_lru == 0/
{
    self->anon_lru_reclaimed += arg2;
}

/*RECLAIM_WB_FILE*/
sdt:vmscan::mm_vmscan_lru_shrink_inactive
/self->inactive_lru == 2/
{
    self->file_lru_reclaimed += arg2;
}
