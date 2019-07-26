#!/usr/bin/env python

import sys
import os
import shutil
import struct
import filecmp
# import md5

try:
    from PIL import Image
except ImportError:
    print("This program requires PIL such as from the python-pil package")

from tinytag import TinyTag
from tinytag import TinyTagException

from moremeta import isThumbnailSize

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
        elif isinstance(unicode_or_str, int):
            text = str(unicode_or_str)
            decoded = False
        elif isinstance(unicode_or_str, float):
            text = str(unicode_or_str)
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


enableShowLarge = False
largeSize = 1024000
maxComparisonSize = 2 * 1024 * 1024

catDirNames = {}

from moremeta import knownThumbnailSizes

# region make configurable
enableNoExtIgnore = True  # if NO extension, ignore
ignoreMoreExts = ["zip", "gz", "html", "htm", "mmw", "php"]
# for more info see derivedMetas

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
validMinFileSizes["Videos"] = 1 * 1024 * 1024
validMinFileSizes["Music"] = 400 * 1024
normalMinFileSizes = {}
normalMinFileSizes["Videos"] = 15 * 1024 * 1024
validMinFileTypeSizes = {}
# validMinFileTypeSizes["flac"] = 3072000
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
badPathChars = ["></\\:;\t|\n\r\"?"]   # NOTE: Invalid characters on
                                       # Windows also include 1-31 & \b
replacementPathChars = [("\"", "in"), (":","-"), ("?",""),("\r",""), ("\n",""), ("/",","), ("\\",","), (":","-")]

# Do not recurse into doneNames
doneNames = ["blank", "duplicates", "thumbnails", "unusable"]

go = True

uniqueCheckExt = []

def replaceAnyChar(s, characters, newStr="_"):
    ret = s
    if ret is not None:
        for c in characters:
            ret = ret.replace(c, newStr)
    return ret

def replaceMany(s, tuples):
    ret = s
    if ret is not None:
        for t in tuples:
            ret = ret.replace(t[0], t[1])
    return ret

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

def removeExtra(folderPath, profilePath, relPath="", depth=0):
    backupPath = os.path.join(profilePath, "Backup")
    print("# checking for blanks in: " + folderPath)
    prevIm = None
    prevSize = None
    prevDestPath = None

    for subName in sortedBySize(folderPath, os.listdir(folderPath)):
        subPath = os.path.join(folderPath, subName)
        subRelPath = subName
        if len(subName) > 0:
            subRelPath = os.path.join(relPath, subName)
        if os.path.isfile(subPath):
            ext = os.path.splitext(subPath)[1]
            if len(ext) > 1:
                ext = ext[1:]  # remove dot
            lowerExt = ext.lower()
            enableIgnore = False
            newName = subName
            newParentPath = folderPath
            newPath = subPath
            isBlank = False
            subCatName = None
            isDup = False
            fileSize = os.path.getsize(subPath)
            category = None
            for k, v in categories.items():
                # print("checking if " + str(v) + "in" + str(catDirNames))
                if lowerExt in v:
                    category = k

            if category == "Pictures":
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
                        if prevIm is not None:
                            prevW, prevH = prevIm.size
                            if prevIm.size == im.size:
                                isDup = True
                                # print("# comparing pixels in '" + subPath + "'...")
                                for y in range(height):
                                    for x in range(width):
                                        if rgbIm.getpixel((x, y)) != prevIm.getpixel((x, y)):
                                            isDup = False
                                            break
                            prevIm.close()
                        # except:
                            # isDup = False
                    prevIm = rgbIm
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
            else:
                validMinFileSize = validMinFileSizes.get(category)
                normalMinFileSize = normalMinFileSizes.get(category)
                if validMinFileSize is not None:
                    if fileSize < validMinFileSize:
                        isBlank = True
                if normalMinFileSize is not None:
                    if fileSize < normalMinFileSize:
                        subCatName = "small"
                if (prevSize is not None) and (fileSize == prevSize) \
                        and (fileSize <= maxComparisonSize) \
                        and (prevDestPath is not None):
                    print("# comparing bytes to " + '{0:.2g}'.format(fileSize/1024/1024) + " MB '" + prevDestPath + "'...")
                    if (filecmp.cmp(prevDestPath, subPath)):
                        isDup = True
            # else:
                # if lowerExt not in uniqueCheckExt:
                    # print("# not checking if blank: " + subPath)
                    # uniqueCheckExt.append(lowerExt)
            newName = replaceMany(newName, replacementPathChars)
            newName = replaceAnyChar(newName, badPathChars, newStr="_")

            if isDup:
                os.remove(subPath)  # do not set previous if removing
                continue

            if isBlank:
                newParentPath = os.path.join(backupPath, "blank")
            elif subCatName is not None:
                newParentPath = os.path.join(newParentPath, subCatName)

            newPath = os.path.join(newParentPath, newName)

            if newPath != subPath:
                if not os.path.isdir(newParentPath):
                    os.makedirs(newParentPath)
                shutil.move(subPath, newPath)
            prevSize = fileSize
            prevDestPath = newPath
        else:
            if subName not in doneNames:
                removeExtra(subPath, profilePath, relPath=subRelPath, depth=depth+1)

artists = []
albums = []

def startsWithThe(s):
    if s is None:
        return False
    return (len(s) >= 4) and (s.lower()[0:4] == "the ")

def getWithThe(s):
    ret = s
    if ret is not None:
        if not startsWithThe(s):
            ret = "The " + s
    return ret

def getWithoutThe(s):
    ret = s
    if ret is not None:
        if startsWithThe(s):
            ret = s[4:]
    return ret

def getTitleQuality(title):
    ret = -1
    if title is not None:
        ret = 0
        if startsWithThe(title):
            ret += 4
        for c in title:
            if c == c.upper():
                ret += 1
    return ret


def getSimilar(needle, haystack):
    ret = None
    if needle is not None:
        needleQuality = getTitleQuality(needle)
        needleL = needle.lower()
        theNeedle = getWithThe(needle)
        theNeedleL = theNeedle.lower()
        retQuality = None
        for s in haystack:
            quality = getTitleQuality(s)
            theS = getWithThe(s)
            theSL = theS.lower()
            sL = s.lower()
            # if (theSL == needleL) or (theSL == theNeedleL) \
                    # or (sL == needleL) or (sL == theNeedleL):
            if (sL == needleL) or (sL == theNeedleL):
                if (retQuality is None) or (quality > retQuality):
                    retQuality = quality
                    ret = s
    return ret


def getAndCollectSimilarArtist(name):
    ret = getSimilar(name, artists)
    if name is not None:
        if name not in artists:
            artists.append(name)
    if ret is None:
        ret = name

def getAndCollectSimilarAlbum(name):
    ret = getSimilar(name, albums)
    if name is not None:
        if name not in albums:
            albums.append(name)
    if ret is None:
        ret = name
    return ret

# Usage:
# tag = TinyTag.get(subPath)
# filenName = fileNameFromStats(tag.__dict__)
def getMeta(path):
    ret = {}
    album = None
    artist = None
    title = None
    track = None
    newName = None

    if not os.path.isfile(path):
        raise RuntimeError("not a file: " + str(path))
    try:
        newName = os.path.basename(path)
        ext = os.path.splitext(path)[1]
        if len(ext) > 1:
            ext = ext[1:]  # remove dot
        lowerExt = ext.lower()
        tag = TinyTag.get(path)
        artist = tag.__dict__.get('albumartist')
        album = tag.__dict__.get('album')
        title = tag.__dict__.get('title')
        track = tag.__dict__.get('track')
        disc = tag.__dict__.get('disc')
        if artist is None:
            songArtist = tag.__dict__.get('artist')
            if songArtist is not None:
                artist = decodeAny(songArtist)
            else:
                artist = "unknown"
            # category = None
        else:
            artist = decodeAny(artist)
            # artist = unicode(artist, "utf-8")
        album = decodeAny(album)
        title = decodeAny(title)
        track = decodeAny(track)
        disc = decodeAny(disc)

        artist = replaceMany(artist, replacementPathChars)
        album = replaceMany(album, replacementPathChars)
        title = replaceMany(title, replacementPathChars)

        artist = replaceAnyChar(artist, badPathChars, newStr="_")
        album = replaceAnyChar(album, badPathChars, newStr="_")
        title = replaceAnyChar(title, badPathChars, newStr="_")

        if artist is not None:
            artist = artist.strip()
        if album is not None:
            album = album.strip()
        if title is not None:
            title = title.strip()
        if track is not None:
            track = track.strip()
            if len(track) == 1:
                track = "0" + track

        album = getAndCollectSimilarAlbum(album)
        artist = getAndCollectSimilarArtist(artist)

        if (artist is None) or (len(artist) == 0):
            artist = "unknown"
        if (album is None) or (len(album) == 0):
            album = "unknown"
            # category = None
        else:
            album = decodeAny(album)
        if len(album) == 0:
            album = "unknown"
        if title is not None:
            if track is not None:
                if title[:3] == track + ".":
                    title = title[3:].strip()
                if title[:2] == track:
                    title = title[2:].strip()
                newName = withExt(track + " " + title, ext)
                if disc is not None:
                    newName = disc + "." + newName
                    # print(newName)
            else:
                newName = withExt(title, ext)
        elif track is not None:
            newName = track + " " + subName
    except TinyTagException:
        # no tag info
        pass
    except struct.error:
        # such as "unpack requires a buffer of 34 bytes"
        # during TinyTag.get(path)
        # print("#  " * depth + "No tags: " + lowerExt)
        pass
    if artist is not None:
        ret['Artist'] = artist
    if album is not None:
        ret['Album'] = album
    if track is not None:
        ret['Track'] = track
    if title is not None:
        ret['Title'] = title
    if newName is not None:
        ret['SuggestedFileName'] = newName
    return ret


def sortFiles(preRecoveredPath, profilePath, relPath="", depth=0):
    # preRecoveredPath becomes a subdirectory upon recursion
    global catDirNames
    if os.path.isdir(preRecoveredPath):
        folderPath = preRecoveredPath
        for subName in os.listdir(folderPath):
            newPath = None
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
                    ext = ext[1:]  # remove dot
                lowerExt = ext.lower()
                if len(lowerExt) == 0:
                    if enableNoExtIgnore:
                        enableIgnore = True
                if lowerExt in ignoreExts:
                    enableIgnore = True
                if enableIgnore:
                    continue
                fileSize = os.path.getsize(subPath)
                category = None
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
                    # print('This track is by %s.' % tag.artist)
                    # print("  " * depth + subPath + ": " + str(tag))
                    catPath = catMajorPath
                    newStats = getMeta(subPath)
                    newName = newStats.get("SuggestedFileName")
                    artist = newStats.get("Artist")
                    album = newStats.get("Album")
                    if newName is None:
                        newName = subName
                    if (artist is not None) and (album is not None):
                        catPath = os.path.join(
                            os.path.join(catMajorPath, artist),
                            album
                        )
                    else:
                        catPath = os.path.join(catMajorPath, "misc")
                elif category == "Pictures":
                    try:
                        im = Image.open(subPath)
                        imSize = im.size
                        width, height = imSize
                        im.close()
                        if (isThumbnailSize(imSize)):
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
                newPath = os.path.join(catPath, newName)
                tryNum = 0
                newNamePartial = os.path.splitext(newName)[0]
                print("# moving to '" + newPath + "'")
                while os.path.isfile(newPath):
                    tryNum += 1
                    newPath = os.path.join(catPath, newNamePartial + " [" + str(tryNum) + "]")
                    newPath = withExt(newPath, ext)
                shutil.move(subPath, newPath)
                print("mv '" + newPath+ "' '" + newPath + "'")

                if enableShowLarge:
                    if fileSize > largeSize:
                        print('{0:.3g}'.format(fileSize/1024/1024) + "MB: " + newPath)
                        # g removes insignificant zeros
                if (category not in foundMaximums) or (fileSize > foundMaximums[category]):
                    foundMaximums[category] = fileSize
                    foundMaximumPaths[category] = newPath
                if lowerExt not in foundTypeCounts.keys():
                    foundTypeCounts[lowerExt] = 1
                else:
                    foundTypeCounts[lowerExt] += 1
                if category is None:
                    print("  " * depth + "unknown type: " + lowerExt + " for '" + subPath + "'")
                # print("  " * depth + "[" + str(category) + "]" + newPath)
            elif os.path.isdir(subPath):
                # print(" " * depth + subName)
                # if subName[:1] != ".":
                sortFiles(subPath, profilePath, depth=depth+1)
    else:
        customDie(preRecoveredPath + " is not a directory")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        customDie("There must be two parameters.")
    # print(sys.argv[1])
    sortFiles(sys.argv[1], sys.argv[2])

    removeExtra(sys.argv[2], sys.argv[2])  # same arg for both

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
