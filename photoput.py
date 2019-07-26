#!/usr/bin/env python
# gets original date from EXIF information, and moves file to relative yyyy-MM-dd folder
# Author: Jake Gustafson (poikilos)
import sys

from moremeta import *

if len(sys.argv) < 2:
    print("You must specify a directory.")
    exit(1)

#process_files("/run/media/owner/sandisku32/DCIM/2017-10-29", 'move')
process_files(sys.argv[1], 'move')

print("unknown_type_count: " + str(results.get('unknown_type_count')))
print("missing_meta_count: " + str(results.get('missing_meta_count')))
print("processed_count: " + str(results.get('processed_count')))
