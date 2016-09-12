#!/bin/bash

i=$1
echo "i:" $i

n=$#
echo "n:" $n

argv=$@
echo "argv:" $argv

argc=`expr $n - 1`
echo "argc:" $argc

all=${argv[@]}
echo "all:" $all

head=${argv[@]:0:1}
echo "head:" $head

head2=${argv[1]}
echo "head2:" $head2

next=${argv[@]:1}
echo "next:" $next
