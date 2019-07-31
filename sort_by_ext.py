#!/usr/bin/env python
import sys
import os
import shutil

from moremeta import modificationDate
from moremeta import metaBySize
from moremeta import minBannerRatio
from moremeta import isPhotoSize
from moremeta import isThumbnailSize
from moremeta import sortByExt

if len(sys.argv) < 2:
    print("You must specify a directory.")
    exit(1)

sortByExt(sys.argv[1])
