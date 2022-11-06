#!/usr/bin/env python

import sys
import os
import shutil
import filecmp
# import md5

try:
    from PIL import Image
except ImportError:
    print("This program requires PIL such as from the python-pil package")

from moremeta import (
    isThumbnailSize,
    neatMetaTags,
    replaceMany,
    cleanFileName,
    withExt,
    getCategoryByExt,
    knownThumbnailSizes,
)

def usage():
    print(sys.argv[0] + " <photorec result directory with recup_dir.*> <profile>")


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
ignore = ["user", "nohup.out"]


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

# Do not recurse into doneNames
doneNames = ["blank", "duplicates", "thumbnails", "unusable"]

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

def removeExtra(folderPath, profilePath, relPath="", depth=0):
    backupPath = os.path.join(profilePath, "Backup")
    print("# checking for blanks in: " + folderPath)
    prevIm = None
    prevSize = None
    prevDestPath = None
    parentName = os.path.basename(folderPath)

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
            category = getCategoryByExt(lowerExt)

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
            newName = cleanFileName(newName)

            if isDup:
                print("#dup:")
                print("rm '" + subPath + "'")
                os.remove(subPath)  # do not set previous if removing
                continue

            if isBlank:
                newParentPath = os.path.join(backupPath, "blank")
            elif subCatName is not None:
                if subCatName != parentName:
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

def sortFiles(preRecoveredPath, profilePath, relPath="", depth=0, enablePrint=False):
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
                category = getCategoryByExt(lowerExt)
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
                    newStats = neatMetaTags(subPath)
                    newName = newStats.get("SuggestedFileName")
                    artist = newStats.get("Artist")
                    album = newStats.get("Album")
                    # if artist == "unknown":
                        # debug only arst
                        # print("unknown artist in " + str(newStats))
                        # exit(1)
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
                # if enablePrint:
                    # print("# moving to '" + newPath + "'")
                if os.path.isfile(newPath):
                    if fileSize <= os.path.getsize(newPath):
                        continue
                    elif fileSize > os.path.getsize(newPath):
                        print("# removing smaller '" + newPath + "' and keeping '" + subPath + "'")
                        os.remove(newPath)

                # while os.path.isfile(newPath):
                    # tryNum += 1
                    # newPath = os.path.join(catPath, newNamePartial + " [" + str(tryNum) + "]")
                    # newPath = withExt(newPath, ext)
                shutil.move(subPath, newPath)
                if enablePrint:
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
    enableCleanup = True
    for argI in range(len(sys.argv)):
        arg = sys.argv[argI]
        if argI == 0:
            # script name
            pass
        elif arg[:2] == "--":
            if arg == "--nocleanup":
                enableCleanup = False
            else:
                customDie("Unknown option: " + arg)
    if enableCleanup:
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
