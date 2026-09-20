# Maintainer: brightwalker25 <7045432+brightwalker25@users.noreply.github.com>
pkgname=kbullet
pkgver=2.1.0
pkgrel=1
pkgdesc="Bullet journal for the Linux desktop - day sections, drag-and-drop, sorting, 11 entry symbols"
arch=('any')
url="https://github.com/brightwalker25/kbullet"
license=('GPL-3.0-or-later')
depends=('python' 'python-pyqt6')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')  # run `updpkgsums` once the v2.1.0 tag exists

package() {
    cd "$srcdir/$pkgname-$pkgver"

    # The script is self-contained; install it under its bare name.
    install -Dm755 kbullet.py "$pkgdir/usr/bin/$pkgname"

    install -Dm644 kbullet.desktop \
        "$pkgdir/usr/share/applications/$pkgname.desktop"

    # Mandatory on Arch: GPL-3.0-or-later is not in /usr/share/licenses/common.
    install -Dm644 LICENSE \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
