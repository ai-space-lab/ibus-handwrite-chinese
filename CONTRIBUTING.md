# Contributing

## Dev Environment Setup

Clone the repo and install dependencies:

```bash
git clone https://github.com/ai-space-lab/ibus-handwrite-chinese
cd ibus-handwrite-chinese
./tools/install.sh --skip-deps  # system install for deps only
```

The `--skip-deps` flag installs the engine files, creates the onnxruntime venv,
and sets up the IBus component without re-installing system packages.

For a full automatic install across distros, use:

```bash
./bootstrap.sh
```

See **README.md** for end-user install instructions, distro requirements, and
troubleshooting.

## How to Run Tests

### Python Syntax Checks

```bash
python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
python3 -c "compile(open('src/handwrite_evdev.py').read(), 'evdev', 'exec')"
```

### Lint

```bash
shellcheck -e SC1091 tools/install.sh tools/restore.sh bootstrap.sh
xmllint --noout xml/handwrite-chinese.xml
```

### GTK Tests (requires Xvfb or display)

```bash
xvfb-run -a python3 tests/test_esc_key_routing.py
xvfb-run -a python3 tests/test_gtk_write_phrase.py
```

### Recognition Smoke Test

```bash
python3 tests/test_recognition.py
```

This creates synthetic strokes (horizontal line and cross shape) and verifies
that the PP-OCRv6 model recognizes them as **一** and **十** with high confidence.

### Quick Pre-Commit Check

```bash
git diff --check
shellcheck -e SC1091 bootstrap.sh tools/install.sh tools/restore.sh
xmllint --noout xml/handwrite-chinese.xml
python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
python3 -c "compile(open('src/handwrite_evdev.py').read(), 'evdev', 'exec')"
```

See **README.md** for details on CI workflows and manual test environment.

## Code Style

### Python

- Follow PEP 8 (ruff/flake8 compatible)
- No bare `except:`. If you must catch broadly, include a comment explaining why
- No silent `except Exception:` without logging or a documented reason
- Prefer structural pattern matching over if/elif chains when matching on shape
- Keep functions focused and under 50 lines where possible
- Use type hints for function signatures (stdlib types only; no typing imports
  that require external packages)

### Shell

- All shell scripts pass `shellcheck -e SC1091`
- Use `set -euo pipefail` in install scripts
- Quote all variable expansions

### XML

- All XML files pass `xmllint --noout`

## PR Workflow

1. **Branch from `main`**: name branches meaningfully (e.g., `fix/esc-firefox`,
   `feat/multi-char`)
2. **Atomic commits per logical change**. Each commit should compile and pass
   syntax checks
3. **Run pre-commit checks** (see above) before opening a PR
4. **CI must pass**: the CI workflow runs on every push/PR across 5 distro
   containers (Debian, Ubuntu, Fedora, Arch, openSUSE). It checks syntax,
   lint, install, and GTK tests
5. **Each wave ships via its own branch + tag**: releases follow a version tag
   pattern (`v0.6.0`, `v0.7.0`, `v0.8.0`). Tag pushes trigger the release
   workflow that builds `.deb`, `.rpm`, and source tarball
6. **Keep PRs focused**: one feature or fix per PR. Large changes should be
   broken into logical waves

## How to Add a New Test

1. Place the test file in `tests/`
2. Name it with a `test_` prefix (e.g., `test_candidate_selection.py`)
3. Use Python assertions for pass/fail
4. If the test needs GTK, wrap it with `xvfb-run -a` in CI
5. If the test needs a trackpad device (unavailable in CI), guard it with
   a hardware check or skip condition
6. Register the test in `.github/workflows/ci.yml` if it should run in CI

Example test structure:

```python
"""Test candidate selection logic."""
import sys
sys.path.insert(0, 'src')
import handwrite_evdev

def test_tap_detection():
    reader = handwrite_evdev.TrackpadReader({})
    assert reader is not None
```

## How to Build Packages Locally

```bash
# .deb (requires dpkg-dev, fakeroot)
bash packaging/build-deb.sh 0.8.0

# .rpm (requires rpm-build)
bash packaging/build-rpm.sh 0.8.0

# Source tarball (as done in CI)
tar --exclude='.git' --exclude='__pycache__' \
    --exclude='.venv' --exclude='.omo' --exclude='models' \
    -czf ibus-handwrite-chinese-0.8.0.tar.gz \
    src xml icons tools packaging models \
    bootstrap.sh VERSION README.md \
    README.zh-Hans-汉.md README.zh-Hant-漢.md LICENSE
```

The `.deb` and `.rpm` builders copy files into a staging directory and invoke
`dpkg-deb --build` / `rpmbuild` respectively. Both are used by the CI release
workflow and produce packages ready for distribution.

## Adding a Language Variant of README

The project maintains Chinese translations of the README (`README.zh-Hans-汉.md`
and `README.zh-Hant-漢.md`). To add a new translation:

1. Copy the English `README.md` to `README.<locale>.md`
2. Translate the content, keeping the same structure and section headings
3. Add a language link in the English README's header
4. Include the file in release tarball packaging

## License

GPLv3. By contributing you agree to license your contributions under GPLv3.
