from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class MemoryStoreError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    memory_id: str
    run_id: str
    memory_tier: str
    content: str
    evidence_refs: tuple[str, ...]
    created_at: str
    promoted_from: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "run_id": self.run_id,
            "memory_tier": self.memory_tier,
            "content": self.content,
            "evidence_refs": list(self.evidence_refs),
            "created_at": self.created_at,
            "promoted_from": self.promoted_from,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MemoryRecord":
        return cls(
            memory_id=str(payload["memory_id"]),
            run_id=str(payload["run_id"]),
            memory_tier=str(payload["memory_tier"]),
            content=str(payload["content"]),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
            created_at=str(payload["created_at"]),
            promoted_from=str(payload.get("promoted_from", "")),
        )


class MemoryStore:
    TIERS = ("raw", "working", "candidate", "long")

    def __init__(self, run_root: Path, run_id: str) -> None:
        self.run_root = run_root
        self.run_id = run_id
        self._run_dir = self.run_root / self.run_id
        self._memory_dir = self._run_dir / "memory"
        self._index_dir = self._run_dir / "index"
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._index_dir.mkdir(parents=True, exist_ok=True)
        for tier in self.TIERS:
            (self._memory_dir / tier).mkdir(parents=True, exist_ok=True)

    def _tier_path(self, tier: str) -> Path:
        if tier not in self.TIERS:
            raise MemoryStoreError(f"unknown memory tier: {tier}")
        return self._memory_dir / tier

    def _record_path(self, tier: str, memory_id: str) -> Path:
        return self._tier_path(tier) / f"{memory_id}.json"

    def create_record(
        self,
        memory_tier: str,
        content: str,
        evidence_refs: list[str] | tuple[str, ...],
        promoted_from: str = "",
        memory_id: str = "",
    ) -> MemoryRecord:
        resolved_memory_id = memory_id or f"mem-{memory_tier}-{uuid4().hex[:12]}"
        record = MemoryRecord(
            memory_id=resolved_memory_id,
            run_id=self.run_id,
            memory_tier=memory_tier,
            content=content,
            evidence_refs=tuple(evidence_refs),
            created_at=datetime.now(UTC).isoformat(),
            promoted_from=promoted_from,
        )
        output = self._record_path(memory_tier, resolved_memory_id)
        output.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def get_record(self, memory_id: str) -> MemoryRecord:
        for tier in self.TIERS:
            path = self._record_path(tier, memory_id)
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                return MemoryRecord.from_dict(payload)
        raise MemoryStoreError(f"memory record not found: {memory_id}")

    def list_records(self, memory_tier: str = "") -> list[MemoryRecord]:
        tiers = (memory_tier,) if memory_tier else self.TIERS
        records: list[MemoryRecord] = []
        for tier in tiers:
            tier_path = self._tier_path(tier)
            for file in sorted(tier_path.glob("*.json")):
                payload = json.loads(file.read_text(encoding="utf-8"))
                records.append(MemoryRecord.from_dict(payload))
        return records

    def promote_candidate_to_long(self, candidate_memory_id: str) -> MemoryRecord:
        candidate = self.get_record(candidate_memory_id)
        if candidate.memory_tier != "candidate":
            raise MemoryStoreError("only candidate memory can be promoted")
        long_record = self.create_record(
            memory_tier="long",
            content=candidate.content,
            evidence_refs=list(candidate.evidence_refs),
            promoted_from=candidate.memory_id,
        )
        self._append_long_memory_link(candidate.memory_id, long_record.memory_id)
        return long_record

    def _append_long_memory_link(self, candidate_id: str, long_id: str) -> Path:
        path = self._index_dir / "long-memory-links.json"
        payload: list[dict[str, str]] = []
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
        payload.append(
            {
                "run_id": self.run_id,
                "candidate_memory_id": candidate_id,
                "long_memory_id": long_id,
                "linked_at": datetime.now(UTC).isoformat(),
            }
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def append_promotion_decision(self, decision: dict[str, Any]) -> Path:
        path = self._index_dir / "memory-promotion-decisions.jsonl"
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(decision, ensure_ascii=False))
            file.write("\n")
        return path
