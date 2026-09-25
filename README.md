# Kbullet

A bullet journal for the Linux desktop. Kbullet follows [Ryder Carroll's Bullet
Journal method](https://bulletjournal.com/) and stores each day as an ordinary
markdown file, so your journal outlives the app that wrote it.

The day is split into Morning, Afternoon and Evening. New entries land in the
section matching the current time, and you can drag them between columns as
plans change.

> **Status:** Kbullet works well day to day, but it is a single-developer
> project with no automated tests. Please back up your journal directory as you
> would any other plain-text notes.

## Features

- Three time-of-day sections, with entries filed automatically by the clock
- Drag and drop within and between sections
- Eleven bullet-journal symbols, each colour-coded
- Sorting by type or chronologically, per section or across the whole day, with
  an in-session undo
- Week and month views, both printable, with per-day statistics
- Search across every entry, plus a master task list and an unfinished-task view
- Migrate or schedule a task onto a future day
- System-tray quick capture for a task, event or note
- Settings for the journal location and timestamp display

## Requirements

- Python 3.9 or newer
- PyQt6

## Installing

### Arch-based distributions

```sh
git clone https://github.com/brightwalker25/kbullet.git
cd kbullet
makepkg -si
```

This installs `/usr/bin/kbullet` along with a desktop entry, and pulls in
`python-pyqt6` automatically.

### Other distributions

Install PyQt6 through your package manager. It is `python3-pyqt6` on Debian and
Ubuntu, and `python3-qt6` on Fedora. Then run:

```sh
install -Dm755 kbullet.py ~/.local/bin/kbullet
install -Dm644 kbullet.desktop ~/.local/share/applications/kbullet.desktop
```

Make sure `~/.local/bin` is on your `PATH`.

### Running without installing

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

The six symbols in the left column are entry *types*. The five on the right are
*statuses*, which you apply to an entry that already exists. Completed entries
are greyed out and struck through.

## Most-used shortcuts

| Key | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>T</kbd> / <kbd>E</kbd> / <kbd>N</kbd> | New entry as Task, Event or Note |
| <kbd>Enter</kbd> | Add the entry |
| <kbd>Ctrl</kbd>+<kbd>D</kbd> | Mark the selected entry done |
| <kbd>Ctrl</kbd>+<kbd>M</kbd> | Migrate the selected entry to another day |
| <kbd>Ctrl</kbd>+<kbd>←</kbd> / <kbd>→</kbd> | Previous or next day |
| <kbd>Ctrl</kbd>+<kbd>H</kbd> | Go to today |
| <kbd>Ctrl</kbd>+<kbd>F</kbd> | Search the journal |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | Master task list |
| <kbd>Ctrl</kbd>+<kbd>W</kbd> / <kbd>K</kbd> | Week or month view |

The full list is in [docs/shortcuts.md](docs/shortcuts.md).

## How your journal is stored

Kbullet writes one file per day, named `YYYY-MM-DD.md`, in `~/Documents/Kbullet`
by default. You can change the location in **File, then Settings**.

```markdown
## Morning
• [09:15] Draft the quarterly report
× [09:40] Reply to the planning email

## Afternoon
○ [14:00] Dentist
! [15:30] Chase the invoice

## Evening
— [20:10] Good focus today, though the afternoon ran away from me
```

Timestamps are written only while **Show timestamps** is enabled. Turning it off
means new entries are saved without a time, and that time cannot be recovered
later.

Because the format is plain markdown, your journal is readable in any editor,
searchable with `grep`, and easy to keep under version control.

### A note on syncing

Kbullet rewrites the whole day file on every change. That is fine for a folder
synced with Nextcloud, Syncthing or similar, provided you edit on one machine at
a time. If two machines write the same day, your sync client will produce a
conflict that can cost you that day's entries. Kbullet does not detect or merge
changes made to a file it already has open.

## Optional extras

This is not required, and Kbullet does not depend on it.

- [omarchy-kbullet](https://github.com/brightwalker25/omarchy-kbullet) puts
  today's entries in the [Omarchy](https://omarchy.org) bar, with an open-task
  count and buttons to open Kbullet or capture an entry. It is only of use if
  you run Omarchy, which is why it lives in a separate repository.

## Documentation

- [User guide](docs/user-guide.md): every feature in detail
- [Keyboard shortcuts](docs/shortcuts.md): the complete list
- [Packaging](docs/packaging.md): building and releasing
- [Changelog](CHANGELOG.md)

## Contributing

Issues and pull requests are welcome. Please open an issue before starting
anything large. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Written with AI help

Yes, an AI helped write this. No, it has not become self-aware, and I have
checked the code to make sure it is not plotting anything. If that still puts
you off, no hard feelings. The whole point of Linux is that you decide what
runs on your computer.

## Licence

Kbullet is licensed under GPL-3.0-or-later. See [LICENSE](LICENSE).

Kbullet is free software: you may use, study, share and modify it. If you
distribute a modified version, it must remain under the same licence and you
must make your source available. It comes with no warranty.
