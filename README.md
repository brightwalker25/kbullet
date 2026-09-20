# Kbullet

A bullet journal for the Linux desktop. Kbullet follows [Ryder Carroll's Bullet
Journal method](https://bulletjournal.com/) and stores each day as an ordinary
markdown file, so your journal outlives the app that wrote it.

The day is split into **Morning**, **Afternoon** and **Evening**. New entries
land in the section matching the current time; drag them between columns as
plans change.

> **Status:** works well day to day, but it is a single-developer project with
> no automated tests. Back up your journal directory like you would any other
> plain-text notes.

## Features

- Three time-of-day sections, with entries auto-filed by the clock
- Drag and drop within and between sections
- 11 bullet-journal symbols, colour-coded
- Sort by type or chronologically, per section or across the day; undo in-session
- Week and month views, with printing and per-day stats
- Search across every entry; a master task list and an unfinished-task view
- Migrate or schedule a task onto a future day
- System-tray quick capture for a task, event or note
- Settings for journal location and timestamp display

## Requirements

- Python 3.9+
- PyQt6

## Install

### Arch-based distributions

```sh
git clone https://github.com/brightwalker25/kbullet.git
cd kbullet
makepkg -si
```

This installs `/usr/bin/kbullet` plus a desktop entry, and pulls in
`python-pyqt6` automatically.

### Any other distribution

Install PyQt6 through your package manager — `python3-pyqt6` on Debian and
Ubuntu, `python3-qt6` on Fedora — then:

```sh
install -Dm755 kbullet.py ~/.local/bin/kbullet
install -Dm644 kbullet.desktop ~/.local/share/applications/kbullet.desktop
```

Make sure `~/.local/bin` is on your `PATH`.

### Run without installing

```sh
python3 kbullet.py
```

## Notation

| Symbol | Meaning  | | Symbol | Meaning |
|:---:|---|---|:---:|---|
| `•` | Task      | | `×` | Done |
| `○` | Event     | | `>` | Migrated |
| `—` | Note      | | `<` | Scheduled |
| `=` | Mood      | | `\` | Delegated |
| `!` | Urgent    | | `\|` | Waiting |
| `*` | Priority  | | | |

The first six are entry *types*; the rest are *statuses* applied to an existing
entry. Completed entries are greyed out and struck through.

## Most-used shortcuts

| Key | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>T</kbd> / <kbd>E</kbd> / <kbd>N</kbd> | New entry as Task / Event / Note |
| <kbd>Enter</kbd> | Add the entry |
| <kbd>Ctrl</kbd>+<kbd>D</kbd> | Mark selected done |
| <kbd>Ctrl</kbd>+<kbd>M</kbd> | Migrate selected to another day |
| <kbd>Ctrl</kbd>+<kbd>←</kbd> / <kbd>→</kbd> | Previous / next day |
| <kbd>Ctrl</kbd>+<kbd>H</kbd> | Go to today |
| <kbd>Ctrl</kbd>+<kbd>F</kbd> | Search the journal |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | Master task list |
| <kbd>Ctrl</kbd>+<kbd>W</kbd> / <kbd>K</kbd> | Week / month view |

The full list is in [docs/shortcuts.md](docs/shortcuts.md).

## How your journal is stored

One file per day, named `YYYY-MM-DD.md`, in `~/Documents/Kbullet` by default
(change it in **File → Settings**):

```markdown
## Morning
• [09:15] Draft the quarterly report
× [09:40] Reply to the planning email

## Afternoon
○ [14:00] Dentist
! [15:30] Chase the invoice

## Evening
— [20:10] Good focus today; afternoon ran away from me
```

Timestamps are written only while **Show timestamps** is enabled — turning it
off means new entries are saved without a time, which cannot be recovered
later.

Because the format is plain markdown, the journal is readable in any editor,
greppable, and versionable with git.

### A note on sync

Kbullet rewrites the whole day file on every change. That is fine for a folder
synced with Nextcloud, Syncthing or similar **as long as you edit on one
machine at a time** — two machines writing the same day can produce a sync
conflict that costs you that day's entries. Kbullet does not detect or merge
external changes to a file it already has open.

## Documentation

- [User guide](docs/user-guide.md) — every feature in detail
- [Keyboard shortcuts](docs/shortcuts.md) — the complete list
- [Packaging](docs/packaging.md) — building and releasing
- [Changelog](CHANGELOG.md)

## Contributing

Issues and pull requests are welcome — please open an issue before starting
anything large. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

GPL-3.0-or-later. See [LICENSE](LICENSE).

Kbullet is free software: you may use, study, share and modify it. If you
distribute a modified version, it must stay under the same licence and you must
make your source available. It comes with no warranty.
