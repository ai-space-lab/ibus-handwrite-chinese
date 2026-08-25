# Plan: Distribute ibus-handwrite-chinese to the World

**Slug**: distribute-world  
**Intent**: CLEAR (distribution plan with known outcome)  
**Review Required**: true (non-trivial multi-channel distribution)  
**Author**: Mint User <mint@ibus-handwrite>  

---

## 1. Project Summary

**ibus-handwrite-chinese v0.6.0** - A Chinese handwriting IME for Linux with:
- macOS-style floating panel + evdev trackpad input
- PP-OCRv6 ONNX recognition (18,710 chars, 100% top-1 accuracy on 40 samples)
- 6-tab GTK3 preference dialog (`--setup`)
- On-demand model download + SHA256 verification
- User dictionary (SQLite), TOML config, configurable shortcuts
- Cross-distro: Debian/Ubuntu/Mint, Fedora, Arch/Manjaro, openSUSE Tumbleweed

**Current distribution**: GitHub Releases (.deb, .rpm, source tarball) + `bootstrap.sh` curl installer.

---

## 2. Target Distribution Channels

| Channel | Status | Priority | Effort |
|---------|--------|----------|--------|
| **Arch Linux AUR** | PKGBUILD exists, not submitted | HIGH | Low (1-2 hrs) |
| **Fedora COPR** | RPM spec ready, needs SRPM | HIGH | Medium (2-4 hrs) |
| **openSUSE OBS** | RPM spec ready, needs _service | HIGH | Medium (2-4 hrs) |
| **Debian/Ubuntu PPA** | .deb builds, needs Launchpad | MEDIUM | High (days for review) |
| **Flatpak** | No manifest yet | MEDIUM | Medium (4-8 hrs) |
| **Nixpkgs** | No derivation yet | LOW | Medium (4-8 hrs) |
| **Website/Docs** | README only | HIGH | Low (2-4 hrs) |
| **Community/SEO** | None | MEDIUM | Ongoing |

---

## 3. Owner Decisions (Requiring Your Input)

> **These are irreversible / cross-cutting choices you must own. Defaults are proposed but you decide.**

| # | Decision | Options | Proposed Default | Your Choice |
|---|----------|---------|------------------|-------------|
| 1 | **AUR package name** | `ibus-handwrite-chinese` / `ibus-handwrite-chinese-git` | Stable: `ibus-handwrite-chinese` | |
| 2 | **Fedora strategy** | COPR only / Official repo review / Both | Start with COPR, then official review | |
| 3 | **openSUSE strategy** | OBS home project / Factory submission | Home project first (`home:mint-user`) | |
| 4 | **Flatpak vs Snap** | Flatpak only / Both / Neither | Flatpak only (better Wayland, distro-agnostic) | |
| 5 | **Version in debian/control** | Fix 0.7.0→0.6.0 / Auto-generate from tag | Auto-generate from Git tag | |
| 6 | **Website** | GitHub Pages / Netlify / Simple README badge page | GitHub Pages with mkdocs-material | |
| 7 | **Chinese community channels** | Post to Linux.cn / V2EX / 少数派 / r/linuxcn | Yes, bilingual announcement | |
| 8 | **Upstream IBus wiki** | Add to ibus/ibus wiki "Engines" page | Yes | |

---

## 4. Implementation Tasks

### Phase 1: Repository Polish (Prerequisites)

- [ ] **1.1** Fix `packaging/debian/control` version from `0.7.0` → `0.6.0` (or auto-generate from Git tag in release workflow)
- [ ] **1.2** Update RPM spec changelog with v0.6.0 entry
- [ ] **1.3** Update PKGBUILD `sha256sums` from `SKIP` to actual checksum (auto-generate in release workflow)
- [ ] **1.4** Verify all packaging scripts work locally (`build-deb.sh`, `build-rpm.sh`, `makepkg`)

### Phase 2: Arch Linux AUR (Week 1)

- [ ] **2.1** Create AUR account and SSH key
- [ ] **2.2** Generate `.SRCINFO` from PKGBUILD (`makepkg --printsrcinfo > .SRCINFO`)
- [ ] **2.3** Add `.gitignore` for AUR (exclude build artifacts, keep `PKGBUILD`, `.SRCINFO`, `*.install`, `*.patch`)
- [ ] **2.4** Push to AUR: `git remote add aur ssh://aur@aur.archlinux.org/ibus-handwrite-chinese.git && git push aur master`
- [ ] **2.5** Test install: `paru -S ibus-handwrite-chinese` on clean Arch VM
- [ ] **2.6** (Optional) Submit `-git` variant for development version

### Phase 3: Fedora COPR (Week 1-2)

- [ ] **3.1** Create Fedora Account System (FAS) account
- [ ] **3.2** Install `copr-cli`, authenticate
- [ ] **3.3** Create COPR project: `copr-cli create ibus-handwrite-chinese --chroot fedora-41-x86_64 --chroot fedora-42-x86_64 --chroot fedora-rawhide-x86_64`
- [ ] **3.4** Build from Git (SCM method): `copr-cli build-from-scms --repo https://github.com/ai-space-lab/ibus-handwrite-chinese --spec packaging/ibus-handwrite-chinese.spec --method git`
- [ ] **3.5** Test install: `dnf copr enable mint/ibus-handwrite-chinese && dnf install ibus-handwrite-chinese`
- [ ] **3.6** (Optional) Submit to official Fedora repo via Bugzilla review request

### Phase 4: openSUSE OBS (Week 2)

- [ ] **4.1** Create openSUSE account
- [ ] **4.2** Create home project: `home:mint-user` on build.opensuse.org
- [ ] **4.3** Add package `ibus-handwrite-chinese` with spec file
- [ ] **4.3a** Option A: Use `_service` file to auto-fetch from GitHub releases
- [ ] **4.3b** Option B: Manual SRPM upload per release
- [ ] **4.4** Enable repos for: openSUSE Tumbleweed, Leap 15.6
- [ ] **4.5** Test install: `zypper ar -f https://download.opensuse.org/repositories/home:mint-user/openSUSE_Tumbleweed/ home:mint-user && zypper in ibus-handwrite-chinese`

### Phase 5: Flatpak (Week 2-3)

- [ ] **5.1** Create Flatpak manifest (`org.ibus_handwrite_chinese.yml`) with:
  - Runtime: `org.gnome.Platform//47` or `org.freedesktop.Platform//24.08`
  - SDK: matching SDK
  - Modules: python3, python3-evdev, python3-gobject, python3-numpy, ibus, onnxruntime (pip)
  - Finish-args: `--socket=wayland`, `--socket=x11`, `--device=all`, `--filesystem=host:ro`, `--talk-name=org.freedesktop.IBus`
- [ ] **5.2** Test build locally: `flatpak-builder --force-clean build-dir org.ibus_handwrite_chinese.yml`
- [ ] **5.3** Test run: `flatpak run org.ibus_handwrite_chinese`
- [ ] **5.4** Submit to Flathub: PR to flathub/flathub with manifest
- [ ] **5.5** CI: Add GitHub Action for automated Flatpak build on tag push

### Phase 6: Debian/Ubuntu PPA (Week 3-4, Optional)

- [ ] **6.1** Create Launchpad account, sign Ubuntu Code of Conduct
- [ ] **6.2** Create PPA: `ppa:mint/ibus-handwrite-chinese`
- [ ] **6.3** Prepare source package: `debuild -S -sa` (requires GPG key)
- [ ] **6.4** Upload: `dput ppa:mint/ibus-handwrite-chinese ../ibus-handwrite-chinese_0.6.0_source.changes`
- [ ] **6.5** Wait for build, test install on Ubuntu 22.04/24.04

### Phase 7: Nixpkgs (Week 3, Optional)

- [ ] **7.1** Create Nix derivation in local overlay
- [ ] **7.2** Test: `nix-build -A ibus-handwrite-chinese`
- [ ] **7.3** Submit PR to nixpkgs master branch

### Phase 8: Website & Documentation (Week 1, Parallel)

- [ ] **8.1** Create `mkdocs.yml` with material theme
- [ ] **8.2** Pages: Home, Install, Configuration, FAQ, Troubleshooting, Changelog
- [ ] **8.3** Deploy to GitHub Pages (`.github/workflows/pages.yml`)
- [ ] **8.4** Add badges to README: AUR, COPR, Flatpak, OBS, License, CI
- [ ] **8.5** Create `CONTRIBUTING.md` with packaging guidelines

### Phase 9: Community Announcement (Week 4)

- [ ] **9.1** Write bilingual announcement (English + Chinese)
- [ ] **9.2** Post to: r/linux, r/archlinux, r/Fedora, r/openSUSE, r/Ubuntu
- [ ] **9.3** Post to Chinese communities: Linux.cn, V2EX, 少数派, r/linuxcn
- [ ] **9.4** Add to IBus wiki: https://github.com/ibus/ibus/wiki/Engines
- [ ] **9.5** Add to ArchWiki "Input method" and "IBus" pages
- [ ] **9.6** Tweet / Mastodon / Bluesky announcement

### Phase 10: Automation & Maintenance (Ongoing)

- [ ] **10.1** Update release workflow to auto-generate checksums, update version in all packaging files
- [ ] **10.2** Add Renovate/Dependabot for dependency updates
- [ ] **10.3** Document release checklist in `RELEASE_CHECKLIST.md`
- [ ] **10.4** Set up monitoring: Repology, Repology badges in README

---

## 5. Must-NOT-Have (Scope Guardrails)

- ❌ No Fcitx5 port (out of scope - this is IBus-specific)
- ❌ No Windows/macOS support (evdev is Linux-only)
- ❌ No proprietary app store (Snap Store, Microsoft Store) - Flatpak only
- ❌ No GUI installer wizard (bootstrap.sh is sufficient)
- ❌ No binary signing infrastructure (GPG keys for now)

---

## 6. Acceptance Criteria (Per Channel)

| Channel | Done When |
|---------|-----------|
| AUR | `paru -S ibus-handwrite-chinese` installs and runs on clean Arch |
| COPR | `dnf copr enable ... && dnf install ibus-handwrite-chinese` works on Fedora 41/42 |
| OBS | `zypper ar ... && zypper in ibus-handwrite-chinese` works on Tumbleweed/Leap |
| Flatpak | `flatpak install flathub org.ibus_handwrite_chinese` works |
| PPA | `add-apt-repository ppa:... && apt install ibus-handwrite-chinese` works |
| Website | `https://ai-space-lab.github.io/ibus-handwrite-chinese/` loads with all pages |

---

## 7. QA Strategy (Per Task)

| Task | Test Command | Evidence |
|------|--------------|----------|
| AUR | `docker run --rm archlinux:latest bash -c "pacman -Sy --noconfirm git base-devel && git clone https://aur.archlinux.org/ibus-handwrite-chinese.git && cd ibus-handwrite-chinese && makepkg -si --noconfirm"` | Screenshot of `ibus engine handwrite-chinese` working |
| COPR | `docker run --rm fedora:41 bash -c "dnf copr enable mint/ibus-handwrite-chinese && dnf install -y ibus-handwrite-chinese"` | Build log + install log |
| OBS | `docker run --rm opensuse/tumbleweed bash -c "zypper ar ... && zypper in -y ibus-handwrite-chinese"` | Build log + install log |
| Flatpak | `flatpak-builder --force-clean build-dir manifest.yml && flatpak run org.ibus_handwrite_chinese --test` | Screenshot of preference dialog |
| Release workflow | Push tag `v0.6.1`, verify all artifacts uploaded | GitHub Release page |

---

## 8. Dependencies Matrix

```
1.1-1.4 (Repo Polish)
    ↓
2.1-2.6 (AUR) ← can start in parallel with 3.1-3.6
3.1-3.6 (Fedora COPR) ← can start in parallel with 2.1-2.6
    ↓
4.1-4.5 (openSUSE OBS)
    ↓
5.1-5.5 (Flatpak)
    ↓
6.1-6.5 (PPA) ── optional, parallel with 5.x
7.1-7.3 (Nixpkgs) ── optional, parallel with 5.x
    ↓
8.1-8.5 (Website) ── can start anytime after 1.1-1.4
    ↓
9.1-9.6 (Announcements) ── after all packages available
    ↓
10.1-10.4 (Automation) ── ongoing
```

---

## 9. Timeline Estimate

| Phase | Duration | Can Parallelize |
|-------|----------|-----------------|
| Repo Polish | 1 day | No |
| AUR | 1-2 days | With Fedora |
| Fedora COPR | 2-3 days | With AUR |
| openSUSE OBS | 2-3 days | After COPR |
| Flatpak | 3-5 days | After OBS |
| PPA | 5-10 days (review queue) | Optional, parallel |
| Nixpkgs | 3-5 days | Optional, parallel |
| Website | 2 days | Anytime after polish |
| Announcements | 1 day | After all packages live |
| **Total (critical path)** | **~2-3 weeks** | |

---

## 10. Final Verification Wave

- [ ] **F1** All 5 primary channels (AUR, COPR, OBS, Flatpak, GitHub Release) install successfully on clean VMs
- [ ] **F2** Engine starts, preference dialog opens (`--setup`), model downloads, recognition works
- [ ] **F3** Website loads with correct install instructions for each distro
- [ ] **F4** Repology shows green for all channels
- [ ] **F5** Announcement posts live with correct links

---

## 11. Approval Gate

**Status**: `awaiting-approval`

**Next Action**: Please confirm:
1. Your choices for the 8 owner decisions above
2. Whether to include optional channels (PPA, Nixpkgs)
3. Whether to pursue official Fedora/openSUSE repo inclusion (vs COPR/OBS home only)
4. Approval to proceed with plan creation

Once approved, I'll create the final `.omo/plans/distribute-world.md` with task batches appended.