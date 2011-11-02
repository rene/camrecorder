#!/bin/sh

VIDEOPATH=.

# Keep files from the last five days ago
# (each day will have 24 files, 1 per hour)
KEEP_NFILES=120

# Sort files by modification date
ORDFILES=$(ls -l --full-time $VIDEOPATH/*.ogg | awk '{ print $6, $7, $9 }' | sort -n | cut -d" " -f3)

# Count files
OLDIFS=$IFS
IFS=" "
NFILES=$(echo $ORDFILES | wc -l)
IFS=$OLDIFS

# Check if there is a file to remove
if [ $NFILES -le $KEEP_NFILES ]; then
	exit 0
fi

# Remove older files
NREMOVE=$(($NFILES - $KEEP_NFILES))
IFS=" "
REMLIST=$(echo $ORDFILES | head -n $NREMOVE)
IFS=$OLDIFS

if [ -n "$REMLIST" ]; then
	rm $REMLIST
fi

