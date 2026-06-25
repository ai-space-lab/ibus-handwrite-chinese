# Copilot instructions for ibus-handwrite-chinese

When fixing reported issues in this repository:

- Prefer minimal, surgical changes that directly address the reported issue.
- Preserve existing behavior unless the issue requires a behavior change.
- Follow the existing Python, GTK, IBus, and shell script style.
- Do not introduce speculative features or broad refactors.
- Do not store third-party handwriting models in the repository or GitHub Releases.
- When touching CI/CD, keep normal CI separate from release publishing.
- When touching cursor/input behavior, restore cursor and input state on all exit paths.
- When touching tests, keep tests focused on the behavior being verified.

Before proposing a fix, prefer checks that match the changed area:

```bash
git diff --check
python3 -c "compile(open('src/ibus-engine-handwrite-chinese').read(), 'engine', 'exec')"
python3 -c "compile(open('src/handwrite_evdev.py').read(), 'evdev', 'exec')"
```

If GTK code or tests changed, also run:

```bash
xvfb-run -a python3 tests/test_gtk_write_phrase.py
```

If shell scripts or IBus XML changed, also run:

```bash
shellcheck -e SC1091 bootstrap.sh tools/install.sh tools/restore.sh
xmllint --noout xml/handwrite-chinese.xml
```
