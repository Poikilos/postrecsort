# Changelog
All notable changes to this project will be documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [git 33341d7] - 2019-07-24
### Added
- Make separate getMeta function (code was formerly in loop).
- Add renamesongs.py for renaming songs in existing directories.

### Changed
- Use dict from getMeta instead of using TinyTag directly.
- Fix bug on missing artist (was being changed to the word "album").
- Prepend disc number to filename if present.
