#!/usr/bin/env python
import sys
import os
import shutil

from find_moreplatform import moreplatform

from moreplatform import moremeta

from moremeta import (
    modificationDate,
    metaBySize,
    minBannerRatio,
    isPhotoSize,
    isThumbnailSize,
    sortByExt,
)

if len(sys.argv) < 2:
    print("You must specify a directory.")
    exit(1)

sortByExt(sys.argv[1])
