# postrecsort

Sort files recovered by photorec using file analysis.

## Primary Features
- Move images that are mostly transparent (to dest/Backup/blank).
- Remove duplicate images by exact visual match.
- Sort by extension into Documents, Pictures, Videos, and other
  directories ($HOME/Backup/unknown if unknown type, leave unmoved in source if ignored system file).
- Sort and rename music files to "Artist/Album/track title".
- Place videos and pictures that are too small in a "thumbnails"
  directory. Use sort_images.py then sort_photos.py for finer
  categorization and ad deletion (see "Use" below).
- Tries hard to separate non-user files:
    - If title is missing from a song, it may not be a song at all,
      so it goes in "Music/misc".
    - If file is too small to be valid (check if song < 1MB, check if
      image resolution is thumbnail size, check file size otherwise),
      assume it is not, and put it in "dest/Backup/blank".
      - You would usually delete the "blank" folder manually--it only
        exists for you to confirm.

## Install
- Install the PIL and TinyTag packages for your system.
  If there is no tinytag installer/package for your OS, you may be able
  to do:

```bash
cd postrecsort
pip install tinytag -t .
```


## Use
1. Open LICENSE in text editor for disclaimer.
2. If you just want to rename songs (not sort into directories), run
   `renamesongs.py <directory>`. Otherwise, skip this step and continue
   to the next step.
3. Run [photorec](https://www.cgsecurity.org/wiki/PhotoRec_Step_By_Step)
   (or [PhotoRec
   GUI](https://www.ghacks.net/2015/04/20/how-to-use-photorec-gui-to-recover-lost-digital-photos-and-files/),
4. Run postrecsort as follows:
(If you ONLY want to sort images, skip this step)

```bash
python3 postrecsort.py <PhotoRec recovery directory> <destination directory>
```

5. Run image and photo categorization if desired, using commands below.
  - Deletion includes (but in future versions may not be limited to):
    - Ads (any with size such as 252x252)
    - Widgets from installers (any with size such as 170x330, 242x189)
    - YouTube thumbnails (any with size such as 386x217)
  - Categorization and deletion is based on size, so see code in
    moremeta.py (each instance of `'disposable' : True`)
    before continuing below!

```bash
# try to separate photographs, banners,
python3 sort_images.py <destination directory>/Pictures
# optional (sort into full date directories such as 2019-07-29):
python3 sort_photos.py <destination directory>/Pictures/<year>
```

## Developer Notes

### Similar programs
- https://github.com/silug/recsort
  (only sorts music into directories)
  - 2019-07-26: I e-mailed him (see http://www.silug.org/~steve/) to
    inform him of postrecsort. -Poikilos
