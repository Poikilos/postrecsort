#!/usr/bin/env python
import sys
import os
import shutil

from .find_hierosoft import hierosoft

from hierosoft.moremeta import (
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
