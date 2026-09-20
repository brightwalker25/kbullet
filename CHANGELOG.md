# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] — 2026-03-15

First public release.

### Added
- Per-section sort menu (⇅) on each column: by type, by time, or undo
- Right-click context menu on any entry — edit text, delete, change type,
  mark status
- Five further status markers: scheduled `<`, delegated `\`, waiting `|`,
  alongside done `×` and migrated `>`
- Mood `=`, urgent `!` and priority `*` entry types
- Master task list (<kbd>Ctrl</kbd>+<kbd>S</kbd>) gathering every open task,
  with a refresh button and a running count
- Schedule a task from the master list onto a chosen future day
- Compact mode: chrome hides automatically below 700px width
- Toggle the menu bar from **View**

### Changed
- Entry type is chosen from a combo box rather than radio buttons
- Completed entries are struck through as well as greyed out
- Sorting writes to disk immediately, so undo is in-session only

### Fixed
- Strikethrough is now cleared when an entry's status changes away from done

## [2.0.0] — 2026-01-08

### Added
- **Morning / Afternoon / Evening sections** — the day is now three columns
  instead of one list
- Drag and drop entries within a section and between sections
- New entries are filed automatically by the time of day
- Section chooser in the input row, to override that default
- Tray quick-capture for a task, event or note

### Changed
- On-disk format gained `## Morning` / `## Afternoon` / `## Evening` headers.
  Files written by 1.x are still read: their entries are distributed across
  sections by timestamp, and the headers are added the next time that day is
  saved.

## [1.0.0] — 2025

### Added
- Initial release: daily markdown journal, core bullet notation, calendar
  navigation, week and month views, search, unfinished tasks, printing,
  system tray, configurable journal directory

[2.1.0]: https://github.com/brightwalker25/kbullet/releases/tag/v2.1.0
[2.0.0]: https://github.com/brightwalker25/kbullet/releases/tag/v2.0.0
[1.0.0]: https://github.com/brightwalker25/kbullet/releases/tag/v1.0.0
