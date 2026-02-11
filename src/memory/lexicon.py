from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any


@dataclass(frozen=True, slots=True)
class CompressionLexiconEntry:
    lexicon_id: str
    token: str
    original_pattern: str
    reverse_rule: str
    tier: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "lexicon_id": self.lexicon_id,
            "token": self.token,
            "original_pattern": self.original_pattern,
            "reverse_rule": self.reverse_rule,
            "tier": self.tier,
            "created_at": self.created_at,
        }


class CompressionLexicon:
    def __init__(self, version: str = "0.1.0", entries: list[CompressionLexiconEntry] | None = None) -> None:
        self.version = version
        self._entries: list[CompressionLexiconEntry] = list(entries or self.default_entries())

    @staticmethod
    def default_entries() -> list[CompressionLexiconEntry]:
        now = datetime.now(UTC).isoformat()
        return [
            CompressionLexiconEntry(
                lexicon_id="lex-001",
                token="[rc_ok]",
                original_pattern="root cause hypothesis accepted",
                reverse_rule="token-replace",
                tier="semantic",
                created_at=now,
            ),
            CompressionLexiconEntry(
                lexicon_id="lex-002",
                token="[blk_evt]",
                original_pattern="missing evidence trace.captured",
                reverse_rule="token-replace",
                tier="semantic",
                created_at=now,
            ),
            CompressionLexiconEntry(
                lexicon_id="lex-003",
                token="[wf_run]",
                original_pattern="workflow run",
                reverse_rule="token-replace",
                tier="summary",
                created_at=now,
            ),
        ]

    def entries(self) -> list[CompressionLexiconEntry]:
        return list(self._entries)

    def encode_line(self, text: str) -> str:
        output = text
        for entry in self._entries:
            output = output.replace(entry.original_pattern, entry.token)
        return output

    def decode_line(self, text: str) -> str:
        output = text
        for entry in self._entries:
            output = output.replace(entry.token, entry.original_pattern)
        return output

    def bundle(self) -> dict[str, Any]:
        return {
            "lexicon_version": self.version,
            "entries": [entry.to_dict() for entry in self._entries],
        }
