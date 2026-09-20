# Packaging

Kbullet is a single Python file with one runtime dependency (PyQt6), so
packaging is deliberately simple.

## What gets installed

| File | Destination |
|---|---|
| `kbullet.py` | `/usr/bin/kbullet` (mode 755, renamed) |
| `kbullet.desktop` | `/usr/share/applications/kbullet.desktop` |
| `LICENSE` | `/usr/share/licenses/kbullet/LICENSE` |

The licence install is required by Arch policy: GPL-3.0-or-later is not one of
the licences kept in `/usr/share/licenses/common/`.

## Building on Arch

```sh
git clone https://github.com/brightwalker25/kbullet.git
cd kbullet
makepkg -si
```

`makepkg -si` builds the package and installs it, pulling in `python` and
`python-pyqt6`.

To build without installing:

```sh
makepkg -f
sudo pacman -U kbullet-2.1.0-1-any.pkg.tar.zst
```

Never pass `--overwrite` to work around a file conflict. A conflict means
another install is already holding those paths, so remove it first:

```sh
sudo pacman -Rns kbullet          # if a previous package is installed
sudo rm -f /usr/local/bin/kbullet /usr/local/bin/kbullet.py   # older manual installs
```

## Cutting a release

1. Bump `__version__` in `kbullet.py` and `pkgver` in `PKGBUILD`. The two must
   match.
2. Add the release to `CHANGELOG.md`.
3. Commit, tag and push:
   ```sh
   git commit -am "Release 2.1.0"
   git tag -a v2.1.0 -m "Release 2.1.0"
   git push origin main --tags
   ```
4. Fill in the real checksum now the tag's tarball exists:
   ```sh
   updpkgsums          # from pacman-contrib
   makepkg -f          # verify it still builds
   ```
5. Commit the updated `PKGBUILD`.

`sha256sums` ships as `SKIP` until a tag exists. Leaving it as `SKIP` in a
published package is wrong, because it disables integrity checking entirely: a
corrupted or tampered-with tarball would install silently.

## Publishing to the AUR

This requires an AUR account with your SSH key registered.

```sh
makepkg --printsrcinfo > .SRCINFO
git clone ssh://aur@aur.archlinux.org/kbullet.git aur-kbullet
cd aur-kbullet
cp ../PKGBUILD ../.SRCINFO .
git add PKGBUILD .SRCINFO
git commit -m "Initial import: kbullet 2.1.0"
git push
```

`.SRCINFO` must be regenerated and committed on every version bump, or the AUR
will reject the push.

Check the package before submitting:

```sh
namcap PKGBUILD
namcap kbullet-2.1.0-1-any.pkg.tar.zst
```

## Other distributions

There is no package yet, so install it by hand:

```sh
sudo install -Dm755 kbullet.py /usr/local/bin/kbullet
sudo install -Dm644 kbullet.desktop /usr/share/applications/kbullet.desktop
```

PyQt6 comes from `python3-pyqt6` on Debian and Ubuntu, `python3-qt6` on Fedora,
and `python311-qt6` on openSUSE.

For a per-user install needing no root, use `~/.local/bin` and
`~/.local/share/applications` instead.

## A note on build artefacts

`makepkg` leaves `pkg/` and `src/` behind. Both are in `.gitignore`, and they
should stay that way, because `pkg/kbullet/.BUILDINFO` records the absolute
build path along with a complete list of every package installed on the build
machine. Built `.pkg.tar.zst` files belong on a GitHub Release rather than in
git.
