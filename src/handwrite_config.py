"""
Configuration loader for ibus-handwrite-chinese.

Loads settings from TOML config file (XDG_CONFIG_HOME/ibus-handwrite-chinese/config.toml),
with IBUS_HANDWRITE_* env var overrides. Pure stdlib — no GTK/IBus dependency.
"""

import copy
import os
import subprocess
import sys

# TOML parsing: Python 3.11+ has tomllib, older needs tomli backport
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # pip-installable backport
    except ModuleNotFoundError:
        tomllib = None  # No TOML support — defaults only, no config file

DEFAULT_CONFIG = {
    "general": {
        "theme": "dark",       # "auto" | "dark" | "light"
        "log_level": "INFO",
        "log_path": "/tmp/ppocr-recognition.log",
        "log_max_mb": 5,
    },
    "model": {
        "tier": "small",       # tiny | small | medium
        "path": "",            # explicit model .onnx path (empty = auto-detect)
        "dict_path": "",       # explicit dict .txt path (empty = auto-detect)
    },
    "engine": {
        "stroke_width": 8,
        "max_strokes": 128,
        "page_size": 8,
        "max_candidates": 24,
        "min_redraw_ms": 16,
        "momentum_decay": 0.65,
        "momentum_threshold": 0.3,
        "momentum_tick_ms": 50,
        "auto_pause_debounce_ms": 50,
        "delete_hold_ms": 500,
    },
    "window": {
        "width": 400,
        "height": 360,
        "drawing_height": 300,
        "drag_handle_height": 24,
        "candidate_button_width": 36,
    },
    "user_dict": {
        "enabled": True,
        "boost_strength": 1.5,
        "max_entries": 10000,
    },
}

# Env var → config path mapping
ENV_MAP = {
    "IBUS_HANDWRITE_THEME": ("general", "theme"),
    "IBUS_HANDWRITE_LOG_LEVEL": ("general", "log_level"),
    "IBUS_HANDWRITE_LOG_PATH": ("general", "log_path"),
    "IBUS_HANDWRITE_PPOCR_MODEL": ("model", "tier"),
    "IBUS_HANDWRITE_PPOCR_MODEL_PATH": ("model", "path"),
    "IBUS_HANDWRITE_PPOCR_DICT_PATH": ("model", "dict_path"),
    "IBUS_HANDWRITE_STROKE_WIDTH": ("engine", "stroke_width"),
}

# Config keys that expect integer values
_INT_KEYS = frozenset({
    "stroke_width", "max_candidates", "max_strokes", "page_size",
    "min_redraw_ms", "momentum_tick_ms", "auto_pause_debounce_ms",
    "delete_hold_ms", "width", "height", "drawing_height",
    "drag_handle_height", "candidate_button_width", "log_max_mb",
    "max_entries",
})

# Config keys that expect float values
_FLOAT_KEYS = frozenset({
    "momentum_decay", "momentum_threshold", "boost_strength",
})


def detect_system_theme() -> str:
    """Detect system theme via DE tools and env vars. Returns 'dark' or 'light'."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    if "gnome" in desktop or "unity" in desktop:
        try:
            # color-scheme: 'default' = light, 'prefer-dark' = dark, 'prefer-light' = light
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                val = result.stdout.strip().strip("'")
                if "dark" in val:
                    return "dark"
                if "light" in val or val == "default":
                    return "light"
            # Fallback: check gtk-theme for "dark" substring
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                theme_name = result.stdout.strip().strip("'")
                if "dark" in theme_name.lower():
                    return "dark"
                return "light"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    if "kde" in desktop or "plasma" in desktop:
        try:
            kdeglobals = os.path.expanduser("~/.config/kdeglobals")
            result = subprocess.run(
                ["kreadconfig5", "--file", kdeglobals, "--group", "General",
                 "--key", "ColorScheme"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0:
                scheme = result.stdout.strip()
                if "dark" in scheme.lower():
                    return "dark"
                return "light"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Env var fallback
    gtk_theme = os.environ.get("GTK_THEME", "")
    if gtk_theme:
        return "dark" if "dark" in gtk_theme.lower() else "light"

    # Default: dark (safe — current behavior for unknown environments)
    return "dark"


def _deep_merge(base, override):
    """Recursively merge override dict into base dict (in-place on base)."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def load_config():
    """Load config from TOML file + env var overrides.

    Reads from $XDG_CONFIG_HOME/ibus-handwrite-chinese/config.toml
    (defaults to ~/.config/ibus-handwrite-chinese/config.toml).
    Falls back to DEFAULT_CONFIG silently if:
      - file missing
      - file unreadable
      - tomllib/tomli unavailable
    Always applies env var overrides last.
    """
    config = copy.deepcopy(DEFAULT_CONFIG)

    # Try TOML config file
    if tomllib is not None:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if not xdg_config:
            xdg_config = os.path.expanduser("~/.config")
        config_path = os.path.join(xdg_config, "ibus-handwrite-chinese", "config.toml")
        if os.path.isfile(config_path):
            try:
                with open(config_path, "rb") as f:
                    file_config = tomllib.load(f)
                _deep_merge(config, file_config)
            except Exception:
                print(f"  [config] Warning: failed to parse {config_path}, using defaults",
                      file=sys.stderr)

    # Apply env var overrides
    apply_env_overrides(config)

    # Resolve "auto" theme via system detection
    if config["general"]["theme"] == "auto":
        config["general"]["theme"] = detect_system_theme()

    return config


def apply_env_overrides(config):
    """Override config values from IBUS_HANDWRITE_* env vars (in-place)."""
    for env_var, (section, key) in ENV_MAP.items():
        value = os.environ.get(env_var)
        if value is None:
            continue
        if section not in config:
            config[section] = {}
        if key in _INT_KEYS:
            try:
                config[section][key] = int(value)
            except ValueError:
                print(f"  [config] Warning: {env_var}={value} is not a valid integer, ignoring",
                      file=sys.stderr)
        elif key in _FLOAT_KEYS:
            try:
                config[section][key] = float(value)
            except ValueError:
                print(f"  [config] Warning: {env_var}={value} is not a valid float, ignoring",
                      file=sys.stderr)
        else:
            config[section][key] = value


def get_theme_css(theme, scale=1):
    """Return CSS bytes for the given theme name ('dark' or 'light').

    Falls back to dark theme for unknown values.
    ``scale`` is the HiDPI scale factor (typically 1 or 2) used
    to multiply all pixel-based CSS values.
    """
    fs_cand = int(15 * scale)
    mw_cand = int(32 * scale)
    mh_cand = int(28 * scale)
    fs_del = int(16 * scale)
    fs_close = int(18 * scale)
    mw_close = int(28 * scale)
    mh_close = int(28 * scale)

    if theme == "light":
        return f"""
            window {{
                background-color: rgba(245, 245, 245, 0.95);
                border-radius: 8px;
            }}
            .candidate-btn {{
                background: transparent;
                color: #333;
                font-size: {fs_cand}px;
                font-weight: bold;
                border: none;
                padding: 4px 6px;
                min-width: {mw_cand}px;
                min-height: {mh_cand}px;
            }}
            .candidate-btn:hover {{
                background: rgba(0, 0, 0, 0.08);
                border-radius: 4px;
            }}
            .delete-btn {{
                background: transparent;
                color: #666;
                font-size: {fs_del}px;
                border: none;
                padding: 2px 12px;
                min-height: {mh_cand}px;
            }}
            .delete-btn:hover {{
                color: #e74c3c;
            }}
            .close-btn {{
                background: transparent;
                color: #666;
                font-size: {fs_close}px;
                font-weight: bold;
                border: none;
                padding: 2px 8px;
                min-width: {mw_close}px;
                min-height: {mh_close}px;
            }}
            .close-btn:hover {{
                color: #e74c3c;
            }}
            .candidate-btn-highlighted {{
                background: #4a90d9;
                color: white;
                border-radius: 3px;
            }}
        """.encode()
    # Default: dark theme (current behavior)
    return f"""
        window {{
            background-color: rgba(40, 40, 45, 0.92);
            border-radius: 8px;
        }}
        .candidate-btn {{
            background: transparent;
            color: white;
            font-size: {fs_cand}px;
            font-weight: bold;
            border: none;
            padding: 4px 6px;
            min-width: {mw_cand}px;
            min-height: {mh_cand}px;
        }}
        .candidate-btn:hover {{
            background: rgba(255, 255, 255, 0.12);
            border-radius: 4px;
        }}
        .delete-btn {{
            background: transparent;
            color: #999;
            font-size: {fs_del}px;
            border: none;
            padding: 2px 12px;
            min-height: {mh_cand}px;
        }}
        .delete-btn:hover {{
            color: white;
        }}
        .close-btn {{
            background: transparent;
            color: #999;
            font-size: {fs_close}px;
            font-weight: bold;
            border: none;
            padding: 2px 8px;
            min-width: {mw_close}px;
            min-height: {mh_close}px;
        }}
        .close-btn:hover {{
            color: white;
        }}
        .candidate-btn-highlighted {{
            background: #4a90d9;
            color: white;
            border-radius: 3px;
        }}
    """.encode()
