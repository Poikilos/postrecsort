#!/usr/bin/env python

import sys
import os
import shutil

from tinytag import TinyTag
from tinytag import TinyTagException

from .find_hierosoft import hierosoft

from hierosoft.moremeta import (
    withExt,
    neatMetaTags,
)

# badPathChars = ["></\\:;\t|\n\r\"?"]
# ^ NOTE: Invalid characters on Windows also: ASCII indices 1-31 and \b
# replacementPathChars = [("\"", "in"), (":","-"), ("?",""),("\r",""),
#                         ("\n",""), ("/",","), ("\\",","), (":","-")]

def renameSongs(folderPath, relPath=""):
    for subName in os.listdir(folderPath):
        subPath = os.path.join(folderPath, subName)
        # catPath = folderPath
        subRelPath = subName
        if len(subName) > 0:
            subRelPath = os.path.join(relPath, subName)

        catMajorPath = os.path.join(folderPath, "Music")
        if os.path.isfile(subPath):
            # print(subPath)
            newPath = subPath
            ext = os.path.splitext(subPath)[1]
            if len(ext) > 1:
                ext = ext[1:]  # remove dot
            # lowerExt = ext.lower()
            # print('This track is by %s.' % tag.artist)
            # print("  " * depth + subPath + ": " + str(tag))
            newStats = neatMetaTags(subPath)
            newName = newStats.get('SuggestedFileName')
            # print("* " + artist + "/" + album + "/" + newName)
            if newName is not None:
                newPath = os.path.join(folderPath, newName)
            if (newPath is not None) and (subPath != newPath):
                newPath = os.path.join(folderPath, newName)
                tryNum = 0
                newNamePartial = os.path.splitext(newName)[0]
                while os.path.isfile(newPath):
                    tryNum += 1
                    newPath = os.path.join(folderPath, newNamePartial + " [" + str(tryNum) + "]")
                    newPath = withExt(newPath, ext)
                shutil.move(subPath, newPath)
                # print(newPath)
        else:
            renameSongs(subPath, relPath=subRelPath)


if __name__ == "__main__":
    renameSongs(sys.argv[1])
