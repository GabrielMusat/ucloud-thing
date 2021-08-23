#!/usr/bin/env bash

if [[ "$EUID" -ne 0 ]]
  then echo "Please run as root"
  exit
fi

fdisk -l

echo "type de disk1 you want to clone"
read device
echo "ok, now select the output size to clone in Mb (last time minimum was 3500)"
read size

dd if=/dev/$device of=ucloud.img bs=1M count=$size status=progress