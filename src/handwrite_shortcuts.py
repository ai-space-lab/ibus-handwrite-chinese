"""
Config-driven keybinding lookup for the IBus handwriting engine.

Bridges Gdk key name strings and IBus keyval integers for the two key
handling paths in ibus-engine-handwrite-chinese:

  1. GTK path  (HandwriteWin.on_key):
       Gdk.keyval_name(ev.get_keyval()[1])  → "Escape"
       lookup_action(name)                  → "escape"

  2. IBus path (HandwriteEngine.do_process_key_event):
       raw keyval int 65307 + state bitmask
       lookup_ibus_action(keyval, state)    → "escape"

Supports simple keys ("Escape", "Return") and composite keys with modifier
prefixes in GTK accelerator notation ("<Control><Shift>T").

Usage:
    from handwrite_shortcuts import load_bindings, lookup_action

    config = {"shortcuts": {"escape": "Escape", "cycle_theme": "<Control><Shift>T"}}
    load_bindings(config.get("shortcuts", {}))

    action = lookup_action("Escape")               # → "escape"
    action = lookup_ibus_action(65307, 0)           # → "escape"
    action = lookup_ibus_action(0x0074, 4 | 1)       # → "cycle_theme"
"""

import threading
import functools

# ── X11 keysym values ──────────────────────────────────────────────────────
# Common keys use the same values in both Gdk and IBus (X11 keysyms).
_KEYVALS = {
    "Escape": 0xFF1B,      # 65307
    "Return": 0xFF0D,      # 65293
    "BackSpace": 0xFF08,   # 65288
    "Left": 0xFF51,        # 65361
    "Right": 0xFF53,       # 65363
    "t": 0x0074,           # 116
    "s": 0x0073,           # 115
    "T": 0x0054,           # 84
    "S": 0x0053,           # 83
}

# ── IBus.ModifierType masks ────────────────────────────────────────────────
_MOD_MASK_SHIFT   = 1 << 0
_MOD_MASK_CONTROL = 1 << 2
_MOD_MASK_ALT     = 1 << 3  # MOD1
_MOD_MASK_SUPER   = 1 << 6  # MOD4

_VALID_MODIFIERS = {
    "Control": _MOD_MASK_CONTROL,
    "Shift": _MOD_MASK_SHIFT,
    "Alt": _MOD_MASK_ALT,
    "Super": _MOD_MASK_SUPER,
}

# ── Display-name overrides ─────────────────────────────────────────────────
_DISPLAY_NAMES = {
    "Escape": "Esc",
    "Return": "Enter",
    "BackSpace": "Backspace",
}

# ── Internal state (populated by load_bindings) ────────────────────────────
_bindings = {}                     # action → raw key string
_keyname_to_action = {}            # "Escape"               → "escape"
_keyval_to_action = {}             # 65307                  → "escape"
_composite_bindings = []           # [(keyval, mod_mask, action)]
_lock = threading.Lock()
_bindings_loaded = False


# ── Public API ─────────────────────────────────────────────────────────────

def load_bindings(config_shortcuts):
    """Parse and normalise shortcut config into internal lookup tables.

    Args:
        config_shortcuts: dict mapping action names to key strings, e.g.
            {"escape": "Escape", "cycle_theme": "<Control><Shift>T"}.

    Returns:
        The normalised bindings dict (action → key_string).
    """
    global _bindings, _keyname_to_action, _keyval_to_action
    global _composite_bindings, _bindings_loaded

    parsed = {}
    for action, key_string in config_shortcuts.items():
        parsed[action] = key_string.strip()

    with _lock:
        _bindings = parsed
        _keyname_to_action = {}
        _keyval_to_action = {}
        _composite_bindings = []
        _rebuild_tables()
        _bindings_loaded = True

    # Invalidate caches so stale entries are not returned after a reload.
    lookup_action.cache_clear()
    lookup_ibus_action.cache_clear()

    return dict(_bindings)


@functools.lru_cache(maxsize=128)
def lookup_action(keyval_name, modifiers=0):
    """Look up an action by Gdk key name string (GTK path).

    Args:
        keyval_name: Gdk key name string (e.g. ``"Escape"``, ``"Return"``).
        modifiers:   Optional IBus modifier bitmask (reserved for composite
                     key support in the GTK path; ignored for simple keys).

    Returns:
        Action string (e.g. ``"escape"``) or *None* if not bound.
    """
    if not _bindings_loaded:
        return None
    with _lock:
        return _keyname_to_action.get(keyval_name)


@functools.lru_cache(maxsize=128)
def lookup_ibus_action(keyval, state=0):
    """Look up an action by IBus keyval integer and modifier state (IBus path).

    Simple keys (no modifiers required) are checked first, then composite
    bindings that require a modifier combination.

    Args:
        keyval: IBus keyval integer (e.g. 65307 for Escape).
        state:  IBus modifier state bitmask.

    Returns:
        Action string (e.g. ``"escape"``) or *None* if not bound.
    """
    if not _bindings_loaded:
        return None

    # 1. Simple key (exact match, no modifiers required).
    with _lock:
        if keyval in _keyval_to_action:
            return _keyval_to_action[keyval]

    # 2. Composite key (keyval + required modifiers must all be present).
    mod_mask = _extract_modifiers(state)
    with _lock:
        for kv, req_mod, action in _composite_bindings:
            if kv == keyval and (mod_mask & req_mod) == req_mod:
                return action

    return None


def get_default_bindings():
    """Return the default shortcut map.

    Returns:
        A dict mapping each action name to its default key string, suitable
        for passing to :func:`load_bindings` or for a "Reset to Defaults"
        button in the preferences dialog.
    """
    return {
        "escape": "Escape",
        "commit": "Return",
        "delete_stroke": "BackSpace",
        "page_up": "Left",
        "page_down": "Right",
        "cycle_theme": "<Control><Shift>T",
        "open_settings": "<Control><Shift>S",
    }


def validate_binding(key_string):
    """Validate a user-entered key binding string.

    Checks performed:
        * Not empty.
        * All modifier names are recognised (Control, Shift, Alt, Super).
        * A single key name follows the modifiers (no sequences).
        * The key name is a known key or a single printable ASCII character.

    Args:
        key_string: Raw key binding string to validate.

    Returns:
        *None* if valid, or an error message string describing the problem.
    """
    key_string = key_string.strip()
    if not key_string:
        return "Key binding cannot be empty."

    # Check for unknown modifier names before the parser silently skips them.
    rest = key_string
    while rest.startswith("<"):
        closing = rest.find(">")
        if closing == -1:
            return "Malformed modifier: missing closing '>'."
        mod_name = rest[1:closing]
        if mod_name not in _VALID_MODIFIERS:
            return (
                f"Unknown modifier: '{mod_name}'. "
                f"Valid modifiers: {', '.join(sorted(_VALID_MODIFIERS))}."
            )
        rest = rest[closing + 1:]

    key_name = rest

    if not key_name:
        return "Key binding must include a key after modifiers."

    # Ensure it is a single key, not a sequence (no spaces, plus signs, etc.
    # that would indicate multiple keys).
    if len(key_name) > 1 and key_name not in _KEYVALS:
        # A multi-character token that isn't a known key name is suspect.
        # Single ASCII letters are always valid (catch single chars above).
        return (
            f"Unknown key: '{key_name}'. "
            f"Use a standard key name (e.g. Escape, Return, BackSpace) "
            f"or a single letter."
        )

    keyval = _resolve_keyval(key_name)
    if keyval is None:
        return f"Unrecognised key: '{key_name}'."

    return None


def format_for_display(action, bindings):
    """Format a shortcut action for human-readable display.

    Converts internal key strings to user-friendly labels::

        "<Control><Shift>T"  →  "Ctrl+Shift+T"
        "Escape"             →  "Esc"
        "Return"             →  "Enter"
        "BackSpace"          →  "Backspace"

    Args:
        action:   Action name (e.g. ``"escape"``, ``"cycle_theme"``).
        bindings: The bindings dict (action → key string).

    Returns:
        Formatted display string, or ``""`` if the action has no binding.
    """
    key_string = bindings.get(action)
    if not key_string:
        return ""

    modifiers, key_name = _parse_key_string(key_string)

    parts = []
    if modifiers & _MOD_MASK_CONTROL:
        parts.append("Ctrl")
    if modifiers & _MOD_MASK_SHIFT:
        parts.append("Shift")
    if modifiers & _MOD_MASK_ALT:
        parts.append("Alt")
    if modifiers & _MOD_MASK_SUPER:
        parts.append("Super")

    display_key = _DISPLAY_NAMES.get(key_name)
    if display_key is None:
        display_key = key_name.upper() if len(key_name) == 1 and key_name.isalpha() else key_name

    parts.append(display_key)
    return "+".join(parts)


# ── Internal helpers ───────────────────────────────────────────────────────

def _rebuild_tables():
    """Populate the three lookup tables from the current _bindings dict."""
    for action, key_string in _bindings.items():
        modifiers, key_name = _parse_key_string(key_string)

        if modifiers == 0:
            # Simple key — add to both string and integer lookups.
            _keyname_to_action[key_name] = action
            keyval = _resolve_keyval(key_name)
            if keyval is not None:
                _keyval_to_action[keyval] = action
        else:
            # Composite key — only the integer path checks modifiers.
            # When a modifier (e.g. Shift) is already tracked in the mask,
            # IBus reports the base keysym (lowercase for letters).
            ibus_key_name = key_name.lower() if len(key_name) == 1 and key_name.isalpha() else key_name
            keyval = _resolve_keyval(ibus_key_name)
            if keyval is not None:
                _composite_bindings.append((keyval, modifiers, action))


def _parse_key_string(key_string):
    """Parse GTK-accelerator-notation into (modifier_mask, key_name).

    Examples::

        "Escape"                  →  (0, "Escape")
        "<Control><Shift>T"       →  (CONTROL|SHIFT, "t")
        "<Control><Alt>BackSpace" →  (CONTROL|ALT, "BackSpace")

    Returns:
        Tuple of ``(modifier_mask: int, key_name: str)``.
    """
    modifier_mask = 0
    rest = key_string

    while rest.startswith("<"):
        closing = rest.find(">")
        if closing == -1:
            break
        mod_name = rest[1:closing]
        mask = _VALID_MODIFIERS.get(mod_name)
        if mask is not None:
            modifier_mask |= mask
        rest = rest[closing + 1:]

    return modifier_mask, rest


def _resolve_keyval(key_name):
    """Resolve *key_name* to its X11 keysym integer.

    Checks the hardcoded ``_KEYVALS`` dict first, then falls back to
    ``ord()`` for single printable ASCII characters.
    """
    if key_name in _KEYVALS:
        return _KEYVALS[key_name]
    if len(key_name) == 1 and key_name.isascii() and key_name.isprintable():
        return ord(key_name)
    return None


def _extract_modifiers(state):
    """Extract only the modifier bits we track from an IBus state bitmask.

    Masks out irrelevant high bits such as ``RELEASE_MASK`` (1 << 30).
    """
    relevant = (
        _MOD_MASK_CONTROL | _MOD_MASK_SHIFT |
        _MOD_MASK_ALT | _MOD_MASK_SUPER
    )
    return state & relevant


# Auto-load default bindings so the module works out of the box without an
# explicit load_bindings() call.  User code can override at any time.
load_bindings(get_default_bindings())
