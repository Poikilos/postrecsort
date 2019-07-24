# postrecsort

Sort files recovered by photorec, as comprehensively as possible.

## Primary Features
- Remove images that are transparent.
- Remove duplicate images by exact visual match.
- Sort by extension into Documents, Pictures, Videos, and other
  directories ($HOME/Backup/unknown if unknown type).
- Sort and rename music files to "Artist/Album/track title".
- Place videos and pictures that are too small in a "thumbnails"
  directory.
- Tries hard to separate non-user files:
    - If title is missing from a song, it may not be a song at all,
      so it goes in "Music/misc".

## Install
- Install the PIL and TinyTag packages for your system.
  If they are unavailable, you may be able to do:
  ```
cd postrecsort
pip install tinytag -t .
pip install Pillow -t .
```

## Use
- Type `python3 postrecsort.py` to see instructions.


## Developer Notes

### Similar programs
- https://github.com/silug/recsort
