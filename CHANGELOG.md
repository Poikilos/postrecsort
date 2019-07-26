# Changelog
All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [git] - 2019-07-26
### Added
- sort_photos.py (formerly photoput.py local project)
- sort_images.py
- Add new sort_images backend features to moremeta.py which was
  formerly called internaldates.py and used by sort_photos.py

### Changed
- Rename photoput to sort_photos.

## [git 33341d7] - 2019-07-24
### Added
- Make separate getMeta function (code was formerly in loop).
- Add renamesongs.py for renaming songs in existing directories.

### Changed
- Use dict from getMeta instead of using TinyTag directly.
- Fix bug on missing artist (was being changed to the word "album").
- Prepend disc number to filename if present.
