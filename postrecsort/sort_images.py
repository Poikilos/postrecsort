#!/usr/bin/env python

import sys
import os
import shutil
import struct

# import PIL.Image
try:
    from PIL import Image
except ImportError:
    print("This program requires PIL such as from the python-pil package")

import PIL.ExifTags

from .find_hierosoft import hierosoft

from hierosoft.moremeta import (
    modificationDate,
    metaBySize,
    minBannerRatio,
    isPhotoSize,
    isThumbnailSize,
)

if len(sys.argv) < 2:
    print("You must specify a directory.")
    exit(1)

def pushYearUsingModTime(folderPath, recurse=True):
    if os.path.isdir(folderPath):
        subs = os.listdir(folderPath)
        subIndex = -1
        interval = len(subs) / 100
        if interval < 0:
            interval = 1
        progressChunkCount = -1
        for subName in subs:
            subIndex += 1
            progressChunkCount += 1
            newPath = None
            catPath = folderPath
            subCatName = None
            subPath = os.path.join(folderPath, subName)
            parentName = os.path.basename(folderPath)
            if progressChunkCount >= interval:
                print("# " + parentName + " " + str(int(round(float(subIndex)/float(len(subs))*100.0))) + "%")
                progressChunkCount = -1
            if os.path.isfile(subPath):
                ext = os.path.splitext(subPath)[1]
                if len(ext) > 1:
                    ext = ext[1:]  # remove dot
                lowerExt = ext.lower()
                dt = modificationDate(subPath)
                year = dt.strftime("%Y")
                ratio = None
                imSize = None
                dMeta = None
                try:
                    im = Image.open(subPath)
                    imSize = im.size
                    width, height = imSize
                    ratio = float(width) / float(height)
                    invRatio = float(height) / float(width)
                    isPhoto = False
                    if isPhotoSize(im.size):
                        isPhoto = True
                    if isPhoto and (year is not None):
                        subCatName = year
                    dMeta = metaBySize(im.size)
                    im.close()
                except OSError:
                    # may be svg or other non-raster or non-image
                    # print("# no meta: '" + subPath + "'")
                    pass
                if lowerExt == "psd":
                    subCatName = "projects"
                enableRemove = False
                if dMeta is not None:
                    enableRemove = dMeta['disposable']
                    subCatName = dMeta['category']
                elif ratio is not None:
                    if (ratio >= minBannerRatio) \
                            or (invRatio >= minBannerRatio):
                        subCatName = 'banners'
                if (imSize is not None) and (subCatName != 'banner'):
                    if isThumbnailSize(imSize):
                        subCatName = 'thumbnails'

                if enableRemove:
                    print("rm '" + subPath + "'")
                    os.remove(subPath)
                    continue
                if (subCatName is not None) and (subCatName != parentName):
                    catPath = os.path.join(folderPath, subCatName)
                newPath = os.path.join(catPath, subName)
                if subPath != newPath:
                    print("mv '" + subPath + "' '" + newPath + "'")
                    if not os.path.isdir(catPath):
                        os.makedirs(catPath)
                    shutil.move(subPath, newPath)
            else:
                if recurse:
                    pushYearUsingModTime(subPath, recurse=recurse)


if __name__ == "__main__":
    # process_files("/run/media/owner/sandisku32/DCIM/2017-10-29", 'move')
    pushYearUsingModTime(sys.argv[1])
