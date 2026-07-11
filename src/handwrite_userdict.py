"""
User dictionary for ibus-handwrite-chinese.

Per-user character learning via local SQLite database.
Learns characters the user selects and boosts them in future recognition.
"""

import math
import os
import sqlite3
import sys
import threading

# ---------------------------------------------------------------------------
# Default boost_strength — overridden by config when loaded from engine
# ---------------------------------------------------------------------------
_DEFAULT_BOOST_STRENGTH = 1.5
_DEFAULT_MAX_ENTRIES = 10000


def _default_db_path() -> str:
    """Return the default SQLite database path under XDG_DATA_HOME."""
    xdg_data = os.environ.get("XDG_DATA_HOME", "")
    if not xdg_data:
        xdg_data = os.path.expanduser("~/.local/share")
    directory = os.path.join(xdg_data, "ibus-handwrite-chinese")
    os.makedirs(directory, exist_ok=True)
    return os.path.join(directory, "user-dict.sqlite")


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character TEXT NOT NULL UNIQUE,
    count INTEGER DEFAULT 1,
    last_used TEXT DEFAULT (datetime('now')),
    created TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_user_dict_char ON user_dictionary(character);
"""

_PRAGMA_WAL = 'PRAGMA journal_mode=WAL;'
_PRAGMA_BUSY = 'PRAGMA busy_timeout=5000;'


class UserDict:
    """Per-user character learning database.

    Learns characters the user selects and applies a confidence boost
    to promote frequently-used characters in recognition results.
    """

    def __init__(self, db_path: str | None = None):
        """Open (or create) the user dictionary database.

        Args:
            db_path: SQLite database path. ``:memory:`` for testing.
                     ``None`` (default) resolves to ``~/.local/share/ibus-handwrite-chinese/user-dict.sqlite``.
        """
        self._db_path = db_path if db_path is not None else _default_db_path()
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._boost_strength = _DEFAULT_BOOST_STRENGTH
        self._max_entries = _DEFAULT_MAX_ENTRIES
        self._enabled = True
        self._open()

    # -- public helpers -----------------------------------------------------

    def configure(self, *, enabled: bool | None = None,
                  boost_strength: float | None = None,
                  max_entries: int | None = None) -> None:
        """Apply runtime configuration.  Thread-safe."""
        if enabled is not None:
            self._enabled = enabled
        if boost_strength is not None:
            self._boost_strength = boost_strength
        if max_entries is not None:
            self._max_entries = max_entries

    @property
    def enabled(self) -> bool:
        return self._enabled

    # -- public API ---------------------------------------------------------

    def learn(self, char: str) -> None:
        """Record that the user selected *char*.

        INSERTs if new, otherwise increments the count and updates
        last_used.  This is a no-op when the dict is disabled.
        """
        if not self._enabled or not char or self._conn is None:
            return
        try:
            with self._lock:
                self._conn.execute(
                    """INSERT INTO user_dictionary (character, count, last_used)
                       VALUES (?, 1, datetime('now'))
                       ON CONFLICT(character) DO UPDATE SET
                           count = count + 1,
                           last_used = datetime('now')""",
                    (char,),
                )
                self._conn.commit()
                # Prune oldest entries if over limit
                if self._max_entries > 0:
                    self._conn.execute(
                        """DELETE FROM user_dictionary WHERE id NOT IN (
                               SELECT id FROM user_dictionary
                               ORDER BY count DESC, last_used DESC
                               LIMIT ?
                           )""",
                        (self._max_entries,),
                    )
                    self._conn.commit()
        except sqlite3.Error as exc:
            self._log_error(f"learn({char!r}) failed: {exc}")

    def boost(self, candidates: list) -> list:
        """Reorder *candidates* to promote user-learned characters.

        Accepts either ``list[str]`` (plain character strings) or
        ``list[tuple[str, float]]`` (character + PP-OCR confidence score).
        Returns the same format as the input.

        The boost factor is ``min(1 + 0.05 * log(count), boost_strength)``
        applied multiplicatively to the candidate confidence score before
        re-sorting.
        """
        if not candidates or not self._enabled or self._conn is None:
            return candidates

        # Detect format
        first = candidates[0]
        tuple_mode = not isinstance(first, str)

        # Build a lookup of count per known character
        counts: dict[str, int] = {}
        try:
            with self._lock:
                cursor = self._conn.execute(
                    "SELECT character, count FROM user_dictionary "
                    "WHERE character IN ({})".format(
                        ",".join("?" for _ in candidates)
                    ),
                    [c[0] if tuple_mode else c for c in candidates],
                )
                for row in cursor:
                    counts[row[0]] = row[1]
        except sqlite3.Error as exc:
            self._log_error(f"boost() query failed: {exc}")
            return candidates

        if not counts:
            return candidates

        strength = self._boost_strength

        # Build (char, boosted_score, original_score_or_none) entries
        entries: list[tuple[str, float, float | None]] = []
        for item in candidates:
            if tuple_mode:
                char, score = item
            else:
                char = item
                score = 1.0
            cnt = counts.get(char, 0)
            factor = min(1.0 + 0.05 * math.log1p(cnt), strength)
            entries.append((char, score * factor, score))

        # Sort by boosted score descending
        entries.sort(key=lambda x: x[1], reverse=True)

        if tuple_mode:
            return [(c, orig) for c, _, orig in entries]
        else:
            return [c for c, _, _ in entries]

    def get_stats(self) -> dict:
        """Return summary statistics about the user dictionary."""
        if self._conn is None:
            return {"total": 0, "top": []}
        try:
            with self._lock:
                total = self._conn.execute(
                    "SELECT COUNT(*) FROM user_dictionary"
                ).fetchone()[0]
                top = self._conn.execute(
                    "SELECT character, count FROM user_dictionary "
                    "ORDER BY count DESC, last_used DESC LIMIT 10"
                ).fetchall()
            return {"total": total, "top": [(r[0], r[1]) for r in top]}
        except sqlite3.Error as exc:
            self._log_error(f"get_stats() failed: {exc}")
            return {"total": 0, "top": []}

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    # -- internal -----------------------------------------------------------

    def _open(self) -> None:
        """Open the SQLite connection and create schema if needed."""
        is_memory = self._db_path == ':memory:'
        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            if not is_memory:
                self._conn.executescript(_PRAGMA_WAL + _PRAGMA_BUSY)
            self._conn.executescript(_SCHEMA_SQL)
        except sqlite3.Error as exc:
            self._log_error(f"failed to open user dictionary at {self._db_path}: {exc}")
            self._conn = None

    @staticmethod
    def _log_error(msg: str) -> None:
        print(f"  [userdict] Error: {msg}", file=sys.stderr)
