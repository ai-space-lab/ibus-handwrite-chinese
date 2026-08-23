"""
PP-OCRv6 ONNX model and dictionary downloader.

Downloads the PP-OCRv6 recognition model (ONNX) and character dictionary
from HuggingFace (primary) with hf-mirror.com fallback, verifies SHA256,
and stores them at configurable paths.

Usage (via config dict):
    from handwrite_model_download import ensure_model
    model_path, dict_path = ensure_model(config["model"])

Public functions:
    ensure_model(config) -> tuple[str, str]
        Download model+dictionary if missing. Returns (model_path, dict_path).

    check_existing(download_path, tier) -> tuple[bool, bool]
        Return (model_exists, dict_exists) for the given tier.

    model_info(download_path, tier) -> dict
        Return metadata dict about downloaded files.
"""

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

# Valid model tiers (must match install.sh / postinst validation)
VALID_TIERS = frozenset({"tiny", "small", "medium"})

# Default tier fallback
DEFAULT_TIER = "small"

# Output filenames (same as install.sh / postinst)
MODEL_OUTPUT = "ppocrv6_{tier}_rec.onnx"
DICT_OUTPUT = "dict_v6.txt"

# URL templates (primary and fallback)
MODEL_URL_PRIMARY = (
    "https://huggingface.co/PaddlePaddle/"
    "PP-OCRv6_{tier}_rec_onnx/resolve/main/inference.onnx"
)
MODEL_URL_FALLBACK = (
    "https://hf-mirror.com/PaddlePaddle/"
    "PP-OCRv6_{tier}_rec_onnx/resolve/main/inference.onnx"
)
DICT_URL_PRIMARY = (
    "https://raw.githubusercontent.com/"
    "PaddlePaddle/PaddleOCR/main/ppocr/utils/dict/ppocrv6_dict.txt"
)
DICT_URL_FALLBACK = (
    "https://cdn.jsdelivr.net/gh/"
    "PaddlePaddle/PaddleOCR@main/ppocr/utils/dict/ppocrv6_dict.txt"
)

# Path to checksums file (resolved relative to this module's location)
_CHECKSUMS_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "models",
        "checksums.sha256",
    )
)


# ---------------------------------------------------------------------------
# SHA256 helpers
# ---------------------------------------------------------------------------

def _load_checksums(checksums_path=None):
    """Parse checksums.sha256 into {filename: hex_hash}.

    Returns empty dict if the file is missing (graceful skip, matching the
    shell behaviour: ``[ -f "$CHECKSUMS_FILE" ] || return 0``).
    """
    path = checksums_path or _CHECKSUMS_PATH
    if not os.path.isfile(path):
        logger.debug("Checksums file not found at %s — skipping verification", path)
        return {}
    checksums = {}
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            # Format: "<hash>  <filename>" (two spaces)
            parts = line.split(None, 1)
            if len(parts) == 2:
                checksums[parts[1]] = parts[0]
    logger.debug("Loaded %d checksum(s) from %s", len(checksums), path)
    return checksums


def _sha256_of(path):
    """Compute SHA256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(65536)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _verify_sha256(file_path, expected_filename, checksums):
    """Verify *file_path* against *expected_filename* in *checksums* dict.

    Returns True if:
      - checksums dict is empty (graceful skip)
      - expected_filename not in checksums (graceful skip)
      - hash matches

    Returns False (and logs error) if hash mismatches.
    """
    if not checksums:
        return True  # no checksums file → skip
    expected_hash = checksums.get(expected_filename)
    if expected_hash is None:
        logger.debug("No checksum entry for %s — skipping verification", expected_filename)
        return True
    actual_hash = _sha256_of(file_path)
    if actual_hash != expected_hash:
        logger.error(
            "SHA256 mismatch for %s\n"
            "  Expected: %s\n"
            "  Actual:   %s\n"
            "  The downloaded file is corrupted or has been tampered with.",
            expected_filename,
            expected_hash,
            actual_hash,
        )
        return False
    logger.info("SHA256 OK: %s", expected_filename)
    return True


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def _download_with_fallback(primary_url, fallback_url, output_path, timeout, desc):
    """Download *output_path* from *primary_url*, falling back to *fallback_url*.

    *timeout* is the per-URL timeout in seconds (fallback gets 2× timeout).
    Returns True on success, False if both URLs fail.
    """
    for attempt, (url, to) in enumerate(
        [(primary_url, timeout), (fallback_url, timeout * 2)], 1
    ):
        try:
            logger.info("Downloading %s from %s (timeout=%ds)", desc, url, to)
            _urlretrieve(url, output_path, timeout=to)
            logger.info("Downloaded %s successfully", desc)
            return True
        except Exception as exc:
            if attempt == 1:
                logger.warning(
                    "Primary download failed for %s: %s — trying fallback...",
                    desc,
                    exc,
                )
            else:
                logger.error(
                    "Fallback download also failed for %s: %s", desc, exc
                )
    return False


def _urlretrieve(url, path, timeout=30):
    """Download *url* to *path* with urllib. Raises on failure."""
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "ibus-handwrite-chinese/1.0")]
    data = opener.open(url, timeout=timeout).read()
    with open(path, "wb") as fh:
        fh.write(data)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _move_to_target(src: str, dst: str) -> None:
    """Move src to dst, retrying with pkexec on PermissionError."""
    try:
        shutil.move(src, dst)
    except PermissionError:
        logger.info("Target directory not writable, elevating via pkexec...")
        result = subprocess.run(
            ["pkexec", "cp", src, dst],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Cannot write to {os.path.dirname(dst)}. "
                f"Run the preference dialog with admin privileges, "
                f"or install manually via: sudo ./tools/install.sh"
            )
        # Verify the file was actually copied (pkexec might have been dismissed)
        if not os.path.isfile(dst):
            raise RuntimeError(
                f"Failed to copy {src} to {dst}. "
                f"Please run: sudo cp {src} {dst}"
            )


def check_existing(download_path, tier):
    """Check whether model and dictionary files already exist.

    Args:
        download_path: Directory containing the downloaded files.
        tier: Model tier (tiny, small, medium).

    Returns:
        (model_exists, dict_exists) tuple of booleans.
    """
    model_path = os.path.join(download_path, MODEL_OUTPUT.format(tier=tier))
    dict_path = os.path.join(download_path, DICT_OUTPUT)
    return (os.path.isfile(model_path), os.path.isfile(dict_path))


def ensure_model(config):
    """Download model and dictionary if missing.

    Reads these keys from *config* dict (matching handwrite_config.py's
    ``model`` section):

        tier              – Model tier (tiny / small / medium).
        download_path     – Directory to store downloaded files.
        auto_download     – If False, raise RuntimeError instead of downloading.
        download_timeout  – Per-URL timeout in seconds (fallback gets 2×).

    Args:
        config: dict with model configuration keys.

    Returns:
        (model_path, dict_path) tuple of absolute paths to existing files.

    Raises:
        RuntimeError: If files are missing and auto_download is False,
            or if all download/verification attempts fail.
    """
    tier = config.get("tier", DEFAULT_TIER)
    if tier not in VALID_TIERS:
        logger.warning(
            "Unknown PP-OCRv6 model tier '%s'. "
            "Valid: %s. Defaulting to '%s'.",
            tier,
            ", ".join(sorted(VALID_TIERS)),
            DEFAULT_TIER,
        )
        tier = DEFAULT_TIER

    download_path = config.get(
        "download_path", "/usr/local/share/ibus-handwrite-chinese/models"
    )
    auto_download = config.get("auto_download", True)
    timeout = config.get("download_timeout", 30)

    model_path = os.path.join(download_path, MODEL_OUTPUT.format(tier=tier))
    dict_path = os.path.join(download_path, DICT_OUTPUT)

    model_exists, dict_exists = os.path.isfile(model_path), os.path.isfile(dict_path)

    if model_exists and dict_exists:
        logger.info(
            "PP-OCRv6 %s model already installed at %s", tier, download_path
        )
        return (model_path, dict_path)

    if not auto_download:
        missing = []
        if not model_exists:
            missing.append(
                MODEL_OUTPUT.format(tier=tier)
            )
        if not dict_exists:
            missing.append(DICT_OUTPUT)
        raise RuntimeError(
            "PP-OCRv6 model files not found at '{}'. "
            "Missing: {}. "
            "Please download manually from "
            "https://huggingface.co/PaddlePaddle/PP-OCRv6_{}_rec_onnx "
            "and place files in '{}', "
            "or set auto_download=True in config.".format(
                download_path,
                ", ".join(missing),
                tier,
                download_path,
            )
        )

    # Ensure target directory exists
    os.makedirs(download_path, exist_ok=True)

    # Load checksums once
    checksums = _load_checksums()

    # We use a temporary directory for atomic writes: download to temp file
    # in the same filesystem, verify, then rename into place.
    tmpdir = tempfile.mkdtemp()
    try:
        ok = True

        if not model_exists:
            tmp_model = os.path.join(tmpdir, "inference.onnx")
            if not _download_with_fallback(
                MODEL_URL_PRIMARY.format(tier=tier),
                MODEL_URL_FALLBACK.format(tier=tier),
                tmp_model,
                timeout,
                "PP-OCRv6 {} model".format(tier),
            ):
                ok = False
                logger.error(
                    "Failed to download PP-OCRv6 %s model (primary and fallback)", tier
                )
            elif not _verify_sha256(
                tmp_model, MODEL_OUTPUT.format(tier=tier), checksums
            ):
                ok = False
                logger.error(
                    "PP-OCRv6 %s model integrity check failed — aborting", tier
                )
            else:
                _move_to_target(tmp_model, model_path)
                logger.info("PP-OCRv6 %s model downloaded to %s", tier, model_path)

        if not dict_exists:
            tmp_dict = os.path.join(tmpdir, "dict.txt")
            if not _download_with_fallback(
                DICT_URL_PRIMARY,
                DICT_URL_FALLBACK,
                tmp_dict,
                timeout,
                "PP-OCRv6 dictionary",
            ):
                ok = False
                logger.error(
                    "Failed to download PP-OCRv6 dictionary (primary and fallback)"
                )
            elif not _verify_sha256(tmp_dict, DICT_OUTPUT, checksums):
                ok = False
                logger.error("PP-OCRv6 dictionary integrity check failed — aborting")
            else:
                _move_to_target(tmp_dict, dict_path)
                logger.info("PP-OCRv6 dictionary downloaded to %s", dict_path)

        if not ok:
            raise RuntimeError(
                "PP-OCRv6 model download failed. "
                "See log above for details. "
                "Manual download: https://huggingface.co/PaddlePaddle/"
                "PP-OCRv6_{}_rec_onnx".format(tier)
            )

        return (model_path, dict_path)

    finally:
        # Clean up temporary directory
        for fname in os.listdir(tmpdir):
            fpath = os.path.join(tmpdir, fname)
            try:
                os.remove(fpath)
            except OSError:
                pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


def model_info(download_path, tier):
    """Return metadata about downloaded model and dictionary files.

    Args:
        download_path: Directory containing the downloaded files.
        tier: Model tier (tiny, small, medium).

    Returns:
        dict with keys:
            model_size_mb  – size of model file in MB (float), or 0 if missing.
            dict_lines     – number of lines in dictionary (int), or 0.
            model_exists   – bool.
            dict_exists    – bool.
            last_modified  – ISO-8601 string of model mtime, or None.
    """
    model_path = os.path.join(download_path, MODEL_OUTPUT.format(tier=tier))
    dict_path = os.path.join(download_path, DICT_OUTPUT)

    model_exists = os.path.isfile(model_path)
    dict_exists = os.path.isfile(dict_path)

    model_size_mb = 0.0
    last_modified = None
    if model_exists:
        st = os.stat(model_path)
        model_size_mb = st.st_size / (1024.0 * 1024.0)
        last_modified = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)
        )

    dict_lines = 0
    if dict_exists:
        with open(dict_path, "r") as fh:
            dict_lines = sum(1 for _ in fh)

    return {
        "model_size_mb": round(model_size_mb, 2),
        "dict_lines": dict_lines,
        "model_exists": model_exists,
        "dict_exists": dict_exists,
        "last_modified": last_modified,
    }
