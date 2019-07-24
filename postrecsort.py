#!/usr/bin/env python

import sys
import os
import shutil
import struct
# import md5

try:
    from PIL import Image
except ImportError:
    print("This program requires PIL such as from the python-pil package")

from tinytag import TinyTag
from tinytag import TinyTagException

def usage():
    print(sys.argv[0] + " <photorec result directory with recup_dir.*> <profile>")

def withExt(namePart, ext=None):
    ret = namePart
    if (ext is not None) and (len(ext) > 0):
         ret += "." + ext
    return ret


def decodeAny(unicode_or_str):
    # see https://stackoverflow.com/a/19877309/4541104
    text = None
    if unicode_or_str is not None:
        if isinstance(unicode_or_str, str):
            text = unicode_or_str
            decoded = False
        else:
            text = unicode_or_str.decode('ascii')
            decoded = True
        # text = text.rstrip('\x00')
        text = text.replace('\x00','')  # overkill (rstrip is ok)
    return text

def customDie(msg):
    usage()
    print("")
    if msg is not None:
        print("ERROR:")
        print(msg)
        print("")
    exit(1)

if len(sys.argv) < 3:
    customDie("There must be two parameters.")

enableShowLarge = False
largeSize = 1024000

catDirNames = {}

# region make configurable
enableNoExtIgnore = True  # if NO extension, ignore
ignoreMoreExts = ["zip", "gz", "html", "htm", "mmw", "php"]
knownThumbnailSizes = [(160,120), (160,120), (200,200), (264,318), (218,145), (100,100), (158,158), (53,53)]
# 170x330 is hp setup image
minNonThumnailPixels = 150 * 199 + 1
# for knownThumbnailSize in knownThumbnailSizes:
    # pixCount = knownThumbnailSize[0] * knownThumbnailSize[1]
    # if pixCount + 1 > minNonThumnailPixels:
        # minNonThumnailPixels = pixCount + 1
clearRatioMax = 0.9
# endregion make configurable


ignoreExts = [ "ani", "api", "asp", "ax", "bat", "cnv", "cp_", "cpl",
               "class", "dat", "db", "dll", "cab", "chm", "edb", "elf", "emf", "exe", "f",
               "h", "icc", "ime", "ini", "jar", "java", "js", "jsp", "lib", "loc",
               "mui", "ocx", "olb", "reg", "rll", "sam", "scr", "sports", "sqm", "swc", "sys",
               "sys_place_holder_for_2k_and_xp_(see_pxhelp)",
               "tlb", "ttf", "vdm", "woff", "xml"]
for thisExt in ignoreMoreExts:
    ignoreExts.append(thisExt)
ignore = ["user"]
categories = {}
categories["Backup"] = ["7z", "accdb", "dbx", "idx", "mbox", "mdb", "pst", "sqlite", "tar", "wab", "zip"]
categories["Documents"] = ["ai", "csv", "doc", "docx", "mpp", "pdf", "ppt", "pptx", "ps", "rtf", "wpd", "wps", "xls", "xlsx", "xlr"]
categories["PlainText"] = ["txt"]
categories["Downloads"] = ["bin", "cue", "iso"]
categories["Torrents"] = ["torrent"]
categories["eBooks"] = ["prc", "lit"]
categories["Links"] = ["url", "website"]
categories["Meshes"] = ["x3d"]
categories["Music"] = ["ape", "flac", "m4a", "mid", "mp3", "ogg", "wav", "wma"]
categories["Pictures"] = ["bmp", "gif", "ico", "jpe", "jpeg", "jpg", "png", "psd", "svg", "wmf"]
categories["Playlists"] = ["asx", "bpl", "feed", "itpc", "m3u", "m3u8", "opml", "pcast", "pls", "podcast", "rm", "rmj","rmm", "rmx", "rp", "smi", "smil", "upf", "vlc", "wpl", "xspf", "zpl"]
categories["Shortcuts"] = ["lnk"]
categories["Videos"] = ["asf", "avi", "mp2", "mp4", "mpe", "mpeg", "mpg", "mov", "swf", "wmv", "webm", "wm"]
validMinFileSizes = {}
validMinFileSizes["Videos"] = 4096
validMinFileSizes["Music"] = 1024000
validMinFileTypeSizes = {}
validMinFileTypeSizes["flac"] = 3072000
unknownTypes = []
unknownPathExamples = []
foundTypeCounts = {}
foundMaximums = {}
foundMaximumPaths = {}
extDesc = {}
extDesc['mmw'] = "AceMoney Money File, MechCAD Software LLC financial file, or misnamed dangerous executable"
extDesc['mpp'] = "Microsoft Project"
extDesc['mui'] = "MultiLanguage Windows Resource"
extDesc['olb'] = "Microsoft Office Library"
extDesc['rll'] = "Microsoft Windows Resource"
extDesc['swc'] = "Precompiled Flash and ActionScript Code"
extDesc['tlb'] = "OLE Library"
extDesc['wpd'] = "Corel WordPerfect Document"
extDesc['woff'] = "Web Open Font Format"
extDesc['wpl'] = "Windows Media Player Playlist"
extDesc['wps'] = "Microsoft Works (or Kingsoft Writer) Document"
extDesc['xlr'] = "Microsoft Works Spreadsheet or Chart"

foundTypeCounts = {}


catDirNames["Backup"] = "Backup"
catDirNames["Documents"] = "Documents"
catDirNames["eBooks"] = os.path.join(catDirNames["Documents"], "eBooks")
catDirNames["Downloads"] = "Downloads"
catDirNames["Links"] = "Favorites"
catDirNames["Meshes"] = "Meshes"
catDirNames["Music"] = "Music"
catDirNames["Pictures"] = "Pictures"
catDirNames["PlainText"] = os.path.join(catDirNames["Documents"], "plaintext")
catDirNames["Playlists"] = "Music"
catDirNames["Shortcuts"] = "Shortcuts"
catDirNames["Torrents"] = os.path.join(catDirNames["Downloads"], "torrents")
catDirNames["Videos"] = "Videos"
badPathChars = ["></\\:;\t|\n\r\""]   # invalid characters on Windows
                                      # also include 1-31 and \b

go = True

uniqueCheckExt = []

def sortedBySize(parent, subs):
    pairs = []
    for sub in subs:
        path = os.path.join(parent, sub)
        size = os.path.getsize(path)
        pairs.append((size, sub))
    pairs.sort(key=lambda s: s[0])
    ret = []
    for size, sub in pairs:
        ret.append(sub)
    return ret

def removeBlank(preRecoveredPath, profilePath, relPath="", depth=0):
    backupPath = os.path.join(profilePath, "Backup")
    folderPath = preRecoveredPath
    print("# checking for blanks in: " + folderPath)
    imPrev = None

    for subName in sortedBySize(folderPath, os.listdir(folderPath)):
        subPath = os.path.join(folderPath, subName)
        subRelPath = subName
        # catMajorPath = None
        # catPath = None
        if len(subName) > 0:
            subRelPath = os.path.join(relPath, subName)
        if os.path.isfile(subPath):
            ext = os.path.splitext(subPath)[1]
            if len(ext) > 1:
                ext = ext[1:]
            lowerExt = ext.lower()
            enableIgnore = False
            isBlank = False
            isDup = False
            fileSize = os.path.getsize(subPath)
            if lowerExt in categories["Pictures"]:
                # print("# checking if blank: " + subPath)
                try:
                    im = Image.open(subPath)
                    width, height = im.size
                    pixCount = width * height
                    rgbIm = im.convert('RGBA')
                    # convert, otherwise GIF will yield single value
                    lastColor = None
                    isBlank = True
                    clearCount = 0
                    print("# checking pixels in " + '{0:.2g}'.format(fileSize/1024/1024) + " MB '" + subPath + "'...")
                    for y in range(height):
                        for x in range(width):
                            thisColor = rgbIm.getpixel((x, y))
                            if thisColor[3] == 0:
                                thisColor = (0, 0, 0, 0)
                            if thisColor[3] < 128:
                                clearCount += 1
                            if (lastColor is not None) and (lastColor != thisColor):
                                isBlank = False
                                break
                            lastColor = thisColor
                    if (float(clearCount) / float(pixCount)) > clearRatioMax:
                        isBlank = True
                    if not isBlank:
                        #try:
                        if imPrev is not None:
                            prevW, prevH = imPrev.size
                            if imPrev.size == im.size:
                                isDup = True
                                # print("# comparing pixels in '" + subPath + "'...")
                                for y in range(height):
                                    for x in range(width):
                                        if rgbIm.getpixel((x, y)) != imPrev.getpixel((x, y)):
                                            isDup = False
                                            break
                            imPrev.close()
                        # except:
                            # isDup = False
                    imPrev = rgbIm
                except OSError:
                    # isBlank = True
                    # such as "Unsupported BMP header type (0)"
                    # but it could be an SVG, PSD, or other good file!
                    pass
                try:
                    if im is not None:
                        im.close()
                except:
                    pass
            elif lowerExt in categories["Music"]:
                validMinFileSize = validMinFileSizes.get("Music")
                if validMinFileSize is not None:
                    if fileSize < validMinFileSize:
                        isBlank = True
                validMinFileTypeSize = validMinFileTypeSizes.get(lowerExt)
                if validMinFileTypeSize is not None:
                    if fileSize < validMinFileTypeSize:
                        isBlank = True
            # else:
                # if lowerExt not in uniqueCheckExt:
                    # print("# not checking if blank: " + subPath)
                    # uniqueCheckExt.append(lowerExt)
            newName = subName
            for c in badPathChars:
                newName = newName.replace(c, "_")
            if isBlank:
                newParentPath = os.path.join(backupPath, "blank")
                newPath = os.path.join(newParentPath, newName)
                if not os.path.isdir(newParentPath):
                    os.makedirs(newParentPath)
                shutil.move(subPath, newPath)
            elif isDup:
                newParentPath = os.path.join(backupPath, "duplicates")
                newPath = os.path.join(newParentPath, newName)
                # if not os.path.isdir(newParentPath):
                    # os.makedirs(newParentPath)
                # shutil.move(subPath, newPath)
                os.remove(subPath)
            elif newName != subName:
                newParentPath = folderPath
                newPath = os.path.join(newParentPath, newName)
                # if not os.path.isdir(newParentPath):
                    # os.makedirs(newParentPath)
                shutil.move(subPath, newPath)
        else:
            doneNames = ["blank", "duplicates", "thumbnails", "unusable"]
            if subName not in doneNames:
                removeBlank(subPath, profilePath, relPath=subRelPath, depth=depth+1)


def sortFiles(preRecoveredPath, profilePath, relPath="", depth=0):
    global catDirNames
    if os.path.isdir(preRecoveredPath):
        folderPath = preRecoveredPath
        for subName in os.listdir(folderPath):
            dstFilePath = None
            subPath = os.path.join(folderPath, subName)
            subRelPath = subName
            catMajorPath = None
            catPath = None
            if len(subName) > 0:
                subRelPath = os.path.join(relPath, subName)
            if os.path.isfile(subPath):
                enableIgnore = False
                if subName in ignore:
                    enableIgnore = True
                newName = subName
                ext = os.path.splitext(subPath)[1]
                if len(ext) > 1:
                    ext = ext[1:]
                lowerExt = ext.lower()
                if len(lowerExt) == 0:
                    if enableNoExtIgnore:
                        enableIgnore = True
                if lowerExt in ignoreExts:
                    enableIgnore = True
                if enableIgnore:
                    continue
                category = None
                fileSize = os.path.getsize(subPath)
                for k, v in categories.items():
                    # print("checking if " + str(v) + "in" + str(catDirNames))
                    if lowerExt in v:
                        category = k
                if category is None:
                    category = "Backup"
                    if lowerExt not in unknownTypes:
                        unknownTypes.append(lowerExt)
                        unknownPathExamples.append(subPath)
                    # continue
                    catMajorPath = os.path.join(profilePath, catDirNames[category])
                    catMajorPath = os.path.join(catMajorPath, "unknown")
                else:
                    catMajorPath = os.path.join(profilePath, catDirNames[category])
                if category == "Music":
                    try:
                        tag = TinyTag.get(subPath)
                        # print('This track is by %s.' % tag.artist)
                        # print("  " * depth + subPath + ": " + str(tag))
                        artist = tag.__dict__.get('albumartist')
                        album = tag.__dict__.get('album')
                        title = tag.__dict__.get('title')
                        track = tag.__dict__.get('track')
                        catPath = catMajorPath
                        if artist is None:
                            songartist = tag.__dict__.get('artist')
                            if songartist is not None:
                                artist = decodeAny(songartist)
                            else:
                                artist = "unknown"
                            # category = None
                        else:
                            artist = decodeAny(artist)
                            # artist = unicode(artist, "utf-8")
                        album = decodeAny(album)
                        title = decodeAny(album)
                        track = decodeAny(album)
                        if len(artist) == 0:
                            artist = "unknown"
                        if album is None:
                            album = "unknown"
                            # category = None
                        else:
                            album = decodeAny(album)
                        if len(album) == 0:
                            artist = "album"
                        if title is not None:
                            catPath = os.path.join(
                                os.path.join(catMajorPath, artist),
                                album
                            )
                        else:
                            catPath = os.path.join(catMajorPath, "misc")
                        if track is not None:
                            track = str(track)
                        if title is not None:
                            if track is not None:
                                newName = withExt(track + " " + title, ext)
                            else:
                                newName = withExt(title, ext)
                        elif track is not None:
                            newName = track + " " + subName
                    except KeyboardInterrupt:
                        go = False
                        break
                    except TinyTagException:
                        print("  " * depth + "No tags: " + lowerExt)
                        catPath = os.path.join(catMajorPath, "misc")
                    except struct.error:
                        # such as "unpack requires a buffer of 34 bytes"
                        # during TinyTag.get(path)
                        print("  " * depth + "No tags: " + lowerExt)
                        catPath = os.path.join(catMajorPath, "misc")

                elif category == "Pictures":
                    try:
                        im = Image.open(subPath)
                        width, height = im.size
                        im.close()
                        if ((width*height < minNonThumnailPixels)
                                or ((width, height) in knownThumbnailSizes)):
                            catPath = os.path.join(catMajorPath, "thumbnails")
                        else:
                            catPath = catMajorPath
                    except OSError:
                        # such as "Unsupported BMP header type (0)"
                        catPath = os.path.join(catMajorPath, "unusable")
                else:
                    catPath = catMajorPath
                    validMinFileSize = validMinFileSizes.get(category)
                    if validMinFileSize is not None:
                        if fileSize < validMinFileSize:
                            catPath = os.path.join(catMajorPath, "thumbnails")
                # if category == "Music":
                    # if lowerExt == "wma":
                # print("ensuring dir: " + catPath)
                if not os.path.isdir(catPath):
                    os.makedirs(catPath)
                dstFilePath = os.path.join(catPath, newName)
                tryNum = 0
                newNamePartial = os.path.splitext(newName)[0]
                print("# moving to '" + dstFilePath + "'")
                while os.path.isfile(dstFilePath):
                    tryNum += 1
                    dstFilePath = os.path.join(catPath, newNamePartial + " [" + str(tryNum) + "]")
                    dstFilePath = withExt(dstFilePath, ext)
                shutil.move(subPath, dstFilePath)
                print("mv '" + dstFilePath+ "' '" + dstFilePath + "'")

                if enableShowLarge:
                    if fileSize > largeSize:
                        print('{0:.3g}'.format(fileSize/1024/1024) + "MB: " + dstFilePath)
                        # g removes insignificant zeros
                if (category not in foundMaximums) or (fileSize > foundMaximums[category]):
                    foundMaximums[category] = fileSize
                    foundMaximumPaths[category] = dstFilePath
                if lowerExt not in foundTypeCounts.keys():
                    foundTypeCounts[lowerExt] = 1
                else:
                    foundTypeCounts[lowerExt] += 1
                if category is None:
                    print("  " * depth + "unknown type: " + lowerExt + " for '" + subPath + "'")
                # print("  " * depth + "[" + str(category) + "]" + dstFilePath)
            elif os.path.isdir(subPath):
                # print(" " * depth + subName)
                # if subName[:1] != ".":
                sortFiles(subPath, profilePath, depth=depth+1)
    else:
        customDie(preRecoveredPath + " is not a directory")


# print(sys.argv[1])
sortFiles(sys.argv[1], sys.argv[2])

removeBlank(sys.argv[2], sys.argv[2])  # same arg for both

print("Maximums:")
for k, v in foundMaximums.items():
    print("  Largest in " + k + ":" + '{0:.3g}'.format(v/1024/1024) + " MB): " + foundMaximumPaths[k])
print("unknownTypes: " + str(unknownTypes))
print("unknownPathExamples:")
for s in unknownPathExamples:
    print("  - " + s)
if not go:
    print("Cancelled.")
else:
    print("Done.")
