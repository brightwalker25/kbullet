# Kbullet user guide

For the complete key list see [shortcuts.md](shortcuts.md).

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
│ ◀ Previous Day │ 📅 Calendar │ Today │ Next Day ▶   ⇅Type ⇅Time ↩ │
│                    Sunday, September 20, 2026                    │
│ Type: [Task ▾]  Section: [Morning ▾]  [ entry text…      ] [Add] │
├──────────────────┬──────────────────┬────────────────────────────┤
│ 🌅 Morning    ⇅  │ ☀️ Afternoon  ⇅  │ 🌙 Evening              ⇅  │
│                  │                  │                            │
│ • [09:15] Draft  │ ○ [14:00] Dentist│ — [20:10] Good focus       │
│ × [09:40] Email  │ ! [15:30] Invoice│                            │
│                  │                  │                            │
├──────────────────┴──────────────────┴────────────────────────────┤
│  Edit  Del │ Task Event Note Mood Urgent Priority                 │
│            │ Done Un-done Migrate Schedule Delegated Waiting      │
└──────────────────────────────────────────────────────────────────┘
```

The day is three columns. Drag the dividers to resize them; the split is not
remembered between sessions.

Below 700px wide, Kbullet switches to **compact mode** — the navigation bar,
date label, input row, action buttons and menu bar hide, leaving just the three
columns. Widen the window to bring them back.

## Notation

Six entry **types**:

| Symbol | Meaning |
|:---:|---|
| `•` | Task — something to do |
| `○` | Event — something happening at a time |
| `—` | Note — an observation, not actionable |
| `=` | Mood — how the day felt |
| `!` | Urgent |
| `*` | Priority |

Five **statuses** you apply to an existing entry:

| Symbol | Meaning |
|:---:|---|
| `×` | Done — greyed out and struck through |
| `>` | Migrated to another day |
| `<` | Scheduled for a specific date |
| `\` | Delegated to someone else |
| `\|` | Waiting on someone else |

## Adding entries

1. Choose a type — the **Type** box, or <kbd>Ctrl</kbd>+<kbd>T</kbd> / <kbd>E</kbd> / <kbd>N</kbd>.
2. Choose a section, or accept the default. **Section** starts on the one
   matching the current time: Morning before noon, Afternoon until 17:00,
   Evening after.
3. Type the text and press <kbd>Enter</kbd>.

Entries are timestamped `[HH:MM]` at the moment you add them, and saved
immediately. There is no save button.

## Changing entries

Select an entry, then use the buttons below the columns — or right-click it for
the same options in a context menu:

- **Edit** — change the text, keeping the symbol and timestamp
- **Del** — remove it
- **Change type** — swap `•` for `○`, `—`, `=`, `!` or `*`
- **Mark status** — done, un-done, migrate, schedule, delegated, waiting

The action buttons stay greyed out until you select something.

## Moving entries between sections

Drag any entry to reorder it within its column, or drop it into another
column. Plans that slip from morning to afternoon move with the mouse; the
timestamp does not change, because it records when you wrote the entry.

## Sorting

Sort a single column from its ⇅ menu, or the whole day from the toolbar and the
**View** menu:

- **By type** groups tasks, then events, then notes, and so on
- **Chronologically** orders by timestamp
- **Undo** restores the previous order

Sorting is written to disk as soon as it happens, so **undo only works while
the app stays open**.

## Navigating days

<kbd>Ctrl</kbd>+<kbd>←</kbd> and <kbd>Ctrl</kbd>+<kbd>→</kbd> step a day at a
time, <kbd>Ctrl</kbd>+<kbd>H</kbd> returns to today, and 📅 **Calendar** jumps
to any date. Days with no entries open empty and are written only once you add
something.

## Week and month views

**Week view** (<kbd>Ctrl</kbd>+<kbd>W</kbd>) shows Monday to Sunday as
read-only panes, with previous/next week and a print button.

**Month view** (<kbd>Ctrl</kbd>+<kbd>K</kbd>) shows a calendar plus totals for
the month — entries, tasks, completed, and a completion rate. Click a date to
preview that day.

Both are read-only; close them to edit.

## Finding things

- **Search** (<kbd>Ctrl</kbd>+<kbd>F</kbd>) — case-insensitive text search
  across every file, newest first. Double-click a result to jump to that day.
- **Unfinished tasks** (<kbd>Ctrl</kbd>+<kbd>U</kbd>) — every open `•` task
  across the whole journal, with a **Go to Date** button.
- **Master task list** (<kbd>Ctrl</kbd>+<kbd>S</kbd>) — the same open tasks with
  their date and section, a running count, a refresh button, and the ability to
  schedule one onto a future day.

## Migrating and scheduling

**Migrate** (<kbd>Ctrl</kbd>+<kbd>M</kbd>) marks the original `>` with a
` → YYYY-MM-DD` suffix and copies it to the target day.

**Schedule** works the same way but marks the original `<`. Note the
**Schedule** button opens the master task list rather than acting on your
selection — schedule from there.

Migrated and scheduled copies always land in the target day's **Morning**
section, wherever they came from. Move them once you're there.

## Printing

<kbd>Ctrl</kbd>+<kbd>P</kbd> prints the current day; week and month views have
their own print buttons. Output keeps the section headings and symbols. Any
printer your system offers works, including print-to-PDF.

## System tray

Closing the window hides Kbullet to the tray rather than quitting. From the
tray you can show the window, quickly capture a task, event or note without
opening the full UI, or quit properly.

**Double-click** the tray icon to show or hide — a single click does nothing.

Quick-captures are filed into the section matching the current time.

## Settings

**File → Settings** has two options:

- **Journal directory** — where the markdown files live. Changing it switches
  to the new location; existing files are not moved.
- **Show timestamps on entries** — on by default.

Settings live in `~/.config/Kbullet/Settings.conf`.

> Turning timestamps **off** means new entries are written without a time.
> That is not recoverable later, and the week/month views use timestamps to
> place entries from older files.

## How files are stored

One file per day, `YYYY-MM-DD.md`, UTF-8:

```markdown
## Morning
• [09:15] Draft the quarterly report
× [09:40] Reply to the planning email

## Afternoon
○ [14:00] Dentist

## Evening
— [20:10] Good focus today
```

Two things to know:

1. **Kbullet rewrites the whole file on every change**, from what's in the
   window. It never re-reads a file it already has open, so edits made
   elsewhere — another editor, a sync client, a script — are overwritten the
   next time you change anything. Close Kbullet before editing a day by hand.
2. **Only section headers and lines starting with a valid symbol survive.**
   Any other line you add by hand is dropped on the next save.

Files from 1.x with no `##` headers are still read — entries are distributed by
timestamp — and gain headers the next time that day is saved.

## Troubleshooting

**The app won't start.** Check PyQt6 is present: `python3 -c "import PyQt6"`.
If that fails, install your distribution's PyQt6 package.

**No tray icon.** Your desktop needs a system tray or AppIndicator applet. GNOME
requires an extension for this.

**Entries look wrong in week or month view.** Older files without `##` headers
are shown entirely under Morning in those views, though the main window places
them correctly. Opening and re-saving the day fixes it permanently.

**An entry vanished.** Most likely the file was changed outside Kbullet while
it was open, then overwritten on the next save — see above. If the journal is
in a synced folder, check for conflict copies left by your sync client.

**<kbd>Ctrl</kbd>+<kbd>Z</kbd> didn't undo my typing.** It's bound to undo
sorting. Use the text field's own undo while editing.
