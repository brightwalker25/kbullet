# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-15

The first version published to this repository. Earlier versions were never
released publicly, and are recorded below for context.

### Added
- A per-section sort menu on each column, offering sort by type, sort by
  time, or undo
- A right-click context menu on any entry, for editing the text, deleting it,
  changing its type or marking its status
- Three further status markers, scheduled `<`, delegated `\` and waiting `|`,
  alongside the existing done `×` and migrated `>`
- Mood `=`, urgent `!` and priority `*` entry types
- Master task list (<kbd>Ctrl</kbd>+<kbd>S</kbd>) gathering every open task,
  with a refresh button and a running count
- Schedule a task from the master list onto a chosen future day
- Compact mode, which hides the surrounding controls automatically below 700
  pixels wide
- Toggle the menu bar from **View**

### Changed
- Entry type is chosen from a combo box rather than radio buttons
- Completed entries are struck through as well as greyed out
- Sorting writes to disk immediately, so undo is in-session only

### Fixed
- Strikethrough is now cleared when an entry's status changes away from done
- <kbd>Ctrl</kbd>+<kbd>Q</kbd> and the tray's Quit item now exit the
  application. Both previously called `close()`, which the close handler
  ignored unconditionally, so the app could only be quit by killing it
- The window now sets a Wayland `app_id`, so it identifies itself as `kbullet`
  rather than falling back to `python3`. Window rules, launchers and taskbars
  can now target it

## [2.0.0] - 2026-01-08

### Added
- **Morning, Afternoon and Evening sections.** The day is now three columns
  rather than a single list
- Drag and drop entries within a section and between sections
- New entries are filed automatically by the time of day
- Section chooser in the input row, to override that default
- Tray quick-capture for a task, event or note

### Changed
- On-disk format gained `## Morning` / `## Afternoon` / `## Evening` headers.
  Files written by 1.x are still read: their entries are distributed across
  sections by timestamp, and the headers are added the next time that day is
  saved.

## [1.0.0] - 2025-12-20

### Added
- The first working version: daily markdown journal, core bullet notation, calendar
  navigation, week and month views, search, unfinished tasks, printing,
  system tray, configurable journal directory

[2.1.0]: https://github.com/brightwalker25/kbullet/releases/tag/v2.1.0
