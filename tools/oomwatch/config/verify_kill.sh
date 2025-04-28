#!/bin/bash

# Sample verification script that echoes arguments and exits 0
pid="$1"
pname="$2"
rss_bytes="$3"

echo "called with PID: $pid name: $pname RSS: $rss_bytes"

#if [ "$rss_bytes" -lt 1073741824 ]; then
#        echo "$rss_bytes less than 1G - not killing"
#        exit 1
#fi

exit 0
