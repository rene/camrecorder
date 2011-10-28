#!/bin/sh

VDEVICE=$1

if [ -z "$VDEVICE" ]; then
	VDEVICE=/dev/video0
fi

./camrecorder.py -d $VDEVICE -a 10.1.1.2 -p 2180 -s rene -m live.ogg

