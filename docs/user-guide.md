# Kbullet user guide

For the complete key list, see [shortcuts.md](shortcuts.md).

## Contents

- [The main window](#the-main-window)
- [Notation](#notation)
- [Adding entries](#adding-entries)
- [Changing entries](#changing-entries)
- [Moving entries between sections](#moving-entries-between-sections)
- [Sorting](#sorting)
- [Navigating days](#navigating-days)
- [Week and month views](#week-and-month-views)
- [Finding things](#finding-things)
- [Migrating and scheduling](#migrating-and-scheduling)
- [Printing](#printing)
- [System tray](#system-tray)
- [Settings](#settings)
- [How files are stored](#how-files-are-stored)
- [Troubleshooting](#troubleshooting)

## The main window

```
┌──────────────────────────────────────────────────────────────────┐
│ File   View   Search   Help                                      │
├──────────────────────────────────────────────────────────────────┤
│ ◀ Previous Day │ Calendar │ Today │ Next Day ▶     ⇅Type ⇅Time ↩ │
│                    Sunday, September 20, 2026                    │
│ Type: [Task ▾]  Section: [Morning ▾]  [ entry text…      ] [Add] │
├──────────────────┬──────────────────┬────────────────────────────┤
│ Morning       ⇅  │ Afternoon     ⇅  │ Evening                 ⇅  │
│                  │                  │                            │
│ • [09:15] Draft  │ ○ [14:00] Dentist│ — [20:10] Good focus       │
│ × [09:40] Email  │ ! [15:30] Invoice│                            │
│                  │                  │                            │
├──────────────────┴──────────────────┴────────────────────────────┤
│  Edit  Del │ Task Event Note Mood Urgent Priority                 │
│            │ Done Un-done Migrate Schedule Delegated Waiting      │
└──────────────────────────────────────────────────────────────────┘
```

The day is laid out as three columns. You can drag the dividers to resize them,
although the split is not remembered between sessions.

Below 700 pixels wide, Kbullet switches to compact mode. The navigation bar,
date label, input row, action buttons and menu bar all hide, leaving just the
three columns. Widen the window to bring them back.

## Notation

There are six entry types:

| Symbol | Meaning |
|:---:|---|
| `•` | Task, meaning something to do |
| `○` | Event, meaning something happening at a particular time |
| `—` | Note, meaning an observation rather than an action |
| `=` | Mood, meaning how the day felt |
| `!` | Urgent |
| `*` | Priority |

There are five statuses, which you apply to an entry that already exists:

| Symbol | Meaning |
|:---:|---|
| `×` | Done, shown greyed out and struck through |
| `>` | Migrated to another day |
| `<` | Scheduled for a specific date |
| `\` | Delegated to someone else |
| `\|` | Waiting on someone else |

## Adding entries

1. Choose a type, either from the **Type** box or with
   <kbd>Ctrl</kbd>+<kbd>T</kbd>, <kbd>Ctrl</kbd>+<kbd>E</kbd> or
   <kbd>Ctrl</kbd>+<kbd>N</kbd>.
2. Choose a section, or accept the default. **Section** starts on whichever one
   matches the current time: Morning before noon, Afternoon from noon until
   17:00, and Evening from 17:00 onwards.
3. Type the text and press <kbd>Enter</kbd>.

Entries are saved immediately, and there is no save button. While **Show
timestamps** is enabled, which it is by default, each entry is also stamped
`[HH:MM]` at the moment you add it.

## Changing entries

Select an entry, then use the buttons below the columns. Right-clicking the
entry offers the same options in a context menu:

- **Edit** changes the text, keeping the symbol and timestamp.
- **Del** removes the entry.
- **Change type** swaps `•` for `○`, `—`, `=`, `!` or `*`.
- **Mark status** applies done, un-done, migrate, schedule, delegated or
  waiting.

The action buttons stay greyed out until you select something.

## Moving entries between sections

Drag any entry to reorder it within its column, or drop it into another column.
When a plan slips from the morning to the afternoon, you can move it with the
mouse. The timestamp does not change, because it records when you wrote the
entry rather than when the entry is due.

## Sorting

You can sort a single column from its own sort menu, or the whole day from the
toolbar and the **View** menu:

- **By type** groups urgent entries first, then priority, task, event, note and
  mood, with the status markers last.
- **Chronologically** orders entries by timestamp.
- **Undo** restores the previous order.

Sorting is written to disk as soon as it happens, so the undo only works while
the app stays open.

## Navigating days

<kbd>Ctrl</kbd>+<kbd>←</kbd> and <kbd>Ctrl</kbd>+<kbd>→</kbd> step a day at a
time, <kbd>Ctrl</kbd>+<kbd>H</kbd> returns to today, and the **Calendar** button
jumps to any date. Days with no entries open empty, and Kbullet writes the file
only once you add something.

## Week and month views

**Week view**, at <kbd>Ctrl</kbd>+<kbd>W</kbd>, shows Monday to Sunday as
read-only panes, with buttons for the previous and next week and for printing.

**Month view**, at <kbd>Ctrl</kbd>+<kbd>K</kbd>, shows a calendar alongside
totals for the month: entries, tasks, completed tasks and a completion rate.
Click a date to preview that day.

Both views are read-only, so close them to edit.

## Finding things

- **Search**, at <kbd>Ctrl</kbd>+<kbd>F</kbd>, performs a case-insensitive text
  search across every file, newest first. Double-click a result to jump to that
  day.
- **Unfinished tasks**, at <kbd>Ctrl</kbd>+<kbd>U</kbd>, lists every open `•`
  task across the whole journal, with a **Go to Date** button.
- **Master task list**, at <kbd>Ctrl</kbd>+<kbd>S</kbd>, shows the same open
  tasks together with their date and section, a running count, a refresh button,
  and the ability to schedule a task onto a future day.

## Migrating and scheduling

**Migrate**, at <kbd>Ctrl</kbd>+<kbd>M</kbd>, marks the original entry `>` with
a ` → YYYY-MM-DD` suffix and copies it to the target day.

**Schedule** works in the same way but marks the original `<`. Note that the
**Schedule** button opens the master task list rather than acting on your
selection, so schedule from there.

Migrated and scheduled copies always land in the target day's Morning section,
wherever they came from. Move them once you are there.

## Printing

<kbd>Ctrl</kbd>+<kbd>P</kbd> prints the current day, and the week and month
views have their own print buttons. The output keeps the section headings and
symbols. Any printer your system offers will work, including print to PDF.

## System tray

Closing the window hides Kbullet to the tray rather than quitting. From the tray
you can show the window, capture a task, event or note quickly without opening
the full interface, or quit properly.

Double-click the tray icon to show or hide the window. A single click does
nothing.

Quick captures are filed into whichever section matches the current time.

## Settings

**File, then Settings** offers two options:

- **Journal directory** sets where the markdown files live. Changing it switches
  to the new location, and existing files are not moved.
- **Show timestamps on entries** is enabled by default.

Settings are stored in `~/.config/Kbullet/Settings.conf`.

> Turning timestamps off means new entries are written without a time. That is
> not recoverable later, and the week and month views rely on timestamps to
> place entries from older files.

## How files are stored

Kbullet writes one file per day, named `YYYY-MM-DD.md`, encoded as UTF-8:

```markdown
## Morning
• [09:15] Draft the quarterly report
× [09:40] Reply to the planning email

## Afternoon
○ [14:00] Dentist

## Evening
— [20:10] Good focus today
```

There are two things worth knowing about how this works:

1. Kbullet rewrites the whole file on every change, using what is currently in
   the window. It never re-reads a file it already has open, so any edit made
   elsewhere, whether in another editor, by a sync client or by a script, is
   overwritten the next time you change anything. Close Kbullet before editing a
   day by hand.
2. Only section headers and lines starting with a valid symbol survive. Any
   other line you add by hand is dropped on the next save.

Files written by version 1.x have no `##` headers, but Kbullet still reads them.
Their entries are distributed by timestamp, and the headers are added the next
time that day is saved.

## Troubleshooting

**The app will not start.** Check that PyQt6 is present by running
`python3 -c "import PyQt6"`. If that fails, install your distribution's PyQt6
package.

**There is no tray icon.** Your desktop needs a system tray or an AppIndicator
applet. GNOME requires an extension for this.

**Entries look wrong in the week or month view.** Older files without `##`
headers are shown entirely under Morning in those views, even though the main
window places them correctly. Opening and re-saving the day fixes it
permanently.

**An entry has vanished.** The most likely cause is that the file was changed
outside Kbullet while it was open, then overwritten on the next save, as
described above. If your journal is in a synced folder, check for conflict
copies left behind by your sync client.

**<kbd>Ctrl</kbd>+<kbd>Z</kbd> did not undo my typing.** It is bound to undo
sorting. Use the text field's own undo while editing.
