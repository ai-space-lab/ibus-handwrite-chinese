#!/bin/sh
set -e

# Build a binary .deb package for ibus-handwrite-chinese
# Usage: ./packaging/build-deb.sh [version]

VERSION="${1:-0.1.0}"
PACKAGE="ibus-handwrite-chinese"
ROOTDIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILDDIR="/tmp/${PACKAGE}-deb-build"

rm -rf "$BUILDDIR"
mkdir -p "$BUILDDIR/DEBIAN"

# Copy control files
cp "$ROOTDIR/packaging/debian/control" "$BUILDDIR/DEBIAN/"
cp "$ROOTDIR/packaging/debian/copyright" "$BUILDDIR/DEBIAN/"
cp "$ROOTDIR/packaging/debian/changelog" "$BUILDDIR/DEBIAN/changelog"
cp "$ROOTDIR/packaging/debian/postinst" "$BUILDDIR/DEBIAN/"
cp "$ROOTDIR/packaging/debian/prerm" "$BUILDDIR/DEBIAN/"
chmod 755 "$BUILDDIR/DEBIAN/postinst" "$BUILDDIR/DEBIAN/prerm"

# Add version to control
sed -i "s/^Version:.*/Version: ${VERSION}/" "$BUILDDIR/DEBIAN/control"
sed -i "s/^Maintainer:.*/Maintainer: $(git config user.name 2>/dev/null || echo 'ibus-handwrite-chinese developers') <$(git config user.email 2>/dev/null || echo 'dev@ibus-handwrite-chinese.example.com')>/" "$BUILDDIR/DEBIAN/control"

# Copy files into package tree
mkdir -p "$BUILDDIR/usr/local/bin"
mkdir -p "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/icons"
mkdir -p "$BUILDDIR/usr/share/ibus/component"
mkdir -p "$BUILDDIR/etc/udev/rules.d"

cp "$ROOTDIR/src/ibus-engine-handwrite-chinese" "$BUILDDIR/usr/local/bin/"
chmod 755 "$BUILDDIR/usr/local/bin/ibus-engine-handwrite-chinese"
cp "$ROOTDIR/src/handwrite_evdev.py" "$BUILDDIR/usr/local/bin/"
chmod 644 "$BUILDDIR/usr/local/bin/handwrite_evdev.py"
cp "$ROOTDIR/xml/handwrite-chinese-simplified.xml" "$BUILDDIR/usr/share/ibus/component/"
cp "$ROOTDIR/xml/handwrite-chinese-traditional.xml" "$BUILDDIR/usr/share/ibus/component/"
cp "$ROOTDIR/icons/handwrite-chinese-simplified.svg" "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/icons/"
cp "$ROOTDIR/icons/handwrite-chinese-traditional.svg" "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/icons/"
cp "$ROOTDIR/tools/restore.sh" "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/"
chmod 755 "$BUILDDIR/usr/local/share/ibus-handwrite-chinese/restore.sh"
cp "$ROOTDIR/tools/99-trackpad-handwrite.rules" "$BUILDDIR/etc/udev/rules.d/"

# Check for required Python modules
python3 -c "compile(open('$ROOTDIR/src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
python3 -c "compile(open('$ROOTDIR/src/handwrite_evdev.py').read(), 'evdev', 'exec')"

# Build .deb with deterministic compression
fakeroot dpkg-deb --build --root-owner-group "$BUILDDIR" "${ROOTDIR}/${PACKAGE}_${VERSION}_all.deb"

echo "Package built: ${ROOTDIR}/${PACKAGE}_${VERSION}_all.deb"
rm -rf "$BUILDDIR"
