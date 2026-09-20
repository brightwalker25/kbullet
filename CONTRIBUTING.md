# Contributing

Thanks for taking an interest. This is a small solo project, so please **open
an issue before starting anything large** — it saves you writing code that
doesn't fit the direction.

## Running from source

```sh
git clone https://github.com/brightwalker25/kbullet.git
cd kbullet
python3 kbullet.py
```

The only dependency is PyQt6. There is no build step: `kbullet.py` is the whole
program.

Point the app at a scratch directory while developing, so you don't churn your
real journal — **File → Settings → Journal directory**, or edit `journal_dir`
in `~/.config/Kbullet/Settings.conf`.

## Layout

Everything lives in `kbullet.py` (~2200 lines):

| Area | What it is |
|---|---|
| `SectionListWidget` | One day-section column. Owns drag-and-drop, sorting and per-item styling. |
| `Kbullet` | The main window: menus, shortcuts, the input row, load/save. |
| `*Dialog` classes | Calendar, Search, Unfinished tasks, Master task list, Week view, Month view, Settings. |
| `main()` | Entry point. |

Two things are worth knowing before you change file handling:

- `save_current_day()` rewrites the entire day file from the in-memory list
  widgets. It does not read the file first, so anything written to that file by
  another process while the app is open will be lost on the next save.
- `_parse_sections()` keeps only section headers and lines beginning with a
  valid bullet symbol. Every other line in a journal file is silently dropped
  on the next save.

## Style

- Follow the surrounding code: 4-space indent, double-quoted strings,
  docstrings on classes and non-trivial methods.
- Keep it dependency-free beyond PyQt6.
- `.editorconfig` covers whitespace; please keep the file free of trailing
  whitespace and ending with a newline.

Before opening a PR:

```sh
python3 -m py_compile kbullet.py
```

and launch the app to click through what you changed. There is no test suite —
if you add one, that's a welcome contribution in itself.

## Releasing

1. Bump `__version__` in `kbullet.py` and `pkgver` in `PKGBUILD`.
2. Add a section to `CHANGELOG.md`.
3. Tag `vX.Y.Z` and push the tag.
4. Run `updpkgsums` to fill in the real `sha256sums` for the new tarball.

## Licence

By contributing you agree that your work is licensed under GPL-3.0-or-later,
the same terms as the rest of the project.
