# Task 2: CD-ROM apt source reproduction

## Summary

Recreated `/var/lib/apt/cdroms.list` with the original Mint installer CD-ROM entry and tested
whether it causes `apt update` to fail. The results confirm an important nuance about the root cause.

## Findings

### `apt update` result: SUCCESS (no error)

Even with `/var/lib/apt/cdroms.list` present containing the CD-ROM identifier:
```
CD::0c06d058567b95b94af55b76555d29d3-2 "Linux Mint 22.3 _Zena_ - Release amd64 20260108";
CD::0c06d058567b95b94af55b76555d29d3-2::Label "Linux Mint 22.3 _Zena_ - Release amd64 20260108";
```

`sudo apt update` completed successfully. The cdroms.list file alone is **not sufficient** to
trigger the CD-ROM error.

### `bootstrap.sh` result: PROCEEDED past apt update, began installation

Since apt update succeeded, bootstrap.sh (which has `set -e`) continued normally through
dependency installation and began the full install workflow. It was externally terminated
by timeout during the onnxruntime venv creation step — not by a CD-ROM error.

### Root cause confirmed

The actual root cause of the original bug requires a `deb cdrom:` source line in
`/etc/apt/sources.list` or `/etc/apt/sources.list.d/`. That line was already cleaned
up in a previous fix, so the cdroms.list file on its own is harmless.

### Cleanup

`/var/lib/apt/cdroms.list` was deleted after testing.

## Evidence Files

- `apt-error.txt` — stdout/stderr from `sudo apt update` (no error, successful update)
- `bootstrap-error.txt` — partial output from bootstrap.sh before timeout termination
