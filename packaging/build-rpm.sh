#!/bin/sh
set -e

# Build an RPM package for ibus-handwrite-chinese
# Usage: ./packaging/build-rpm.sh [version] [dist]

VERSION="${1:-0.1.0}"
DIST="${2:-%{nil}}"
PACKAGE="ibus-handwrite-chinese"
ROOTDIR="$(cd "$(dirname "$0")/.." && pwd)"

# Determine dist suffix for Fedora
case "$DIST" in
    fc*) DIST_SUFFIX=".${DIST}" ;;
    el*) DIST_SUFFIX=".${DIST}" ;;
    *)    DIST_SUFFIX="" ;;
esac

# Create RPM build tree
RPMBUILDDIR="/tmp/${PACKAGE}-rpm-build"
rm -rf "$RPMBUILDDIR"
mkdir -p "$RPMBUILDDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
TARDIR="${PACKAGE}-${VERSION}"
TARBALL="${PACKAGE}-${VERSION}.tar.gz"
rm -rf "/tmp/${TARDIR}"
mkdir -p "/tmp/${TARDIR}"
cp -r "$ROOTDIR/src" "$ROOTDIR/xml" "$ROOTDIR/icons" "$ROOTDIR/tools" \
      "$ROOTDIR/packaging" \
      "$ROOTDIR/README.md" "$ROOTDIR/README.zh-Hans.md" "$ROOTDIR/README.zh-Hant.md" \
      "$ROOTDIR/LICENSE" "$ROOTDIR/bootstrap.sh" "/tmp/${TARDIR}/"
tar -czf "$RPMBUILDDIR/SOURCES/$TARBALL" -C /tmp "$TARDIR"
rm -rf "/tmp/${TARDIR}"

# Copy spec and update version
sed "s/Version:.*/Version: ${VERSION}/" "$ROOTDIR/packaging/ibus-handwrite-chinese.spec" > "$RPMBUILDDIR/SPECS/${PACKAGE}.spec"

# Build RPM (dist auto-detected from container)
rpmbuild --define "_topdir ${RPMBUILDDIR}" \
         -bb "$RPMBUILDDIR/SPECS/${PACKAGE}.spec"

# Copy built RPM to ROOTDIR
RPM_FILE=$(find "$RPMBUILDDIR/RPMS" -name "${PACKAGE}-${VERSION}-1*.noarch.rpm" -print -quit)
if [ -n "$RPM_FILE" ]; then
    cp "$RPM_FILE" "$ROOTDIR/"
    echo "RPM copied: $ROOTDIR/$(basename "$RPM_FILE")"
else
    echo "Warning: RPM not found"
    ls -la "$RPMBUILDDIR/RPMS/noarch/" 2>/dev/null || true
fi

rm -rf "$RPMBUILDDIR"
