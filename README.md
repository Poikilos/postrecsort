# postrecsort

Sort files recovered by photorec using file analysis.

## Primary Features
- Move images that are mostly transparent (to dest/Backup/blank).
- Remove duplicate images by exact visual match.
- Sort by extension into Documents, Pictures, Videos, and other
  directories ($HOME/Backup/unknown if unknown type, leave unmoved in source if ignored system file).
- Sort and rename music files to "Artist/Album/track title".
- Place videos and pictures that are too small in a "thumbnails"
  directory.
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
  If they are unavailable, you may be able to do:
  ```
cd postrecsort
pip install tinytag -t .
pip install Pillow -t .
```

## Use
- If you just want to rename songs (not sort into directories), run `renamesongs.py <directory>`. Otherwise, continue to the next step.
- Run PhotoRec, then:
(If you just want to sort images, skip the first command below)
```
python3 postrecsort.py <PhotoRec recovery directory> <destination directory>
# try to separate photographs, banners,
python3 sort_images.py <destination directory>/Pictures
# optional (sort into full date directories such as 2019-07-29):
python3 sort_photos.py <destination directory>/Pictures/<year>
```

## Developer Notes

### Similar programs
- https://github.com/silug/recsort
  (only sorts music into directories)
